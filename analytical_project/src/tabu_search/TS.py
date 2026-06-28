from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Set, Tuple

from src.ScheduleContext import ScheduleContext, Discipline, Group
from src.models import Schedule, Vec


# ============================================================
# СЕССИИ, КОТОРЫЕ НУЖНО РАССТАВИТЬ
# ============================================================

@dataclass(frozen=True)
class SessionSpec:
    """Одна пара (лекция/семинар/лаба), которую TS должен куда-то поставить."""
    discipline_id: int
    kind: str  # "course" | "seminar" | "lab" — пока используется только для документации


def expand_discipline_to_sessions(discipline: Discipline, pair_length_hours: float = 2.0) -> List[SessionSpec]:
    """
    Переводит часы дисциплины в список пар.
    """
    def n_pairs(hours: float) -> int:
        return int(round(hours / pair_length_hours)) if hours else 0

    sessions: List[SessionSpec] = []
    sessions += [SessionSpec(discipline.id, "course")] * n_pairs(discipline.course_hours)
    sessions += [SessionSpec(discipline.id, "seminar")] * n_pairs(discipline.seminar_hours)
    sessions += [SessionSpec(discipline.id, "lab")] * n_pairs(discipline.lab_hours)
    return sessions


# ============================================================
# ОБЯЗАТЕЛЬНЫЕ ОГРАНИЧЕНИЯ (hard)
# ============================================================

def hard_unique_slot(schedule: List[Vec]) -> int:
    """Группа не может быть в двух местах одновременно: (weekday, timeslot) не повторяется."""
    seen: Set[Tuple[int, int]] = set()
    violations = 0
    for v in schedule:
        key = (v.weekday_id, v.timeslot_id)
        if key in seen:
            violations += 1
        seen.add(key)
    return violations


def hard_professor_qualified(schedule: List[Vec], context: ScheduleContext) -> int:
    """Преподаватель должен быть привязан к дисциплине через professor_discipline."""
    violations = 0
    for v in schedule:
        if v.professor_id not in context.get_discipline_professors(v.discipline_id):
            violations += 1
    return violations


def hard_room_capacity(schedule: List[Vec], context: ScheduleContext, group: Group) -> int:
    """Аудитория должна вмещать группу."""
    violations = 0
    for v in schedule:
        if context.get_audience(v.audience_id).seats < group.students_count:
            violations += 1
    return violations


def hard_room_type(schedule: List[Vec], context: ScheduleContext) -> int:
    """Аудитория должна поддерживать хотя бы один из optimal_room_type дисциплины."""
    violations = 0
    for v in schedule:
        disc = context.get_discipline(v.discipline_id)
        if not disc.optimal_room_types:
            continue
        audience_types = context.audience_roomtypes.get(v.audience_id, set())
        if not (audience_types & disc.optimal_room_types):
            violations += 1
    return violations


def hard_daily_limit(schedule: List[Vec], context: ScheduleContext) -> int:
    """Не больше MAX_PAIRS_PER_DAY пар в один день."""
    limit = context.config.MAX_PAIRS_PER_DAY
    if limit <= 0:
        return 0
    per_day: Dict[int, int] = defaultdict(int)
    for v in schedule:
        per_day[v.weekday_id] += 1
    return sum(max(0, count - limit) for count in per_day.values())


# ============================================================
# ЖЕЛАТЕЛЬНЫЕ ОГРАНИЧЕНИЯ (soft, 3 шт.)
# ============================================================

def soft_day_compactness(schedule: List[Vec]) -> float:
    by_day: Dict[int, List[int]] = defaultdict(list)
    for v in schedule:
        by_day[v.weekday_id].append(v.timeslot_id)
    gaps = 0
    for slots in by_day.values():
        unique = sorted(set(slots))          # было: slots = sorted(slots) — без set()
        if len(unique) >= 2:                 # было: if len(slots) >= 2
            span = unique[-1] - unique[0] + 1
            gaps += span - len(unique)       # было: span - len(slots)
    return float(gaps)


def soft_room_fit(schedule: List[Vec], context: ScheduleContext, group: Group) -> float:
    """Штраф за лишние места в аудитории (не загонять группу в актовый зал)."""
    if not schedule:
        return 0.0
    waste = sum(max(0, context.get_audience(v.audience_id).seats - group.students_count) for v in schedule)
    return waste / len(schedule)


def soft_week_balance(schedule: List[Vec], context: ScheduleContext) -> float:
    """Штраф за неравномерную нагрузку по дням недели (дисперсия пар/день)."""
    weekday_count = context.config.WEEKDAY_COUNT or 1
    per_day: Dict[int, int] = defaultdict(int)
    for v in schedule:
        per_day[v.weekday_id] += 1
    counts = [per_day.get(d, 0) for d in range(weekday_count)]
    mean = sum(counts) / len(counts)
    return sum((c - mean) ** 2 for c in counts) / len(counts)


