"""
rules.py
Правила (ограничения) для проверки, можно ли добавить пару (Vec) в расписание.

Rule - базовый абстрактный класс. Любое правило отвечает на один вопрос:
    "можно ли добавить vec в schedule, не нарушив это правило?"
Чтобы создать своё правило - наследуемся от Rule и реализуем can_add().

ConstraintEngine объединяет несколько правил и проверяет их все сразу
(аналог ConstraintEngine.java из основного GA-проекта ScheduleGen).
"""

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from src.models import Vec, Schedule


class Rule(ABC):
    """Базовый класс правила-ограничения."""

    name: str = "Rule"

    @abstractmethod
    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        """True, если vec можно добавить в schedule без нарушения правила."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<Rule:{self.name}>"


# ---------------------------------------------------------------------------
# Готовые правила
# ---------------------------------------------------------------------------

class NoDuplicateVectorRule(Rule):
    """Запрещает добавлять полностью идентичный вектор дважды."""

    name = "NoDuplicateVector"

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        return vec not in schedule


class NoAudienceTimeConflictRule(Rule):
    """
    Одна аудитория не может быть занята двумя парами одновременно
    (совпадение weekday_id + timeslot_id + audience_id).
    """

    name = "NoAudienceTimeConflict"

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        for existing in schedule:
            if (
                existing.audience_id == vec.audience_id
                and existing.weekday_id == vec.weekday_id
                and existing.timeslot_id == vec.timeslot_id
            ):
                return False
        return True


class NoDisciplineTimeConflictRule(Rule):
    """
    Одна дисциплина не может стоять дважды в одно и то же время
    (предполагается, что у дисциплины одна группа/поток).
    """

    name = "NoDisciplineTimeConflict"

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        for existing in schedule:
            if (
                existing.discipline_id == vec.discipline_id
                and existing.weekday_id == vec.weekday_id
                and existing.timeslot_id == vec.timeslot_id
            ):
                return False
        return True


class MaxPairsPerDayRule(Rule):
    """Ограничивает количество пар в одном дне недели (weekday_id)."""

    def __init__(self, max_pairs_per_day: int) -> None:
        self.max_pairs_per_day = max_pairs_per_day
        self.name = f"MaxPairsPerDay({max_pairs_per_day})"

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        count = sum(1 for existing in schedule if existing.weekday_id == vec.weekday_id)
        return count < self.max_pairs_per_day


class MaxPairsPerDisciplineRule(Rule):
    """Ограничивает, сколько раз дисциплина может встретиться в неделе."""

    def __init__(self, max_per_discipline: int) -> None:
        self.max_per_discipline = max_per_discipline
        self.name = f"MaxPairsPerDiscipline({max_per_discipline})"

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        count = sum(1 for existing in schedule if existing.discipline_id == vec.discipline_id)
        return count < self.max_per_discipline


# ---------------------------------------------------------------------------
# Движок проверки нескольких правил сразу
# ---------------------------------------------------------------------------

class ConstraintEngine:
    """
    Объединяет несколько правил Rule и проверяет добавление вектора
    по всем правилам сразу.
    """

    def __init__(self, rules: Optional[Iterable[Rule]] = None) -> None:
        self.rules: List[Rule] = list(rules) if rules else []
        self.calls = 0

    def add_rule(self, rule: Rule) -> "ConstraintEngine":
        self.rules.append(rule)
        return self

    def can_add(self, schedule: Schedule, vec: Vec) -> bool:
        """True, если vec проходит ВСЕ зарегистрированные правила."""
        self.calls += 1
        for rule in self.rules:
            if not rule.can_add(schedule, vec):
                return False
        return True

    def reset_calls(self) -> None:
        self.calls = 0

    def first_violation(self, schedule: Schedule, vec: Vec) -> Optional[Rule]:
        """Возвращает первое нарушенное правило или None, если всё ок."""
        for rule in self.rules:
            if not rule.can_add(schedule, vec):
                return rule
        return None

    def __repr__(self) -> str:
        return f"ConstraintEngine({self.rules})"
