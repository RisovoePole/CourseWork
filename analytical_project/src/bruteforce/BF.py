"""
scheduling_bruteforce.py

Полный перебор для ТОЙ ЖЕ постановки задачи, что у TS/GA/SA/CP-SAT: дан
фиксированный список `sessions`, нужно подобрать каждой (weekday, timeslot,
audience, professor) так, чтобы выполнялись H1-H5, и среди всех допустимых
найти минимальный по soft. В отличие от старого bruteforceCore.py, здесь
перебираются не произвольные векторы из всего пространства, а позиции под
уже известные обязательные сессии.

Что изменилось относительно rules.py:
  - NoDuplicateVectorRule / NoAudienceTimeConflictRule / NoDisciplineTimeConflictRule
    избыточны: раз на сессию ровно одна позиция, всё это сводится к одному
    H1 (hard_unique_slot) на уровне расписания.
  - MaxPairsPerDisciplineRule избыточен: количество сессий на дисциплину
    больше не решается перебором — sessions строится один раз заранее
    (expand_discipline_to_sessions), это вход, а не часть поиска.
  - MaxPairsPerDayRule остаётся (это H5), но смотрит context.config.MAX_PAIRS_PER_DAY.
  - ДОБАВЛЕНЫ H2 (преподаватель квалифицирован) и H3+H4 (аудитория подходит
    по вместимости и типу) — в исходном rules.py их не было вообще. Как и
    в CP-SAT, это не runtime-проверка, а фильтр кандидатов заранее
    (build_session_candidates) — поэтому во время самого перебора
    проверяются только H1 и H5, остальное физически не нарушаемо.
"""

from __future__ import annotations

import os
import concurrent.futures as cf
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from src.ScheduleContext import ScheduleContext, Group
from src.models import Schedule, Vec
from src.tabu_search.TS import SessionSpec, evaluate
from src.constraint_programming.CP_SAT import SessionCandidates, build_session_candidates


# ============================================================
# РАЗМЕР ПРОСТРАНСТВА (та же роль, что total_schedules_count() в старом модуле)
# ============================================================

def per_session_choice_counts(
    context: ScheduleContext, candidates: List[SessionCandidates]
) -> List[int]:
    """Сколько вариантов (weekday, timeslot, audience, professor) у каждой
    сессии ДО отсечения по H1/H5."""
    w, p = context.config.WEEKDAY_COUNT, context.config.MAX_PAIRS_PER_DAY
    return [w * p * len(c.audiences) * len(c.professors) for c in candidates]


def total_assignment_space_size(context: ScheduleContext, candidates: List[SessionCandidates]) -> int:
    """
    Произведение вариантов по сессиям — НЕ C(|V|, k), как в старом модуле:
    там k пар выбирались из общего неразличимого пула, здесь сессии
    различимы и у каждой свой список кандидатов.
    """
    total = 1
    for count in per_session_choice_counts(context, candidates):
        total *= count
    return total


# ============================================================
# ИНКРЕМЕНТАЛЬНАЯ ПРОВЕРКА (H1 + H5 — единственное, что ещё нужно проверять)
# ============================================================

def _can_place(schedule: Schedule, weekday_id: int, timeslot_id: int, pairs_per_day: int) -> bool:
    """H2-H4 уже невозможно нарушить — кандидаты отфильтрованы заранее."""
    day_count = 0
    for v in schedule:
        if v.weekday_id == weekday_id:
            day_count += 1
            if v.timeslot_id == timeslot_id:
                return False  # H1
    return day_count < pairs_per_day  # H5


# ============================================================
# ОБЩЕЕ ЯДРО ПЕРЕБОРА (используется и последовательной, и параллельной версией)
# ============================================================

def _level_choices(context: ScheduleContext, cand: SessionCandidates):
    for weekday_id in range(context.config.WEEKDAY_COUNT):
        for timeslot_id in range(context.config.MAX_PAIRS_PER_DAY):
            for audience_id in cand.audiences:
                for professor_id in cand.professors:
                    yield weekday_id, timeslot_id, audience_id, professor_id


def _enumerate_from(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    candidates: List[SessionCandidates],
    schedule: Schedule,
    start_index: int,
    calls_counter: List[int],
) -> Iterator[Schedule]:
    """Достраивает schedule начиная с sessions[start_index]. Отдаёт КАЖДОЕ
    полное допустимое назначение (сам объект schedule, без копии — копировать
    на месте использования, если нужно сохранить за пределами итерации)."""
    pairs_per_day = context.config.MAX_PAIRS_PER_DAY
    n = len(sessions)

    stack: List[Iterator] = [_level_choices(context, candidates[start_index])]

    while stack:
        level = len(schedule)
        choice = next(stack[-1], None)

        if choice is None:
            stack.pop()
            if len(schedule) > start_index:
                schedule.pop()
            continue

        weekday_id, timeslot_id, audience_id, professor_id = choice
        calls_counter[0] += 1

        if not _can_place(schedule, weekday_id, timeslot_id, pairs_per_day):
            continue

        schedule.add(Vec(sessions[level].discipline_id, weekday_id, timeslot_id, audience_id, professor_id))

        if len(schedule) == n:
            yield schedule
            schedule.pop()
            continue

        stack.append(_level_choices(context, candidates[len(schedule)]))


