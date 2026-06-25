import importlib
import os
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path


ALGORITHM_ENV_KEYS = (
	"ALGORITHM_DISCIPLINE_COUNT",
	"ALGORITHM_WEEKDAY_COUNT",
	"ALGORITHM_TIMESLOT_COUNT",
	"ALGORITHM_AUDIENCE_COUNT",
	"ALGORITHM_MAX_PAIRS_PER_WEEK",
	"ALGORITHM_MAX_PAIRS_PER_DAY",
	"ALGORITHM_RUN_MAX_PAIRS",
)

MODULES_TO_RELOAD = (
	"src.config",
	"src.models",
	"src.rules",
	"src.bruteforce",
	"src.main",
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@contextmanager
def temporary_env(overrides: dict[str, str], clear_algorithm_keys: bool = True):
	original = os.environ.copy()
	try:
		if clear_algorithm_keys:
			for key in ALGORITHM_ENV_KEYS:
				os.environ.pop(key, None)

		for key, value in overrides.items():
			os.environ[key] = value

		yield
	finally:
		os.environ.clear()
		os.environ.update(original)


@contextmanager
def project_on_syspath():
	project_root_str = str(PROJECT_ROOT)
	had_root = project_root_str in sys.path
	if had_root:
		sys.path.remove(project_root_str)
	sys.path.insert(0, project_root_str)
	try:
		yield
	finally:
		if project_root_str in sys.path:
			sys.path.remove(project_root_str)
		if had_root:
			sys.path.insert(0, project_root_str)


def ensure_dotenv_stub() -> None:
	if "dotenv" in sys.modules:
		return

	dotenv = types.ModuleType("dotenv")

	def load_dotenv(*_args, **_kwargs):
		return False

	setattr(dotenv, "load_dotenv", load_dotenv)
	sys.modules["dotenv"] = dotenv


def load_modules_for_current_env():
	ensure_dotenv_stub()
	for module_name in MODULES_TO_RELOAD:
		sys.modules.pop(module_name, None)

	main = importlib.import_module("src.main")
	bruteforce = importlib.import_module("src.bruteforce")
	return main, bruteforce


class TestThreeAlgorithmsWithEnvConfigs(unittest.TestCase):
	def test_different_env_runs_match_on_result_counts(self):
            scenarios = [
                    {
                        "name": "ultra_easy", # Легкий старт
                        "env": {
                            "ALGORITHM_DISCIPLINE_COUNT": "2",
                            "ALGORITHM_WEEKDAY_COUNT": "2",
                            "ALGORITHM_TIMESLOT_COUNT": "2",
                            "ALGORITHM_AUDIENCE_COUNT": "2",
                            "ALGORITHM_MAX_PAIRS_PER_WEEK": "2",
                            "ALGORITHM_MAX_PAIRS_PER_DAY": "1",
                            "ALGORITHM_RUN_MAX_PAIRS": "2",
                        },
                    },
                    {
                        "name": "very_easy", # Почти мгновенно
                        "env": {
                            "ALGORITHM_DISCIPLINE_COUNT": "3",
                            "ALGORITHM_WEEKDAY_COUNT": "5",
                            "ALGORITHM_TIMESLOT_COUNT": "4",
                            "ALGORITHM_AUDIENCE_COUNT": "5",
                            "ALGORITHM_MAX_PAIRS_PER_WEEK": "5",
                            "ALGORITHM_MAX_PAIRS_PER_DAY": "3",
                            "ALGORITHM_RUN_MAX_PAIRS": "3",
                        },
                    },
                    {
                        "name": "medium", 
                        "env": {
                            "ALGORITHM_DISCIPLINE_COUNT": "3",
                            "ALGORITHM_WEEKDAY_COUNT": "5",
                            "ALGORITHM_TIMESLOT_COUNT": "4",
                            "ALGORITHM_AUDIENCE_COUNT": "5",
                            "ALGORITHM_MAX_PAIRS_PER_WEEK": "4",
                            "ALGORITHM_MAX_PAIRS_PER_DAY": "3",
                            "ALGORITHM_RUN_MAX_PAIRS": "4",
                        },
                    },
                    # {
                    #     "name": "ultra_hard", 
                    #     "env": {
                    #         "ALGORITHM_DISCIPLINE_COUNT": "12",
                    #         "ALGORITHM_WEEKDAY_COUNT": "5",
                    #         "ALGORITHM_TIMESLOT_COUNT": "6",
                    #         "ALGORITHM_AUDIENCE_COUNT": "6",
                    #         "ALGORITHM_MAX_PAIRS_PER_WEEK": "25",
                    #         "ALGORITHM_MAX_PAIRS_PER_DAY": "5",
                    #         "ALGORITHM_RUN_MAX_PAIRS": "20",
                    #     },
                    # },
                ]
                
		
            with project_on_syspath():
                for scenario in scenarios:
                    with self.subTest(scenario=scenario["name"]):
                        with temporary_env(scenario["env"]):
                            main, bruteforce = load_modules_for_current_env()

                            print(f"----{scenario['name']}-----", file=sys.stdout)
                            sys.stdout.flush()
                            
                            parallel_count, _ = main.run_parallel()
                            backtracking_count, _ = main.run_backtracking()

                        self.assertEqual(parallel_count, backtracking_count)


if __name__ == "__main__":
	unittest.main()