W_COMPACT = 1.0
W_ROOMFIT = 0.5
W_BALANCE = 1.0


def evaluate(schedule: List[Vec], context: ScheduleContext, group: Group) -> Tuple[int, float]:
    """
    Лексикографическая оценка: (кол-во hard-нарушений, взвешенная сумма soft-штрафов).
    Сравнение тюплов в Python даёт нужный приоритет автоматически:
    любое решение с меньшим числом hard-нарушений строго лучше,
    soft сравнивается только при равенстве hard.
    """
    hard = (
        hard_unique_slot(schedule)
        + hard_professor_qualified(schedule, context)
        + hard_room_capacity(schedule, context, group)
        + hard_room_type(schedule, context)
        + hard_daily_limit(schedule, context)
    )
    soft = (
        W_COMPACT * soft_day_compactness(schedule)
        + W_ROOMFIT * soft_room_fit(schedule, context, group)
        + W_BALANCE * soft_week_balance(schedule, context)
    )
    return hard, soft


# ============================================================
# ХОДЫ И ОКРЕСТНОСТЬ
# ============================================================

@dataclass(frozen=True)
class Move:
    kind: str  # "reslot" | "reaudience" | "reprofessor" | "swap_slots"
    index: int
    index2: Optional[int] = None
    new_weekday: Optional[int] = None
    new_timeslot: Optional[int] = None
    new_audience: Optional[int] = None
    new_professor: Optional[int] = None


def generate_candidate_moves(
    schedule: Schedule, context: ScheduleContext, rng: random.Random, sample_size: int
) -> List[Move]:
    moves: List[Move] = []
    n = len(schedule)
    weekday_count = context.config.WEEKDAY_COUNT
    pairs_per_day = context.config.MAX_PAIRS_PER_DAY

    for _ in range(sample_size):
        i = rng.randrange(n)
        v = schedule[i]
        kind = rng.choice(["reslot", "reaudience", "reprofessor", "swap_slots"])

        if kind == "reslot":
            moves.append(Move("reslot", i,
                               new_weekday=rng.randrange(weekday_count),
                               new_timeslot=rng.randrange(pairs_per_day)))

        elif kind == "reaudience":
            disc = context.get_discipline(v.discipline_id)
            candidates: Set[int] = set()
            for rt in disc.optimal_room_types:
                candidates |= context.roomtype_audiences.get(rt, set())
            candidates = (candidates or set(context.audience_by_id.keys())) - {v.audience_id}
            if candidates:
                moves.append(Move("reaudience", i, new_audience=rng.choice(list(candidates))))

        elif kind == "reprofessor":
            candidates = context.get_discipline_professors(v.discipline_id) - {v.professor_id}
            if candidates:
                moves.append(Move("reprofessor", i, new_professor=rng.choice(list(candidates))))

        else:  # swap_slots
            j = rng.randrange(n)
            if j != i:
                moves.append(Move("swap_slots", i, index2=j))

    return moves


def apply_move(schedule: Schedule, move: Move) -> Tuple[Schedule, List[Tuple]]:
    """Возвращает (новый Schedule, список атрибутов для табу-листа)."""
    new_schedule = schedule.copy()

    if move.kind == "reslot":
        v = new_schedule[move.index]
        tabu_attrs = [(v.discipline_id, "slot", (v.weekday_id, v.timeslot_id))]
        new_schedule.replace(move.index, Vec(v.discipline_id, move.new_weekday, move.new_timeslot,
                                              v.audience_id, v.professor_id))

    elif move.kind == "reaudience":
        v = new_schedule[move.index]
        tabu_attrs = [(v.discipline_id, "audience", v.audience_id)]
        new_schedule.replace(move.index, Vec(v.discipline_id, v.weekday_id, v.timeslot_id,
                                              move.new_audience, v.professor_id))

    elif move.kind == "reprofessor":
        v = new_schedule[move.index]
        tabu_attrs = [(v.discipline_id, "professor", v.professor_id)]
        new_schedule.replace(move.index, Vec(v.discipline_id, v.weekday_id, v.timeslot_id,
                                              v.audience_id, move.new_professor))

    else:  # swap_slots
        vi, vj = new_schedule[move.index], new_schedule[move.index2]
        tabu_attrs = [
            (vi.discipline_id, "slot", (vi.weekday_id, vi.timeslot_id)),
            (vj.discipline_id, "slot", (vj.weekday_id, vj.timeslot_id)),
        ]
        new_schedule.replace(move.index, Vec(vi.discipline_id, vj.weekday_id, vj.timeslot_id,
                                              vi.audience_id, vi.professor_id))
        new_schedule.replace(move.index2, Vec(vj.discipline_id, vi.weekday_id, vi.timeslot_id,
                                               vj.audience_id, vj.professor_id))

    return new_schedule, tabu_attrs


