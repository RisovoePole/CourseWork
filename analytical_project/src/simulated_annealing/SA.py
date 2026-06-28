from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.ScheduleContext import ScheduleContext, Group
from src.models import Schedule, Vec
from src.tabu_search.TS import SessionSpec, evaluate  # только постановка задачи, не алгоритм


# ============================================================
# НАЧАЛЬНОЕ РЕШЕНИЕ
# ============================================================

def build_initial_schedule(sessions: List[SessionSpec], context: ScheduleContext, rng: random.Random) -> Schedule:
    schedule = Schedule(max_pairs=len(sessions))

    all_slots = [(w, t) for w in range(context.config.WEEKDAY_COUNT) for t in range(context.config.MAX_PAIRS_PER_DAY)]
    rng.shuffle(all_slots)

    for i, session in enumerate(sessions):
        weekday_id, timeslot_id = all_slots[i % len(all_slots)]

        professors = list(context.get_discipline_professors(session.discipline_id))
        if not professors:
            raise ValueError(f"У дисциплины {session.discipline_id} нет преподавателей в professor_discipline.")
        professor_id = rng.choice(professors)

        disc = context.get_discipline(session.discipline_id)
        audiences = set()
        for rt in disc.optimal_room_types:
            audiences |= context.roomtype_audiences.get(rt, set())
        if not audiences:
            audiences = set(context.audience_by_id.keys())
        audience_id = rng.choice(list(audiences))

        schedule.add(Vec(session.discipline_id, weekday_id, timeslot_id, audience_id, professor_id))

    return schedule


# ============================================================
# ВОЗМУЩЕНИЯ (своя реализация, не из TS)
# ============================================================

@dataclass(frozen=True)
class Perturbation:
    kind: str  # "reslot" | "reaudience" | "reprofessor" | "swap_slots"
    index: int
    index2: Optional[int] = None
    weekday_id: Optional[int] = None
    timeslot_id: Optional[int] = None
    audience_id: Optional[int] = None
    professor_id: Optional[int] = None


def random_perturbation(schedule: Schedule, context: ScheduleContext, rng: random.Random) -> Optional[Perturbation]:
    """Ровно ОДИН случайный сосед — без выборки и сравнения нескольких кандидатов."""
    n = len(schedule)
    i = rng.randrange(n)
    v = schedule[i]
    kind = rng.choice(["reslot", "reaudience", "reprofessor", "swap_slots"])

    if kind == "reslot":
        return Perturbation("reslot", i,
                             weekday_id=rng.randrange(context.config.WEEKDAY_COUNT),
                             timeslot_id=rng.randrange(context.config.MAX_PAIRS_PER_DAY))

    if kind == "reaudience":
        disc = context.get_discipline(v.discipline_id)
        candidates = set()
        for rt in disc.optimal_room_types:
            candidates |= context.roomtype_audiences.get(rt, set())
        candidates = (candidates or set(context.audience_by_id.keys())) - {v.audience_id}
        return Perturbation("reaudience", i, audience_id=rng.choice(list(candidates))) if candidates else None

    if kind == "reprofessor":
        candidates = context.get_discipline_professors(v.discipline_id) - {v.professor_id}
        return Perturbation("reprofessor", i, professor_id=rng.choice(list(candidates))) if candidates else None

    j = rng.randrange(n)  # swap_slots
    return Perturbation("swap_slots", i, index2=j) if j != i else None


def apply_perturbation(schedule: Schedule, p: Perturbation) -> Tuple[Vec, ...]:
    """Меняет schedule на месте, возвращает старые Vec — нужно для откатa, если ход отклонят."""
    if p.kind == "reslot":
        v = schedule[p.index]
        schedule.replace(p.index, Vec(v.discipline_id, p.weekday_id, p.timeslot_id, v.audience_id, v.professor_id))
        return (v,)

    if p.kind == "reaudience":
        v = schedule[p.index]
        schedule.replace(p.index, Vec(v.discipline_id, v.weekday_id, v.timeslot_id, p.audience_id, v.professor_id))
        return (v,)

    if p.kind == "reprofessor":
        v = schedule[p.index]
        schedule.replace(p.index, Vec(v.discipline_id, v.weekday_id, v.timeslot_id, v.audience_id, p.professor_id))
        return (v,)

    vi, vj = schedule[p.index], schedule[p.index2]  # swap_slots
    schedule.replace(p.index, Vec(vi.discipline_id, vj.weekday_id, vj.timeslot_id, vi.audience_id, vi.professor_id))
    schedule.replace(p.index2, Vec(vj.discipline_id, vi.weekday_id, vi.timeslot_id, vj.audience_id, vj.professor_id))
    return (vi, vj)


def revert_perturbation(schedule: Schedule, p: Perturbation, old_values: Tuple[Vec, ...]) -> None:
    schedule.replace(p.index, old_values[0])
    if p.kind == "swap_slots":
        schedule.replace(p.index2, old_values[1])


# ============================================================
# ОСНОВНОЙ ЦИКЛ
# ============================================================

HARD_PENALTY_WEIGHT = 1_000.0


def _energy(objective: Tuple[int, float]) -> float:
    """Скаляр для формулы Метрополиса — ей нужно вещественное Δ, а не лексикографический тюпл."""
    hard, soft = objective
    return hard * HARD_PENALTY_WEIGHT + soft


@dataclass
class SAResult:
    best_schedule: Schedule
    best_objective: Tuple[int, float]
    history: List[Tuple[int, float]]
    iterations_run: int
    final_temperature: float

    def to_algorithm_run_record(self, parameters: dict, execution_time_ms: int) -> dict:
        hard, soft = self.best_objective
        return {
            "algorithm_name": "SIMULATED_ANNEALING",
            "parameters": parameters,
            "execution_time_ms": execution_time_ms,
            "fitness_score": soft if hard == 0 else None,
            "extra_metrics": {
                "hard_violations": hard,
                "soft_penalty": soft,
                "iterations": self.iterations_run,
                "final_temperature": self.final_temperature,
            },
        }


def simulated_annealing(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    group: Group,
    initial_temperature: float = 50.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 1e-3,
    max_iterations: int = 20_000,
    seed: Optional[int] = None,
) -> SAResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError("ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0).")

    rng = random.Random(seed)

    current = build_initial_schedule(sessions, context, rng)
    current_obj = evaluate(list(current), context, group)

    best = current.copy()
    best_obj = current_obj

    temperature = initial_temperature
    history = [current_obj]
    iteration = -1

    for iteration in range(max_iterations):
        if temperature < min_temperature:
            break

        perturbation = random_perturbation(current, context, rng)
        if perturbation is None:
            continue

        old_values = apply_perturbation(current, perturbation)
        candidate_obj = evaluate(list(current), context, group)

        delta = _energy(candidate_obj) - _energy(current_obj)

        if delta <= 0 or rng.random() < math.exp(-delta / temperature):
            current_obj = candidate_obj  # принят — оставляем изменения как есть
        else:
            revert_perturbation(current, perturbation, old_values)  # отклонён — откатываем

        history.append(current_obj)

        # для "лучшего из найденных" сравниваем точным лексикографическим тюплом,
        # а не скаляром — здесь не нужна вероятностная формула, можно точнее
        if current_obj < best_obj:
            best, best_obj = current.copy(), current_obj

        temperature *= cooling_rate

    return SAResult(best, best_obj, history, iteration + 1, temperature)