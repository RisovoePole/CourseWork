from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ortools.sat.python import cp_model

from src.ScheduleContext import ScheduleContext, Group
from src.models import Schedule, Vec
from src.tabu_search.TS import SessionSpec, evaluate  # только постановка задачи и сверка, не алгоритм


# ============================================================
# КАНДИДАТЫ (для ограничения доменов, не для штрафов)
# ============================================================

@dataclass(frozen=True)
class SessionCandidates:
    audiences: List[int]   # уже пересечены по типу И вмещают группу
    professors: List[int]


def build_session_candidates(
    sessions: List[SessionSpec], context: ScheduleContext, group: Group
) -> List[SessionCandidates]:
    result = []
    for session in sessions:
        disc = context.get_discipline(session.discipline_id)

        professors = sorted(context.get_discipline_professors(session.discipline_id))
        if not professors:
            raise ValueError(f"У дисциплины {session.discipline_id} нет преподавателей в professor_discipline.")

        type_ok = set()
        for rt in disc.optimal_room_types:
            type_ok |= context.roomtype_audiences.get(rt, set())
        if not type_ok:
            type_ok = set(context.audience_by_id.keys())

        audiences = sorted(a for a in type_ok if context.get_audience(a).seats >= group.students_count)
        if not audiences:
            raise ValueError(
                f"Для дисциплины {session.discipline_id} нет аудитории, подходящей по типу "
                f"и вмещающей группу ({group.students_count} студентов) — модель будет INFEASIBLE."
            )

        result.append(SessionCandidates(audiences=audiences, professors=professors))
    return result


# ============================================================
# МОДЕЛЬ
# ============================================================

@dataclass
class CPSATVars:
    weekday: cp_model.IntVar
    timeslot: cp_model.IntVar
    slot_id: cp_model.IntVar
    audience_idx: cp_model.IntVar   # локальный индекс в SessionCandidates.audiences
    professor_idx: cp_model.IntVar  # локальный индекс в SessionCandidates.professors
    seats: cp_model.IntVar


W_COMPACT = 1
W_ROOMFIT = 1
W_BALANCE = 1


