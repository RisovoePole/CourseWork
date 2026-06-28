from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

from deap import algorithms, base, creator, tools

from src.ScheduleContext import ScheduleContext, Group
from src.models import Schedule, Vec
from src.tabu_search.TS import SessionSpec, evaluate  # переиспользуем те же hard/soft из TS


# ============================================================
# ПРЕДСТАВЛЕНИЕ ОСОБИ
# ============================================================

class Gene(NamedTuple):
    weekday_id: int
    timeslot_id: int
    audience_id: int
    professor_id: int


def random_gene(session: SessionSpec, context: ScheduleContext) -> Gene:
    weekday_id = random.randrange(context.config.WEEKDAY_COUNT)
    timeslot_id = random.randrange(context.config.MAX_PAIRS_PER_DAY)

    professors = list(context.get_discipline_professors(session.discipline_id))
    if not professors:
        raise ValueError(
            f"У дисциплины {session.discipline_id} нет преподавателей в professor_discipline."
        )
    professor_id = random.choice(professors)

    disc = context.get_discipline(session.discipline_id)
    candidates = set()
    for rt in disc.optimal_room_types:
        candidates |= context.roomtype_audiences.get(rt, set())
    if not candidates:
        candidates = set(context.audience_by_id.keys())
    audience_id = random.choice(list(candidates))

    return Gene(weekday_id, timeslot_id, audience_id, professor_id)


def individual_to_vecs(individual: List[Gene], sessions: List[SessionSpec]) -> List[Vec]:
    return [
        Vec(session.discipline_id, gene.weekday_id, gene.timeslot_id, gene.audience_id, gene.professor_id)
        for session, gene in zip(sessions, individual)
    ]


# ============================================================
# FITNESS (скаляризация лексикографики hard/soft)
# ============================================================

HARD_PENALTY_WEIGHT = 1_000.0  # должен быть заведомо больше любого реалистичного soft-штрафа


def fitness(individual: List[Gene], sessions: List[SessionSpec], context: ScheduleContext, group: Group) -> Tuple[float]:
    vecs = individual_to_vecs(individual, sessions)
    hard, soft = evaluate(vecs, context, group)
    return (hard * HARD_PENALTY_WEIGHT + soft,)


# ============================================================
# ОПЕРАТОРЫ
# ============================================================

def mutate_individual(individual, sessions: List[SessionSpec], context: ScheduleContext, indpb: float = 0.1):
    """Каждый ген с вероятностью indpb перегенерируется целиком (как 'reslot+reaudience+reprofessor' сразу)."""
    for i, session in enumerate(sessions):
        if random.random() < indpb:
            individual[i] = random_gene(session, context)
    return (individual,)


def random_individual(sessions: List[SessionSpec], context: ScheduleContext):
    return creator.Individual(random_gene(s, context) for s in sessions)


# ============================================================
# РЕЗУЛЬТАТ
# ============================================================

@dataclass
class GAResult:
    best_schedule: Schedule
    best_objective: Tuple[int, float]
    logbook: "tools.Logbook"

    def to_algorithm_run_record(self, parameters: dict, execution_time_ms: int) -> dict:
        hard, soft = self.best_objective
        return {
            "algorithm_name": "GENETIC_ALGORITHM",
            "parameters": parameters,
            "execution_time_ms": execution_time_ms,
            "fitness_score": soft if hard == 0 else None,
            "extra_metrics": {
                "hard_violations": hard,
                "soft_penalty": soft,
                "generations": len(self.logbook),
            },
        }


# ============================================================
# ОСНОВНОЙ ЗАПУСК
# ============================================================

def genetic_algorithm(
    sessions: List[SessionSpec],
    context: ScheduleContext,
    group: Group,
    population_size: int = 100,
    generations: int = 200,
    cx_prob: float = 0.6,
    mut_prob: float = 0.3,
    gene_mut_indpb: float = 0.1,
    seed: Optional[int] = None,
) -> GAResult:
    if context.config.WEEKDAY_COUNT <= 0 or context.config.MAX_PAIRS_PER_DAY <= 0:
        raise ValueError(
            "ALGORITHM_WEEKDAY_COUNT / ALGORITHM_MAX_PAIRS_PER_DAY не заданы (0) — проверь .env."
        )

    random.seed(seed)

    # creator.create() падает предупреждением при повторном вызове в том же процессе
    # (например, если запускаешь genetic_algorithm() несколько раз в бенчмарк-цикле) —
    # поэтому регистрируем типы один раз.
    if not hasattr(creator, "FitnessMin"):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("individual", random_individual, sessions=sessions, context=context)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", fitness, sessions=sessions, context=context, group=group)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutate_individual, sessions=sessions, context=context, indpb=gene_mut_indpb)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=population_size)
    hof = tools.HallOfFame(1)

    stats = tools.Statistics(lambda ind: ind.fitness.values[0])
    stats.register("min", min)
    stats.register("avg", lambda vals: sum(vals) / len(vals))

    _, logbook = algorithms.eaSimple(
        population, toolbox,
        cxpb=cx_prob, mutpb=mut_prob, ngen=generations,
        stats=stats, halloffame=hof, verbose=False,
    )

    best_individual = hof[0]
    best_vecs = individual_to_vecs(best_individual, sessions)
    best_hard, best_soft = evaluate(best_vecs, context, group)

    best_schedule = best_schedule = Schedule(max_pairs=len(sessions))
    for v in best_vecs:
        best_schedule.add(v)

    return GAResult(best_schedule, (best_hard, best_soft), logbook)