# ============================================================
# ПОСЛЕДОВАТЕЛЬНАЯ ВЕРСИЯ
# ============================================================

def enumerate_assignments(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    group: Group,
    candidates: List[SessionCandidates],
    limit: Optional[int] = None,
    materialize: bool = True,
    calls_counter: Optional[List[int]] = None,
) -> Iterator[Tuple[Optional[Schedule], Tuple[int, float]]]:
    schedule = Schedule(max_pairs=len(sessions))
    calls_counter = calls_counter if calls_counter is not None else [0]
    yielded = 0

    for found in _enumerate_from(sessions, context, candidates, schedule, 0, calls_counter):
        hard, soft = evaluate(list(found), context, group)  # hard всегда 0 — H2-H4 не нарушаемы
        yield (found.copy() if materialize else None), (hard, soft)
        yielded += 1
        if limit is not None and yielded >= limit:
            return


@dataclass
class BruteForceResult:
    best_schedule: Optional[Schedule]
    best_objective: Optional[Tuple[int, float]]
    feasible_count: int
    explored_calls: int  # аналог engine.calls в старом модуле

    def to_algorithm_run_record(self, parameters: dict, execution_time_ms: int) -> dict:
        hard, soft = self.best_objective if self.best_objective else (None, None)
        return {
            "algorithm_name": "BRUTE_FORCE",
            "parameters": parameters,
            "execution_time_ms": execution_time_ms,
            "fitness_score": soft,
            "extra_metrics": {
                "hard_violations": hard,
                "feasible_count": self.feasible_count,
                "explored_calls": self.explored_calls,
            },
        }


def solve_with_bruteforce(
    sessions: List[SessionSpec], context: ScheduleContext, group: Group, limit: Optional[int] = None
) -> BruteForceResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError("ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0).")

    candidates = build_session_candidates(sessions, context, group)

    best_schedule, best_obj = None, None
    feasible_count = 0
    calls = [0]

    for schedule, obj in enumerate_assignments(
        sessions, context, group, candidates, limit=limit, calls_counter=calls
    ):
        feasible_count += 1
        if best_obj is None or obj < best_obj:
            best_schedule, best_obj = schedule, obj

    return BruteForceResult(best_schedule, best_obj, feasible_count, calls[0])


# ============================================================
# ПАРАЛЛЕЛЬНАЯ ВЕРСИЯ (разбивка по выбору ПЕРВОЙ сессии — та же идея, что в старом модуле)
# ============================================================

_worker_state: dict = {}


def _init_worker(sessions, context, group, candidates) -> None:
    """Тяжёлые объекты передаются один раз на старт процесса."""
    _worker_state["sessions"] = sessions
    _worker_state["context"] = context
    _worker_state["group"] = group
    _worker_state["candidates"] = candidates


def _explore_branch(first_choice: Tuple[int, int, int, int]):
    """calls создаётся ЗДЕСЬ, внутри вызова задачи, а не в _init_worker и
    не на уровне модуля — это ровно то, что чинит баг с накоплением calls
    между задачами одного переиспользуемого процесса-воркера (тот самый,
    который ты уже находил в старом bruteforceCore)."""
    sessions = _worker_state["sessions"]
    context = _worker_state["context"]
    group = _worker_state["group"]
    candidates = _worker_state["candidates"]
    pairs_per_day = context.config.MAX_PAIRS_PER_DAY

    calls = [1]
    weekday_id, timeslot_id, audience_id, professor_id = first_choice
    schedule = Schedule(max_pairs=len(sessions))

    if not _can_place(schedule, weekday_id, timeslot_id, pairs_per_day):
        return None, None, 0, calls[0]

    schedule.add(Vec(sessions[0].discipline_id, weekday_id, timeslot_id, audience_id, professor_id))

    best_vecs, best_obj, feasible_count = None, None, 0

    if len(sessions) == 1:
        hard, soft = evaluate(list(schedule), context, group)
        feasible_count, best_vecs, best_obj = 1, schedule.to_list(), (hard, soft)
    else:
        for found in _enumerate_from(sessions, context, candidates, schedule, 1, calls):
            obj = evaluate(list(found), context, group)
            feasible_count += 1
            if best_obj is None or obj < best_obj:
                best_vecs, best_obj = found.to_list(), obj

    return best_vecs, best_obj, feasible_count, calls[0]


def solve_with_bruteforce_parallel(
    sessions: List[SessionSpec], context: ScheduleContext, group: Group, workers: Optional[int] = None
) -> BruteForceResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError("ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0).")

    candidates = build_session_candidates(sessions, context, group)
    first_choices = list(_level_choices(context, candidates[0]))
    workers = workers or os.cpu_count() or 1

    best_schedule, best_obj = None, None
    feasible_count, total_calls = 0, 0

    with cf.ProcessPoolExecutor(
        max_workers=workers, initializer=_init_worker, initargs=(sessions, context, group, candidates)
    ) as pool:
        for best_vecs, obj, count, calls in pool.map(_explore_branch, first_choices):
            feasible_count += count
            total_calls += calls
            if obj is not None and (best_obj is None or obj < best_obj):
                best_obj = obj
                best_schedule = Schedule(max_pairs=len(sessions))
                for row in best_vecs:
                    best_schedule.add(Vec(*row))

    return BruteForceResult(best_schedule, best_obj, feasible_count, total_calls)