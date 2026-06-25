import os

from dotenv import load_dotenv


load_dotenv()


def get_env_int(name: str, default: int, minimum: int = 1) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc

    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {parsed}")

    return parsed


ALGORITHM_DISCIPLINE_COUNT = get_env_int("ALGORITHM_DISCIPLINE_COUNT", 6)
ALGORITHM_WEEKDAY_COUNT = get_env_int("ALGORITHM_WEEKDAY_COUNT", 8)
ALGORITHM_TIMESLOT_COUNT = get_env_int("ALGORITHM_TIMESLOT_COUNT", 7)
ALGORITHM_AUDIENCE_COUNT = get_env_int("ALGORITHM_AUDIENCE_COUNT", 21)
ALGORITHM_MAX_PAIRS_PER_WEEK = get_env_int("ALGORITHM_MAX_PAIRS_PER_WEEK", 15)
ALGORITHM_MAX_PAIRS_PER_DAY = get_env_int("ALGORITHM_MAX_PAIRS_PER_DAY", 2)
ALGORITHM_RUN_MAX_PAIRS = get_env_int("ALGORITHM_RUN_MAX_PAIRS", 3)