def build_model(
    sessions: List[SessionSpec], context: ScheduleContext, group: Group, candidates: List[SessionCandidates]
) -> Tuple[cp_model.CpModel, List[CPSATVars]]:
    model = cp_model.CpModel()
    weekday_count = context.config.WEEKDAY_COUNT
    pairs_per_day = context.config.MAX_PAIRS_PER_DAY
    n = len(sessions)

    session_vars: List[CPSATVars] = []
    for i, cand in enumerate(candidates):
        weekday = model.new_int_var(0, weekday_count - 1, f"weekday_{i}")
        timeslot = model.new_int_var(0, pairs_per_day - 1, f"timeslot_{i}")

        # H1: уникальность слота (заодно неявно даёт H5, см. выше)
        slot_id = model.new_int_var(0, weekday_count * pairs_per_day - 1, f"slot_{i}")
        model.add(slot_id == weekday * pairs_per_day + timeslot)

        # H2 (преподаватель) и H3+H4 (аудитория: тип+вместимость) — индекс в УЖЕ отфильтрованный
        # список кандидатов; недопустимое значение здесь просто не существует в домене
        professor_idx = model.new_int_var(0, len(cand.professors) - 1, f"professor_idx_{i}")
        audience_idx = model.new_int_var(0, len(cand.audiences) - 1, f"audience_idx_{i}")

        seats = model.new_int_var(0, max(a.seats for a in context.audiences), f"seats_{i}")
        model.add_element(audience_idx, [context.get_audience(a).seats for a in cand.audiences], seats)

        session_vars.append(CPSATVars(weekday, timeslot, slot_id, audience_idx, professor_idx, seats))

    model.add_all_different([v.slot_id for v in session_vars])

    # ---- день -> булевы индикаторы (нужны и для явного H5, и для soft-критериев) ----
    day_bool = [[model.new_bool_var(f"day_{i}_{d}") for d in range(weekday_count)] for i in range(n)]
    for i, v in enumerate(session_vars):
        for d in range(weekday_count):
            model.add(v.weekday == d).only_enforce_if(day_bool[i][d])
            model.add(v.weekday != d).only_enforce_if(~day_bool[i][d])
            # exactly-one по d получается автоматически из этой двусторонней связки — отдельный
            # add_exactly_one не нужен

    day_count = []
    gap_terms = []
    for d in range(weekday_count):
        count_d = model.new_int_var(0, n, f"count_{d}")
        model.add(count_d == sum(day_bool[i][d] for i in range(n)))
        day_count.append(count_d)

        model.add(count_d <= pairs_per_day)  # H5 явно — избыточно после H1, но дёшево и наглядно

        used_d = model.new_bool_var(f"used_{d}")
        model.add(count_d >= 1).only_enforce_if(used_d)
        model.add(count_d == 0).only_enforce_if(~used_d)

        min_slot_d = model.new_int_var(0, pairs_per_day - 1, f"min_slot_{d}")
        max_slot_d = model.new_int_var(0, pairs_per_day - 1, f"max_slot_{d}")
        for i, v in enumerate(session_vars):
            model.add(v.timeslot >= min_slot_d).only_enforce_if(day_bool[i][d])
            model.add(v.timeslot <= max_slot_d).only_enforce_if(day_bool[i][d])

        gap_d = model.new_int_var(0, pairs_per_day, f"gap_{d}")
        model.add(gap_d == max_slot_d - min_slot_d + 1 - count_d).only_enforce_if(used_d)
        model.add(gap_d == 0).only_enforce_if(~used_d)  # пустой день — гарантированно без "окон"
        gap_terms.append(gap_d)

    # ---- soft: компактность по дню + room-fit + равномерность по неделе (range, не дисперсия) ----
    max_count = model.new_int_var(0, n, "max_day_count")
    min_count = model.new_int_var(0, n, "min_day_count")
    model.add_max_equality(max_count, day_count)
    model.add_min_equality(min_count, day_count)

    room_fit_total = sum(v.seats for v in session_vars) - group.students_count * n

    model.minimize(
        W_COMPACT * sum(gap_terms)
        + W_ROOMFIT * room_fit_total
        + W_BALANCE * (max_count - min_count)
    )

    return model, session_vars


# ============================================================
# РЕЗУЛЬТАТ И ЗАПУСК
# ============================================================

@dataclass
class CPSATResult:
    best_schedule: Optional[Schedule]
    best_objective: Optional[Tuple[int, float]]
    status_name: str
    wall_time_s: float

    def to_algorithm_run_record(self, parameters: dict, execution_time_ms: int) -> dict:
        hard, soft = self.best_objective if self.best_objective else (None, None)
        return {
            "algorithm_name": "CP_SAT",
            "parameters": parameters,
            "execution_time_ms": execution_time_ms,
            "fitness_score": soft,
            "extra_metrics": {
                "hard_violations": hard,
                "status": self.status_name,
                "wall_time_s": self.wall_time_s,
            },
        }


def solve_with_cp_sat(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    group: Group,
    max_time_in_seconds: float = 30.0,
    seed: Optional[int] = None,
) -> CPSATResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError("ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0).")

    candidates = build_session_candidates(sessions, context, group)
    model, session_vars = build_model(sessions, context, group, candidates)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time_in_seconds
    if seed is not None:
        solver.parameters.random_seed = seed
    # многопоточность по умолчанию использует все доступные ядра — если хочешь ограничить,
    # проверь точное имя параметра в установленной у тебя версии (звался по-разному в разных релизах)

    status = solver.solve(model)
    status_name = solver.status_name(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return CPSATResult(None, None, status_name, solver.wall_time)

    vecs = [
        Vec(
            session.discipline_id,
            solver.value(v.weekday),
            solver.value(v.timeslot),
            cand.audiences[solver.value(v.audience_idx)],
            cand.professors[solver.value(v.professor_idx)],
        )
        for session, v, cand in zip(sessions, session_vars, candidates)
    ]

    hard, soft = evaluate(vecs, context, group)  # должно дать hard == 0 — это не эвристика

    schedule = best_schedule = Schedule(max_pairs=len(sessions))
    for v in vecs:
        schedule.add(v)

    return CPSATResult(schedule, (hard, soft), status_name, solver.wall_time)