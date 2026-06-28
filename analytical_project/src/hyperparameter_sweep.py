"""
hyperparameter_sweep.py

Отвечает на вопрос "а вы проверяли другие настройки алгоритмов?" — реальными
цифрами, не текстом-обещанием. Перебирает 2-3 ключевых гиперпараметра на
КАЖДЫЙ алгоритм по отдельности, на фиксированном датасете (по умолчанию
medium — он достаточно велик, чтобы различия между настройками были видны,
и достаточно мал, чтобы перебор не занял часы).

Какие именно гиперпараметры выбраны и почему — см. SWEEP_GRID ниже; это
ровно те параметры, которые в *_notes.md были отмечены как "что крутить".

Запуск: python -m src.hyperparameter_sweep
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from itertools import product
from typing import Any, Dict, List, Sequence

from src.algorithm_comparison import (
    RunResult, _run_ts, _run_ga, _run_sa, _run_cp_sat,
    export_runs_csv, group_by_algorithm_and_dataset,
)
from src.synthetic_data import DATASET_PRESETS, make_synthetic_context
from src.tabu_search.TS import expand_discipline_to_sessions

logger = logging.getLogger("schedulegen.sweep")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


# ============================================================
# СЕТКА ПАРАМЕТРОВ
#
# По каждому алгоритму перебираются ровно те 2 параметра, которые в
# соответствующем *_notes.md помечены как главные "что крутить":
#   TS — neighborhood_size (размер батча кандидатов) x tabu_tenure (память)
#   GA — population_size x gene_mut_indpb (грубость мутации)
#   SA — initial_temperature x cooling_rate (темп охлаждения)
#   CP-SAT — здесь нет "качественных" гиперпараметров в том же смысле
#            (домены жёстко заданы постановкой задачи), поэтому
#            перебирается единственный содержательный параметр — бюджет
#            времени, чтобы показать, насколько быстро CP-SAT сходится
#            к оптимуму на medium (см. вывод по разделу II.4 — там это
#            было заявлено текстом, здесь подтверждается цифрами).
# ============================================================

SWEEP_GRID: Dict[str, Dict[str, Sequence[Any]]] = {
    "TS": {"neighborhood_size": [10, 25, 50], "tabu_tenure": [10, 20, 40]},
    "GA": {"population_size": [50, 100, 200], "gene_mut_indpb": [0.05, 0.1, 0.2]},
    "SA": {"initial_temperature": [10, 50, 200], "cooling_rate": [0.99, 0.995, 0.999]},
    "CP-SAT": {"max_time_in_seconds": [1, 5, 15]},
}

SEEDS_PER_CONFIG = 5  # меньше, чем в основном сравнении (10) - сеток много, бюджет времени общий


@dataclass
class SweepRunResult(RunResult):
    config_label: str = ""  # человекочитаемая подпись конкретной комбинации параметров


def _label(params: Dict[str, Any]) -> str:
    return ", ".join(f"{k}={v}" for k, v in params.items())


def run_sweep_for_algorithm(
    algorithm: str,
    sessions,
    context,
    group,
    dataset_name: str,
    seeds: Sequence[int] = range(1, SEEDS_PER_CONFIG + 1),
) -> List[SweepRunResult]:
    grid = SWEEP_GRID[algorithm]
    param_names = list(grid.keys())
    combinations = list(product(*grid.values()))

    runner = {"TS": _run_ts, "GA": _run_ga, "SA": _run_sa, "CP-SAT": _run_cp_sat}[algorithm]

    results: List[SweepRunResult] = []
    logger.info("=== %s: %d комбинаций параметров x %d seed(ов) ===", algorithm, len(combinations), len(seeds))

    for combo in combinations:
        params = dict(zip(param_names, combo))
        label = _label(params)

        for seed in seeds:
            run = runner(sessions, dataset_name, context, group, seed, **params)
            results.append(SweepRunResult(**vars(run), config_label=label))
            logger.info("%s [%s] seed=%-3s hard=%s soft=%s time=%.1fms",
                        algorithm, label, seed, run.hard, run.soft, run.wall_time_ms)

    return results


def run_full_sweep(dataset_name: str = "medium") -> Dict[str, List[SweepRunResult]]:
    spec = next(s for s in DATASET_PRESETS if s.name == dataset_name)
    context = make_synthetic_context(seed=0, **spec.make_kwargs)
    group = context.groups[0]
    sessions = [s for d in context.disciplines for s in expand_discipline_to_sessions(d)]

    all_results: Dict[str, List[SweepRunResult]] = {}
    for algorithm in SWEEP_GRID:
        all_results[algorithm] = run_sweep_for_algorithm(algorithm, sessions, context, group, dataset_name)

    return all_results


def print_sweep_summary(results: Dict[str, List[SweepRunResult]]) -> None:
    """Группирует по (algorithm, config_label) - то же самое, для чего служит
    group_by_algorithm_and_dataset в основном сравнении, только группа теперь
    не по dataset, а по конкретной комбинации параметров."""
    import statistics

    print(f"{'algorithm':<8} {'config':<40} {'runs':>4} {'success%':>9} {'soft_mean':>10} {'time_ms':>10}")
    print("-" * 85)

    for algorithm, runs in results.items():
        by_config: Dict[str, List[SweepRunResult]] = {}
        for r in runs:
            by_config.setdefault(r.config_label, []).append(r)

        for label, group_runs in by_config.items():
            feasible = [r.soft for r in group_runs if r.feasible]
            success = len(feasible) / len(group_runs) * 100
            soft_mean = statistics.mean(feasible) if feasible else float("nan")
            time_mean = statistics.mean(r.wall_time_ms for r in group_runs)
            print(f"{algorithm:<8} {label:<40} {len(group_runs):>4} {success:>8.1f}% "
                  f"{soft_mean:>10.3f} {time_mean:>10.1f}")
        print()


if __name__ == "__main__":
    results = run_full_sweep("medium")
    print_sweep_summary(results)

    flat = {f"{algo}": runs for algo, runs in results.items()}
    export_runs_csv(flat, "results/hyperparameter_sweep.csv")