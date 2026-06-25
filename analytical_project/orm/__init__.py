from .base import Base
from .groups import Group
from .teachers import Teacher
from .subjects import Subject
from .rooms import Room
from .time_slots import TimeSlot
from .lesson_requirements import LessonRequirement
from .algorithm_runs import AlgorithmRun
from .scheduled_lessons import ScheduledLesson
from .curriculum import Curriculum

__all__ = [
    "Base",
    "Group",
    "Teacher",
    "Subject",
    "Room",
    "TimeSlot",
    "LessonRequirement",
    "AlgorithmRun",
    "ScheduledLesson",
    "Curriculum",
]

try:
    from src.models import (
        AUDIENCE_COUNT,
        DISCIPLINE_COUNT,
        MAX_PAIRS_PER_WEEK,
        Schedule,
        TIMESLOT_COUNT,
        WEEKDAY_COUNT,
        Vec,
    )
except ModuleNotFoundError:
    pass
else:
    __all__.extend([
        "AUDIENCE_COUNT",
        "DISCIPLINE_COUNT",
        "MAX_PAIRS_PER_WEEK",
        "Schedule",
        "TIMESLOT_COUNT",
        "WEEKDAY_COUNT",
        "Vec",
    ])