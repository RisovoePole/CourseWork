"""
algorithm_comparison.py

Сравнение TS / GA / SA / CP-SAT / bruteforce на наборе датасетов
(sessions, context, group) — материал для раздела с результатами в курсовой.

Почему не просто пять вызовов в блокноте:
  - TS/GA/SA стохастические — один прогон ничего не доказывает, нужно
    несколько seed'ов + агрегаты (среднее/std/доля успешных hard==0).
  - bruteforce и CP-SAT(status=OPTIMAL) дают опорную точку: реальный
    оптимум, относительно которого считается gap у эвристик.
  - Метрики должны лежать в одном формате (RunResult), иначе сравнение
    в отчёте — это пять разных таблиц, которые не свести вместе.
  - Один датасет показывает только "насколько стабилен результат при
    разной случайности" (ось seed). Чтобы делать выводы вида "TS лучше
    GA на туго ограниченных данных" — нужна ВТОРАЯ ось: разные датасеты
    разного размера/трудности (DATASET_PRESETS из synthetic_data.py).
    Поэтому gap_to_best считается ОТДЕЛЬНО на каждый датасет — иначе
    soft=12 на крошечной задаче и soft=340 на стресс-тесте окажутся на
    одной шкале, что бессмысленно.

Что собирается на каждый прогон:
  - hard, soft — общая шкала evaluate() из TS-модуля для ВСЕХ пятерых,
    это и делает сравнение честным.
  - wall_time_ms.
  - trace сходимости, где он осмысленен:
      TS/SA      — (итерация, hard, soft) на каждом шаге (есть history).
      GA         — (поколение, fitness) — DEAP логирует только
                   скаляризованный fitness по поколениям, разложения на
                   hard/soft по шагам нет.
      bruteforce — (порядковый номер улучшения, hard, soft) — точки, где
                   найденное решение стало лучше предыдущего лучшего.
      CP-SAT     — trace ПУСТ: solver не отдаёт промежуточные решения без
                   отдельного solution callback, здесь он не настроен (это
                   честно, не подмена нулями).
"""

from __future__ import annotations

import csv
import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.ScheduleContext import ScheduleContext, Group
from src.tabu_search.TS import SessionSpec, tabu_search, expand_discipline_to_sessions
from src.genetic_algorithm.GA import genetic_algorithm
from src.simulated_annealing.SA import simulated_annealing
from src.constraint_programming.CP_SAT import solve_with_cp_sat, build_session_candidates
from src.bruteforce.BF import solve_with_bruteforce, solve_with_bruteforce_parallel, enumerate_assignments
from src.synthetic_data import DatasetSpec, make_synthetic_context


logger = logging.getLogger("schedulegen.comparison")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


# ============================================================
# ЕДИНЫЙ ФОРМАТ РЕЗУЛЬТАТА ОДНОГО ПРОГОНА
# ============================================================

@dataclass
class TracePoint:
    step: int
    hard: Optional[int] = None
    soft: Optional[float] = None
    fitness: Optional[float] = None  # заполняется только там, где hard/soft по шагам недоступны (GA)


@dataclass
class RunResult:
    algorithm: str
    dataset: str
    seed: Optional[int]
    hard: Optional[int]
    soft: Optional[float]
    wall_time_ms: float
    status: str = "OK"  # для CP-SAT: OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN
    extra: Dict[str, Any] = field(default_factory=dict)
    trace: List[TracePoint] = field(default_factory=list)

    @property
    def feasible(self) -> bool:
        return self.hard == 0


# ============================================================
# ОБЁРТКИ НАД КАЖДЫМ АЛГОРИТМОМ — единая точка замера времени + лога
#
# У всех пяти одна и та же сигнатура (sessions, dataset, context, group, ...) —
# это специально, чтобы run_comparison() ниже могла звать их одинаково в цикле,
# без отдельной ветки на каждый алгоритм.
# ============================================================

