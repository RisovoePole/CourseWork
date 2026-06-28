from dataclasses import dataclass
from typing import List, Iterator, Optional
from orm.schedule import ScheduleORM

@dataclass(frozen=True, order=True, slots=True)
class Vec:
    discipline_id: int
    weekday_id: int
    timeslot_id: int
    audience_id: int
    professor_id: int

    def as_list(self) -> List[int]:
        return [self.discipline_id, self.weekday_id, self.timeslot_id, self.audience_id, self.professor_id]

    def __repr__(self) -> str:
        return f"({self.discipline_id},{self.weekday_id},{self.timeslot_id},{self.audience_id},{self.professor_id})"


class Schedule:
    """
    Расписание - массив векторов Vec.
    Ограничение: не более MAX_PAIRS_PER_WEEK элементов.
    """

    def __init__(self, max_pairs: int) -> None:
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

    def save_to_db(self, session) -> None:
        session.add_all([
        ScheduleORM(
            day_of_week=v.weekday_id,
            pair_number=v.timeslot_id,
            audience_id=v.audience_id,
            discipline_id=v.discipline_id,
            professor_id=v.professor_id,
        )
            for v in self._items
        ])
        session.commit()

    def replace(self, idx: int, vec: Vec) -> None:
        """Точечная замена элемента — нужна для локальных модификаций (Tabu Search и т.п.)."""
        self._items[idx] = vec

    def __repr__(self) -> str:
        return f"Schedule({[repr(v) for v in self._items]})"
