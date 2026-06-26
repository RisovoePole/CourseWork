from abc import ABC, abstractmethod

from models import Schedule


class ScheduleGenerator(ABC):

    @abstractmethod
    def generate_schedule(self) -> Schedule:
        """
        Генерирует расписание.
        """
        pass