def _run_ts(sessions, dataset, context, group, seed: int, **kwargs) -> RunResult:
    t0 = time.perf_counter()
    result = tabu_search(sessions, context, group, seed=seed, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    hard, soft = result.best_objective
    if soft < 0:
        # soft - сумма неотрицательных штрафов по построению (gap/room_fit/balance >= 0),
        # отрицательное значение означает, что evaluate() считался на испорченном
        # расписании - сигнал смотреть декодирование результата, не статистическую случайность
        logger.error("TS      dataset=%-12s seed=%-3s вернул soft=%.3f < 0 — баг декодирования, не результат",
                      dataset, seed, soft)
    trace = [TracePoint(step=i, hard=h, soft=s) for i, (h, s) in enumerate(result.history)]

    logger.info("TS      dataset=%-12s seed=%-3s hard=%d soft=%9.3f time=%8.1fms iters=%d",
                dataset, seed, hard, soft, elapsed_ms, result.iterations_run)
    return RunResult("TS", dataset, seed, hard, soft, elapsed_ms,
                      extra={"iterations": result.iterations_run}, trace=trace)


def _run_ga(sessions, dataset, context, group, seed: int, **kwargs) -> RunResult:
    t0 = time.perf_counter()
    result = genetic_algorithm(sessions, context, group, seed=seed, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    hard, soft = result.best_objective
    if soft < 0:
        logger.error("GA      dataset=%-12s seed=%-3s вернул soft=%.3f < 0 — баг декодирования, не результат",
                      dataset, seed, soft)
    # logbook хранит скаляризованный fitness (hard*1000+soft) по поколениям,
    # а не отдельно hard/soft — раскладка на компоненты по шагам в GA не велась
    trace = [
        TracePoint(step=gen, fitness=fit)
        for gen, fit in zip(result.logbook.select("gen"), result.logbook.select("min"))
    ]

    logger.info("GA      dataset=%-12s seed=%-3s hard=%d soft=%9.3f time=%8.1fms gens=%d",
                dataset, seed, hard, soft, elapsed_ms, len(result.logbook))
    return RunResult("GA", dataset, seed, hard, soft, elapsed_ms,
                      extra={"generations": len(result.logbook)}, trace=trace)


def _run_sa(sessions, dataset, context, group, seed: int, **kwargs) -> RunResult:
    t0 = time.perf_counter()
    result = simulated_annealing(sessions, context, group, seed=seed, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    hard, soft = result.best_objective
    if soft < 0:
        logger.error("SA      dataset=%-12s seed=%-3s вернул soft=%.3f < 0 — баг декодирования, не результат",
                      dataset, seed, soft)
    trace = [TracePoint(step=i, hard=h, soft=s) for i, (h, s) in enumerate(result.history)]

    logger.info("SA      dataset=%-12s seed=%-3s hard=%d soft=%9.3f time=%8.1fms iters=%d T_final=%.5f",
                dataset, seed, hard, soft, elapsed_ms, result.iterations_run, result.final_temperature)
    return RunResult("SA", dataset, seed, hard, soft, elapsed_ms,
                      extra={"iterations": result.iterations_run, "final_temperature": result.final_temperature},
                      trace=trace)


def _run_cp_sat(sessions, dataset, context, group, seed: int, **kwargs) -> RunResult:
    t0 = time.perf_counter()
    result = solve_with_cp_sat(sessions, context, group, seed=seed, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if result.best_objective is None:
        logger.warning("CP-SAT  dataset=%-12s seed=%-3s status=%s — решение не найдено за бюджет времени",
                        dataset, seed, result.status_name)
        return RunResult("CP-SAT", dataset, seed, None, None, elapsed_ms, status=result.status_name)

    hard, soft = result.best_objective
    if hard != 0:
        # не должно произойти НИКОГДА — H2-H4 у CP-SAT это домен, а не штраф
        logger.error("CP-SAT  dataset=%-12s seed=%-3s вернул hard=%d != 0 — баг модели, не данных",
                      dataset, seed, hard)

    logger.info("CP-SAT  dataset=%-12s seed=%-3s status=%-8s hard=%d soft=%9.3f time=%8.1fms",
                dataset, seed, result.status_name, hard, soft, elapsed_ms)
    return RunResult("CP-SAT", dataset, seed, hard, soft, elapsed_ms, status=result.status_name,
                      extra={"solver_wall_time_s": result.wall_time_s})


def _run_bruteforce(sessions, dataset, context, group, **kwargs) -> RunResult:
    """Без seed — полный перебор детерминирован. trace — момент каждого
    улучшения лучшего найденного, не каждый исследованный вариант (иначе
    на разумном instance это были бы десятки тысяч точек)."""
    t0 = time.perf_counter()
    candidates = build_session_candidates(sessions, context, group)

    best_hard, best_soft = None, None
    feasible_count = 0
    trace: List[TracePoint] = []

    for _, (hard, soft) in enumerate_assignments(sessions, context, group, candidates, materialize=False, **kwargs):
        feasible_count += 1
        if best_soft is None or (hard, soft) < (best_hard, best_soft):
            best_hard, best_soft = hard, soft
            trace.append(TracePoint(step=feasible_count, hard=hard, soft=soft))

    elapsed_ms = (time.perf_counter() - t0) * 1000
    if best_hard is not None and best_hard != 0:
        logger.error("Bruteforce dataset=%-12s вернул hard=%d != 0 — баг, H2-H4 не должны пропускать такое",
                      dataset, best_hard)

    logger.info("Bruteforce dataset=%-12s hard=%s soft=%s time=%8.1fms feasible_total=%d",
                dataset, best_hard, best_soft, elapsed_ms, feasible_count)
    return RunResult("Bruteforce", dataset, None, best_hard, best_soft, elapsed_ms,
                      extra={"feasible_count": feasible_count}, trace=trace)


# ============================================================
# ОРКЕСТРАЦИЯ: запуск всех алгоритмов на N seed'ах, ОДИН датасет
# ============================================================

@dataclass
class ComparisonConfig:
    sessions: List[SessionSpec]
    dataset: str  # имя датасета — раньше этого поля не было, и dataset нигде не выставлялся
    context: ScheduleContext
    group: Group
    seeds: Sequence[int] = (1, 2, 3, 4, 5)
    ts_kwargs: Dict[str, Any] = field(default_factory=dict)
    ga_kwargs: Dict[str, Any] = field(default_factory=dict)
    sa_kwargs: Dict[str, Any] = field(default_factory=dict)
    cp_sat_kwargs: Dict[str, Any] = field(default_factory=dict)
    run_bruteforce: bool = False  # см. предупреждение в логе при включении
    bruteforce_kwargs: Dict[str, Any] = field(default_factory=dict)


def run_comparison(config: ComparisonConfig) -> Dict[str, List[RunResult]]:
    """Гонит все 4 стохастических алгоритма на ВСЕХ seeds для ОДНОГО датасета.
    Bruteforce — отдельно, без seed (он детерминирован), только если включён явно."""
    sessions, context, group = config.sessions, config.context, config.group
    dataset = config.dataset
    results: Dict[str, List[RunResult]] = {"TS": [], "GA": [], "SA": [], "CP-SAT": []}

    logger.info("=== dataset=%s: %d сессий, %d seed(ов) ===", dataset, len(sessions), len(config.seeds))

    for seed in config.seeds:
        results["TS"].append(_run_ts(sessions, dataset, context, group, seed, **config.ts_kwargs))
        results["GA"].append(_run_ga(sessions, dataset, context, group, seed, **config.ga_kwargs))
        results["SA"].append(_run_sa(sessions, dataset, context, group, seed, **config.sa_kwargs))
        results["CP-SAT"].append(_run_cp_sat(sessions, dataset, context, group, seed, **config.cp_sat_kwargs))

    if config.run_bruteforce:
        logger.warning(
            "dataset=%s: bruteforce включён — имеет смысл только на маленьком числе сессий "
            "(см. total_assignment_space_size в BF.py), иначе не закончится.",
            dataset,
        )
        results["Bruteforce"] = [
            _run_bruteforce(sessions, dataset, context, group, **config.bruteforce_kwargs)
        ]

    return results


# ============================================================
# АГРЕГАЦИЯ ПО (АЛГОРИТМ, ДАТАСЕТ) + GAP К ЛУЧШЕМУ НАЙДЕННОМУ НА ЭТОМ ДАТАСЕТЕ
# ============================================================

@dataclass
class AggregatedResult:
    algorithm: str
    dataset: str
    n_runs: int
    success_rate: float  # доля прогонов с hard == 0
    soft_mean: Optional[float]
    soft_std: Optional[float]
    soft_min: Optional[float]
    soft_max: Optional[float]
    time_mean_ms: float
    time_std_ms: float
    gap_to_best_pct: Optional[float] = None  # заполняется в summarize_all, отдельно на каждый dataset


def aggregate(results: Sequence[RunResult]) -> AggregatedResult:
    algorithm, dataset = results[0].algorithm, results[0].dataset
    times = [r.wall_time_ms for r in results]
    feasible_softs = [r.soft for r in results if r.feasible]

    return AggregatedResult(
        algorithm=algorithm, dataset=dataset,
        n_runs=len(results),
        success_rate=len(feasible_softs) / len(results) if results else 0.0,
        soft_mean=statistics.mean(feasible_softs) if feasible_softs else None,
        soft_std=(statistics.stdev(feasible_softs) if len(feasible_softs) > 1 else 0.0) if feasible_softs else None,
        soft_min=min(feasible_softs) if feasible_softs else None,
        soft_max=max(feasible_softs) if feasible_softs else None,
        time_mean_ms=statistics.mean(times),
        time_std_ms=statistics.stdev(times) if len(times) > 1 else 0.0,
    )


def group_by_algorithm_and_dataset(results: Dict[str, List[RunResult]]) -> Dict[Tuple[str, str], List[RunResult]]:
    """results приходит как {"TS": [...], "GA": [...], ...} — это удобно для
    run_comparison одного датасета, но после накопления НЕСКОЛЬКИХ датасетов
    в один словарь (см. run_full_benchmark) внутри каждого списка лежит смесь
    разных dataset'ов. Перегруппировываем по (algorithm, dataset), чтобы
    агрегировать и считать gap корректно — раздельно по датасетам."""
    grouped: Dict[Tuple[str, str], List[RunResult]] = defaultdict(list)
    for runs in results.values():
        for r in runs:
            grouped[(r.algorithm, r.dataset)].append(r)
    return grouped


def summarize_all(results: Dict[str, List[RunResult]]) -> List[AggregatedResult]:
    grouped = group_by_algorithm_and_dataset(results)

    # best soft — ОТДЕЛЬНО на каждый датасет, не общий по всем сразу
    best_soft_by_dataset: Dict[str, float] = {}
    for (_, dataset), runs in grouped.items():
        feasible = [r.soft for r in runs if r.feasible]
        if feasible:
            best_soft_by_dataset[dataset] = min(best_soft_by_dataset.get(dataset, float("inf")), min(feasible))

    summaries = []
    for (algorithm, dataset), runs in grouped.items():
        agg = aggregate(runs)
        best_soft = best_soft_by_dataset.get(dataset)
        if agg.soft_mean is not None and best_soft is not None:
            agg.gap_to_best_pct = (
                (agg.soft_mean - best_soft) / best_soft * 100 if best_soft > 0
                else (0.0 if agg.soft_mean == best_soft else float("inf"))
            )
        summaries.append(agg)

    return summaries


def print_summary_table(summaries: List[AggregatedResult]) -> None:
    nan = float("nan")
    rows = sorted(summaries, key=lambda s: (s.dataset, s.algorithm))

    header = (
        f"{'dataset':<14} {'algorithm':<10} {'runs':>4} {'success%':>9} {'soft_mean':>10} "
        f"{'soft_std':>9} {'soft_min':>9} {'time_ms':>10} {'gap%':>7}"
    )
    print(header)
    print("-" * len(header))

    last_dataset = None
    for s in rows:
        if last_dataset is not None and s.dataset != last_dataset:
            print()  # пустая строка между датасетами — читать проще, когда их несколько
        last_dataset = s.dataset

        print(
            f"{s.dataset:<14} {s.algorithm:<10} {s.n_runs:>4} {s.success_rate * 100:>8.1f}% "
            f"{s.soft_mean if s.soft_mean is not None else nan:>10.3f} "
            f"{s.soft_std if s.soft_std is not None else nan:>9.3f} "
            f"{s.soft_min if s.soft_min is not None else nan:>9.3f} "
            f"{s.time_mean_ms:>10.1f} "
            f"{s.gap_to_best_pct if s.gap_to_best_pct is not None else nan:>6.1f}%"
        )


# ============================================================
# ЭКСПОРТ В CSV — под графики/таблицы в отчёте (pandas, Excel, matplotlib)
# ============================================================

def _write_csv(rows: List[Dict[str, Any]], path: str) -> None:
    if not rows:
        logger.warning("Нет данных для записи в %s", path)
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Записано %d строк в %s", len(rows), path)


def export_runs_csv(results: Dict[str, List[RunResult]], path: str) -> None:
    """Один ряд = один прогон. Для распределений/boxplot'ов по soft и времени."""
    rows = [
        {
            "algorithm": r.algorithm,
            "dataset": r.dataset,
            "seed": r.seed,
            "hard": r.hard,
            "soft": r.soft,
            "wall_time_ms": r.wall_time_ms,
            "status": r.status,
            **{f"extra_{k}": v for k, v in r.extra.items()},
        }
        for runs in results.values()
        for r in runs
    ]
    _write_csv(rows, path)


def export_convergence_csv(results: Dict[str, List[RunResult]], path: str) -> None:
    """Один ряд = одна точка trace. Для графиков сходимости (X=step, Y=soft/fitness)."""
    rows = [
        {
            "algorithm": r.algorithm,
            "dataset": r.dataset,
            "seed": r.seed,
            "step": p.step,
            "hard": p.hard,
            "soft": p.soft,
            "fitness": p.fitness,
        }
        for runs in results.values()
        for r in runs
        for p in r.trace
    ]
    _write_csv(rows, path)


def export_summary_csv(summaries: List[AggregatedResult], path: str) -> None:
    _write_csv([s.__dict__ for s in summaries], path)


# ============================================================
# УЗКОЕ СРАВНЕНИЕ: bruteforce sequential vs parallel
# (прямой потомок твоего старого compare_three_runs())
# ============================================================

def compare_bruteforce_modes(sessions, context, group) -> None:
    """
    Это не про качество решения — полный перебор последовательно и
    параллельно находит ОДИН И ТОТ ЖЕ оптимум по определению. Это про
    скорость и про явную проверку того, что параллельная версия не
    врёт (отдельная регрессия на тот самый баг с переиспользуемыми
    счётчиками calls в воркерах, который ты раньше ловил).
    """
    t0 = time.perf_counter()
    seq = solve_with_bruteforce(sessions, context, group)
    seq_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    par = solve_with_bruteforce_parallel(sessions, context, group)
    par_ms = (time.perf_counter() - t0) * 1000

    if seq.best_objective != par.best_objective:
        logger.error(
            "Sequential и parallel bruteforce нашли РАЗНЫЕ оптимумы (%s vs %s) — "
            "это баг, полный перебор обязан совпадать независимо от разбиения на процессы.",
            seq.best_objective, par.best_objective,
        )

    speedup = seq_ms / par_ms if par_ms > 0 else float("inf")
    logger.info(
        "Bruteforce: sequential %.1fms (%d calls) | parallel %.1fms (%d calls) | speedup x%.2f",
        seq_ms, seq.explored_calls, par_ms, par.explored_calls, speedup,
    )


# ============================================================
# ВНЕШНЯЯ ОРКЕСТРАЦИЯ: датасет × seed (а не только seed на одном датасете)
# ============================================================

def run_full_benchmark(
    dataset_specs: List[DatasetSpec],
    seeds: Sequence[int],
    group_students_count: int = 20,
    **per_algo_kwargs,
) -> Dict[str, List[RunResult]]:
    """per_algo_kwargs принимает те же поля, что ComparisonConfig, КРОМЕ
    sessions/dataset/context/group/seeds — они формируются здесь, отдельно
    на каждый dataset из dataset_specs. Например:
        run_full_benchmark(DATASET_PRESETS, seeds=range(1, 11),
                            ts_kwargs={"max_iterations": 1000},
                            run_bruteforce=True, bruteforce_kwargs={"limit": 5000})
    """
    all_results: Dict[str, List[RunResult]] = {"TS": [], "GA": [], "SA": [], "CP-SAT": []}

    for spec in dataset_specs:
        # seed=0 здесь фиксирует СТРУКТУРУ датасета (она должна быть одной и той же для
        # всех алгоритмов и всех seed'ов ниже) — случайность самих алгоритмов идёт через
        # seeds в ComparisonConfig, это разные вещи и их не стоит путать
        context = make_synthetic_context(seed=0, group_students_count=group_students_count, **spec.make_kwargs)
        group = context.groups[0]
        sessions = [s for d in context.disciplines for s in expand_discipline_to_sessions(d)]

        logger.info("--- датасет %-15s | %d сессий ---", spec.name, len(sessions))

        config = ComparisonConfig(
            sessions=sessions, dataset=spec.name, context=context, group=group, seeds=seeds, **per_algo_kwargs #, run_bruteforce=True
        )
        per_dataset = run_comparison(config)

        for algo, runs in per_dataset.items():
            all_results.setdefault(algo, []).extend(runs)

    return all_results
