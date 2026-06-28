from src.algorithm_comparison import *
from src.synthetic_data import DATASET_PRESETS 



def main() -> None:
    results = run_full_benchmark(DATASET_PRESETS, seeds=range(1, 11))
    summaries = summarize_all(results)
    print_summary_table(summaries)
    export_runs_csv(results, "results/runs.csv")
    export_convergence_csv(results, "results/convergence.csv")
    export_summary_csv(summaries, "results/summary.csv")



if __name__ == "__main__":
    main()