def build_initial_schedule(
    sessions: List[SessionSpec], context: ScheduleContext, group: Group, rng: random.Random
) -> Schedule:
    schedule = Schedule(max_pairs=len(sessions))

    all_slots = [(w, t) for w in range(context.config.WEEKDAY_COUNT) for t in range(context.config.MAX_PAIRS_PER_DAY)]
    rng.shuffle(all_slots)

    for i, session in enumerate(sessions):
        weekday_id, timeslot_id = all_slots[i % len(all_slots)]

        professors = list(context.get_discipline_professors(session.discipline_id))
        if not professors:
            raise ValueError(
                f"У дисциплины {session.discipline_id} нет ни одного преподавателя в "
                f"professor_discipline — TS не сможет построить допустимое расписание."
            )
        professor_id = rng.choice(professors)

        disc = context.get_discipline(session.discipline_id)
        candidate_audiences: Set[int] = set()
        for rt in disc.optimal_room_types:
            candidate_audiences |= context.roomtype_audiences.get(rt, set())
        if not candidate_audiences:
            candidate_audiences = set(context.audience_by_id.keys())
        audience_id = rng.choice(list(candidate_audiences))

        schedule.add(Vec(session.discipline_id, weekday_id, timeslot_id, audience_id, professor_id))

    return schedule


# ============================================================
# ОСНОВНОЙ ЦИКЛ TABU SEARCH
# ============================================================

@dataclass
class TabuSearchResult:
    best_schedule: Schedule
    best_objective: Tuple[int, float]
    history: List[Tuple[int, float]]
    iterations_run: int

    def to_algorithm_run_record(self, parameters: dict, execution_time_ms: int) -> dict:
        hard, soft = self.best_objective
        return {
            "algorithm_name": "TABU_SEARCH",
            "parameters": parameters,
            "execution_time_ms": execution_time_ms,
            "fitness_score": soft if hard == 0 else None,
            "extra_metrics": {
                "hard_violations": hard,
                "soft_penalty": soft,
                "iterations": self.iterations_run,
            },
        }


def tabu_search(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    group: Group,
    max_iterations: int = 500,
    neighborhood_size: int = 25,
    tabu_tenure: int = 20,
    stagnation_limit: int = 100,
    seed: Optional[int] = None,
) -> TabuSearchResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError(
            "ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0) — "
            "проверь .env, иначе сетке расписания негде существовать."
        )

    rng = random.Random(seed)

    current = build_initial_schedule(sessions, context, group, rng)
    current_obj = evaluate(list(current), context, group)

    best = current.copy()
    best_obj = current_obj

    tabu_list: Deque[Tuple] = deque(maxlen=tabu_tenure)
    history = [current_obj]
    stagnant_for = 0
    iteration = -1

    for iteration in range(max_iterations):
        candidates = generate_candidate_moves(current, context, rng, neighborhood_size)
        if not candidates:
            continue

        best_move_schedule = None
        best_move_obj = None
        best_move_tabu_attrs = None

        for move in candidates:
            cand_schedule, tabu_attrs = apply_move(current, move)
            cand_obj = evaluate(list(cand_schedule), context, group)

            is_tabu = any(attr in tabu_list for attr in tabu_attrs)
            aspiration = cand_obj < best_obj  # критерий устремления: бьём личный рекорд — разрешаем даже табу-ход

            if is_tabu and not aspiration:
                continue

            if best_move_obj is None or cand_obj < best_move_obj:
                best_move_schedule, best_move_obj, best_move_tabu_attrs = cand_schedule, cand_obj, tabu_attrs

        if best_move_schedule is None:
            # вся окрестность под табу — диверсификация случайным ходом
            move = rng.choice(candidates)
            best_move_schedule, best_move_tabu_attrs = apply_move(current, move)
            best_move_obj = evaluate(list(best_move_schedule), context, group)

        current, current_obj = best_move_schedule, best_move_obj
        tabu_list.extend(best_move_tabu_attrs)
        history.append(current_obj)

        if current_obj < best_obj:
            best, best_obj = current.copy(), current_obj
            stagnant_for = 0
        else:
            stagnant_for += 1

        if best_obj[0] == 0 and stagnant_for >= stagnation_limit:
            break

    return TabuSearchResult(best, best_obj, history, iteration + 1)