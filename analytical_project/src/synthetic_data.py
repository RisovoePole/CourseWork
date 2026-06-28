"""
synthetic_data.py

ScheduleContext без БД, без .env, без SQLAlchemy-сессии — напрямую из
Python. Параметризовано так, чтобы получать датасеты разного размера И
разной "трудности" (через professors_per_discipline/roomtypes_per_audience —
чем меньше, тем туже ограничения, независимо от размера задачи).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from src.ScheduleContext import Audience, Config, Discipline, Group, Professor, RoomType, ScheduleContext


def make_synthetic_context(
    *,
    num_disciplines: int,
    num_professors: int,
    num_audiences: int,
    num_roomtypes: int,
    weekday_count: int,
    max_pairs_per_day: int,
    professors_per_discipline: int = 2,
    roomtypes_per_audience: int = 1,
    group_students_count: int = 20,
    seed: Optional[int] = None,
) -> ScheduleContext:
    rng = random.Random(seed)

    roomtypes = [RoomType(id=i, name=f"type_{i}") for i in range(num_roomtypes)]
    audiences = [Audience(id=i, name=f"A{i}", seats=rng.choice([20, 30, 40, 60, 120])) for i in range(num_audiences)]
    professors = [Professor(id=i, name=f"Professor {i}") for i in range(num_professors)]
    groups = [Group(id=0, name="G0", students_count=group_students_count)]

    audience_roomtypes: Dict[int, Set[int]] = {}
    roomtype_audiences: Dict[int, Set[int]] = {}
    for a in audiences:
        types = rng.sample(range(num_roomtypes), k=min(roomtypes_per_audience, num_roomtypes))
        audience_roomtypes[a.id] = set(types)
        for t in types:
            roomtype_audiences.setdefault(t, set()).add(a.id)

    disciplines: List[Discipline] = []
    professor_discipline: Dict[int, Set[int]] = {}
    discipline_professors: Dict[int, Set[int]] = {}

    for d_id in range(num_disciplines):
        optimal_types = set(rng.sample(range(num_roomtypes), k=min(2, num_roomtypes)))
        disciplines.append(Discipline(
            id=d_id, name=f"Discipline {d_id}", optimal_room_types=optimal_types,
            course_hours=float(rng.choice([0, 2, 4])),
            seminar_hours=float(rng.choice([0, 2])),
            lab_hours=float(rng.choice([0, 2])),
        ))

        qualified = rng.sample(range(num_professors), k=min(professors_per_discipline, num_professors))
        discipline_professors[d_id] = set(qualified)
        for p_id in qualified:
            professor_discipline.setdefault(p_id, set()).add(d_id)

    # Явно собранный Config — без чтения .env/os.getenv, в этом и смысл развязки
    config = Config(
        PROFESSORS_COUNT=num_professors,
        AUDIENCES_COUNT=num_audiences,
        ROOM_TYPES_COUNT=num_roomtypes,
        DISCIPLINES_COUNT=num_disciplines,
        WEEKDAY_COUNT=weekday_count,
        MAX_PAIRS_PER_DAY=max_pairs_per_day,
        MAX_PAIRS_PER_WEEK=weekday_count * max_pairs_per_day,
    )

    return ScheduleContext(
        config=config,
        audiences=audiences, groups=groups, professors=professors,
        disciplines=disciplines, roomtypes=roomtypes,
        professor_discipline=professor_discipline, discipline_professors=discipline_professors,
        audience_roomtypes=audience_roomtypes, roomtype_audiences=roomtype_audiences,
    )


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    make_kwargs: dict


# Размер и "трудность" — НЕЗАВИСИМЫЕ оси. small_tight специально маленький,
# но professors_per_discipline=1 / roomtypes_per_audience=1 делает его туже,
# чем medium — хороший контрпример для "большое значит сложнее".
DATASET_PRESETS: List[DatasetSpec] = [
    DatasetSpec("tiny_easy", dict(
        num_disciplines=4, num_professors=8, num_audiences=10, num_roomtypes=3,
        weekday_count=5, max_pairs_per_day=4, professors_per_discipline=4, roomtypes_per_audience=2,
    )),
    DatasetSpec("small_tight", dict(
        num_disciplines=6, num_professors=6, num_audiences=8, num_roomtypes=4,
        weekday_count=5, max_pairs_per_day=4, professors_per_discipline=1, roomtypes_per_audience=1,
    )),
    DatasetSpec("medium", dict(
        num_disciplines=12, num_professors=15, num_audiences=15, num_roomtypes=4,
        weekday_count=6, max_pairs_per_day=6, professors_per_discipline=2, roomtypes_per_audience=2,
    )),
    DatasetSpec("large_stress", dict(
        num_disciplines=25, num_professors=20, num_audiences=20, num_roomtypes=5,
        weekday_count=6, max_pairs_per_day=7, professors_per_discipline=2, roomtypes_per_audience=2,
    )),
]