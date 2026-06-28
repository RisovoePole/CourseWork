from src.algorithm_comparison import *
from src.synthetic_data import DATASET_PRESETS 
from src.hyperparameter_sweep import run_full_sweep, print_sweep_summary


def main() -> None:
    results = run_full_benchmark(DATASET_PRESETS, seeds=range(1, 11))
    summaries = summarize_all(results)
    print_summary_table(summaries)
    export_runs_csv(results, "results/runs.csv")
    export_convergence_csv(results, "results/convergence.csv")
    export_summary_csv(summaries, "results/summary.csv")


    results = run_full_sweep("medium")
    print_sweep_summary(results)

    flat = {f"{algo}": runs for algo, runs in results.items()}
    export_runs_csv(flat, "results/hyperparameter_sweep.csv")


if __name__ == "__main__":
    main()
