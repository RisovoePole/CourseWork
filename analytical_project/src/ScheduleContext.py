from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from orm.audience import AudienceORM
from orm.roomtype import RoomTypeORM
from orm.professor import ProfessorORM
from orm.discipline import DisciplineORM
from orm.students_group import StudentsGroupORM
from orm.professor_discipline import professor_discipline
from orm.audience_roomtype import audience_roomtype

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

@dataclass(frozen=True)
class Audience:
    id: int
    name: str
    seats: int


@dataclass(frozen=True)
class Group:
    id: int
    name: str
    students_count: int


@dataclass(frozen=True)
class Professor:
    id: int
    name: str


@dataclass(frozen=True)
class Discipline:
    id: int
    name: str
    optimal_room_types: Set[int]

    course_hours: float
    seminar_hours: float
    lab_hours: float

@dataclass(frozen=True)
class RoomType:
    id: int
    name: str

class ScheduleContext:

    # -------------------------
    # GLOBAL CONFIG (UPPER CASE)
    # -------------------------
    class CONFIG:
        PROFESSORS_COUNT: int = 0
        AUDIENCES_COUNT: int = 0
        ROOM_TYPES_COUNT: int = 0
        DISCIPLINES_COUNT: int = 0

        WEEKDAY_COUNT: int = 0
        MAX_PAIRS_PER_WEEK: int = 0
        MAX_PAIRS_PER_DAY: int = 0

    # -------------------------
    # INIT
    # -------------------------
    def __init__(
        self,
        audiences: List[Audience],
        groups: List[Group],
        professors: List[Professor],
        disciplines: List[Discipline],
        roomtypes: List[RoomType],
        professor_discipline: Dict[int, Set[int]],
        discipline_professors: Dict[int, Set[int]],
        audience_roomtypes: Dict[int, Set[int]],
        roomtype_audiences: Dict[int, Set[int]]
    ):

        self.audiences = audiences
        self.groups = groups
        self.professors = professors
        self.disciplines = disciplines
        self.roomtypes = roomtypes

        # relations
        self.professor_discipline = professor_discipline
        self.discipline_professors = discipline_professors
        self.audience_roomtypes = audience_roomtypes
        self.roomtype_audiences = roomtype_audiences

        # -------------------
        # INDEXES
        # -------------------
        self.audience_by_id = {a.id: a for a in audiences}
        self.group_by_id = {g.id: g for g in groups}
        self.professor_by_id = {p.id: p for p in professors}
        self.discipline_by_id = {d.id: d for d in disciplines}
        self.roomtype_by_id = {r.id: r for r in roomtypes}

        self._init_config()
        # -------------------------
        # CONFIG INIT
        # -------------------------
    def _init_config(self):
        self.CONFIG.PROFESSORS_COUNT = len(self.professors)
        self.CONFIG.AUDIENCES_COUNT = len(self.audiences)
        self.CONFIG.DISCIPLINES_COUNT = len(self.disciplines)
        self.CONFIG.ROOM_TYPES_COUNT = len(self.roomtypes)

        self.CONFIG.WEEKDAY_COUNT = get_env_int("ALGORITHM_WEEKDAY_COUNT", 0)
        self.CONFIG.MAX_PAIRS_PER_DAY = get_env_int("ALGORITHM_MAX_PAIRS_PER_DAY", 0)
        self.CONFIG.MAX_PAIRS_PER_WEEK = get_env_int("ALGORITHM_MAX_PAIRS_PER_WEEK", 0)

    # -----------------------------
    # LOAD FROM DB (MAIN METHOD)
    # -----------------------------
    @classmethod
    def load_from_db(cls, session: Session) -> "ScheduleContext":

        audiences_raw = session.execute(select(AudienceORM)).scalars().all()
        groups_raw = session.execute(select(StudentsGroupORM)).scalars().all()
        professors_raw = session.execute(select(ProfessorORM)).scalars().all()
        disciplines_raw = session.execute(select(DisciplineORM)).scalars().all()
        roomtypes_raw = session.execute(select(RoomTypeORM)).scalars().all()

        aud_rt_raw = session.execute(select(audience_roomtype)).all()
        prof_disc_raw = session.execute(select(professor_discipline)).all()
        # -------------------------
        # MAP ORM -> DOMAIN
        # -------------------------
        audiences = [
            Audience(
                id=a.audience_id,
                name=a.room_name,
                seats=a.amount_of_seats
            )
            for a in audiences_raw
        ]

        groups = [
            Group(
                id=g.students_group_id,
                name=g.group_name,
                students_count=g.students_count
            )
            for g in groups_raw
        ]

        professors = [
            Professor(id=p.professor_id, name=p.name)
            for p in professors_raw
        ]

        disciplines = [
            Discipline(
                id=d.discipline_id,
                name=d.discipline_name,
                optimal_room_types=set(d.optimal_room_type or []),
                course_hours=d.course_hours,
                seminar_hours=d.seminar_hours,
                lab_hours=d.lab_hours
            )
            for d in disciplines_raw
        ]

        roomtypes = [
            RoomType(id=r.room_type_id, name=r.room_type_name)
            for r in roomtypes_raw
        ]
        # -------------------------
        # RELATION MAP
        # -------------------------
        prof_disc = {}
        disc_prof = {}

        for r in prof_disc_raw:
            prof_disc.setdefault(r.professor_id, set()).add(r.discipline_id)
            disc_prof.setdefault(r.discipline_id, set()).add(r.professor_id)

        aud_rt = {}
        rt_aud = {}

        for r in aud_rt_raw:
            aud_rt.setdefault(r.audience_id, set()).add(r.room_type_id)
            rt_aud.setdefault(r.room_type_id, set()).add(r.audience_id)
        # -------------------------
        # BUILD CONTEXT
        # -------------------------
        return cls(
            audiences=audiences,
            groups=groups,
            professors=professors,
            disciplines=disciplines,
            roomtypes=roomtypes,
            professor_discipline=prof_disc,
            discipline_professors=disc_prof,
            audience_roomtypes=aud_rt,
            roomtype_audiences=rt_aud
        )
    

    def _invert(self, m: Dict[int, Set[int]]) -> Dict[int, Set[int]]:
        res: Dict[int, Set[int]] = {}
        for k, vals in m.items():
            for v in vals:
                res.setdefault(v, set()).add(k)
        return res
    def get_professor_disciplines(self, professor_id: int) -> Set[int]:
        return self.professor_discipline.get(professor_id, set())

    def get_discipline_professors(self, discipline_id: int) -> Set[int]:
        return self.discipline_professors.get(discipline_id, set())

    def get_audience(self, id: int) -> Audience:
        return self.audience_by_id[id]

    def get_group(self, id: int) -> Group:
        return self.group_by_id[id]

    def get_professor(self, id: int) -> Professor:
        return self.professor_by_id[id]

    def get_discipline(self, id: int) -> Discipline:
        return self.discipline_by_id[id]
    