"""
models.py

Диапазоны идентификаторов (берутся как range(N), т.е. 0..N-1):
    discipline_id : 0..5   -> 6 значений
    weekday_id    : 0..7   -> 8 значений
    timeslot_id   : 0..6   -> 7 значений
    audience_id   : 0..20  -> 21 значение
"""

from dataclasses import dataclass
from typing import List, Iterator, Optional

from src.config import (
    ALGORITHM_MAX_PAIRS_PER_WEEK,
    ALGORITHM_TIMESLOT_COUNT,
    ALGORITHM_WEEKDAY_COUNT,
)

# --- Диапазоны (количество значений, реальные id = range(COUNT)) ---
WEEKDAY_COUNT = ALGORITHM_WEEKDAY_COUNT
TIMESLOT_COUNT = ALGORITHM_TIMESLOT_COUNT


MAX_PAIRS_PER_WEEK = ALGORITHM_MAX_PAIRS_PER_WEEK


@dataclass(frozen=True, order=True, slots=True)
class Vec:
    """
    Один элемент расписания - "пара".
    vec = [discipline_id, weekday_id, timeslot_id, audience_id]
    """
    discipline_id: int
    weekday_id: int
    timeslot_id: int
    audience_id: int
    teacher_id: int

    def as_list(self) -> List[int]:
        return [self.discipline_id, self.weekday_id, self.timeslot_id, self.audience_id, self.teacher_id]

    def __repr__(self) -> str:
        return f"({self.discipline_id},{self.weekday_id},{self.timeslot_id},{self.audience_id},{self.teacher_id})"


class Schedule:
    """
    Расписание - массив векторов Vec.
    Ограничение: не более MAX_PAIRS_PER_WEEK элементов.
    """

    def __init__(self, max_pairs: int = MAX_PAIRS_PER_WEEK) -> None:
        self._items: List[Vec] = []
        self._max_pairs = max_pairs

    def add(self, vec: Vec) -> bool:
        """Добавляет вектор в расписание. Возвращает False, если лимит пар достигнут."""
        if len(self._items) >= self._max_pairs:
            return False
        self._items.append(vec)
        return True

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Vec]:
        return iter(self._items)

    def __getitem__(self, idx: int) -> Vec:
        return self._items[idx]

    def __contains__(self, vec: Vec) -> bool:
        return vec in self._items

    def to_list(self) -> List[List[int]]:
        return [v.as_list() for v in self._items]

    def pop(self) -> Optional[Vec]:
        """Удаляет и возвращает последний добавленный вектор (откат при переборе)."""
        if not self._items:
            return None
        return self._items.pop()

    def copy(self) -> "Schedule":
        """Снимок текущего состояния - нужен, когда расписание отдаётся
        наружу из перебора, а сам объект потом продолжает изменяться."""
        clone = Schedule(max_pairs=self._max_pairs)
        clone._items = list(self._items)
        return clone

    def __repr__(self) -> str:
        return f"Schedule({[repr(v) for v in self._items]})"
