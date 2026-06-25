from src.bruteforce import enumerate_schedules_backtracking, enumerate_schedules_parallel, schedules_count_for_size, total_vectors_count
from src.config import ALGORITHM_MAX_PAIRS_PER_DAY, ALGORITHM_RUN_MAX_PAIRS, ALGORITHM_DISCIPLINE_COUNT
from src.rules import (
    ConstraintEngine,
    MaxPairsPerDayRule,
    NoAudienceTimeConflictRule,
    NoDisciplineTimeConflictRule,
    NoDuplicateVectorRule,
)
from src.timer import timer


def _build_engine() -> ConstraintEngine:
    return ConstraintEngine([
        NoDuplicateVectorRule(),
        NoAudienceTimeConflictRule(),
        NoDisciplineTimeConflictRule(),
        MaxPairsPerDayRule(max_pairs_per_day=ALGORITHM_MAX_PAIRS_PER_DAY),
    ])


@timer
def run_backtracking() -> tuple[int, int]:
    engine = _build_engine()
    result_count = sum(
        1
        for _ in enumerate_schedules_backtracking(
            max_pairs=ALGORITHM_RUN_MAX_PAIRS,
            exact_size=True,
            engine=engine,
            materialize=False,
        )
    )
    return result_count, engine.calls


@timer
def run_parallel() -> tuple[int, int]:
    engine = _build_engine()
    _, result_count, calls = enumerate_schedules_parallel(
        max_pairs=ALGORITHM_RUN_MAX_PAIRS,
        exact_size=True,
        engine=engine,
        materialize=False,
    )
    return result_count, calls

def compare_three_runs() -> None:
    backtracking_count, backtracking_calls = run_backtracking()
    parallel_count, parallel_calls = run_parallel()

    print(
        f"Размер пространства одной пары (|V|): {total_vectors_count()}\n"
        f"Сколько расписаний ровно из k пар существует: C(|V|, k): {schedules_count_for_size(ALGORITHM_DISCIPLINE_COUNT)}" 
    )

    print(
        f"k={ALGORITHM_RUN_MAX_PAIRS} | "
        f"backtracking: {backtracking_count} results, {backtracking_calls} checks | "
        f"parallel: {parallel_count} results, {parallel_calls} checks"
    )



def main() -> None:
    compare_three_runs()


if __name__ == "__main__":
    main()
