"""
bruteforce.py
Алгоритм полного перебора (full enumeration / brute-force) для построения
расписаний из примитивов Vec.

В модуле два варианта перебора:


1. enumerate_schedules_backtracking() - перебор "по разрядам", как
   счётчик 0000, 0001, 0002, ...: вектора пробуются по одному, каждый
   сразу проверяется через ConstraintEngine.can_add(); если проверка не
   прошла - сразу переходим к следующему вектору-кандидату, никуда не
   углубляясь; если прошла - добавляем вектор и пробуем расширить
   расписание дальше, а после возврата откатываем (pop). Невалидные
   ветки отсекаются немедленно, на первом нарушающем векторе - это
   и есть содержательная разница с наивным вариантом.

2. Точно такой же алгоритм, но параллельный.

Размер пространства одной пары:
    N = DISCIPLINE_COUNT * WEEKDAY_COUNT * TIMESLOT_COUNT * AUDIENCE_COUNT
        = 6 * 8 * 7 * 21 = 7056

Количество расписаний размера k без каких-либо ограничений совместимости
равно C(N, k). Для k=15 это C(7056, 15) ~ 10^45 - даже с отсечением
веток полный перебор на реальных диапазонах задачи невыполним физически.
Поэтому весь модуль рассчитан на:
  - демонстрацию принципа (небольшие диапазоны / небольшое k),
  - расчёт сложности (total_schedules_count), который можно
    использовать как аргумент в пользу GA / SA / Tabu / CP-SAT.
"""

import itertools
import math
import os
import concurrent.futures as cf
from typing import Iterator, List, Optional

from src.models import (
    DISCIPLINE_COUNT,
    WEEKDAY_COUNT,
    TIMESLOT_COUNT,
    AUDIENCE_COUNT,
    MAX_PAIRS_PER_WEEK,
    Vec,
    Schedule,
)
from src.bruteforce.rules import ConstraintEngine


def all_vectors() -> Iterator[Vec]:
    """Полный перебор всех возможных одиночных векторов (пар)."""
    for discipline_id, weekday_id, timeslot_id, audience_id in itertools.product(
        range(DISCIPLINE_COUNT),
        range(WEEKDAY_COUNT),
        range(TIMESLOT_COUNT),
        range(AUDIENCE_COUNT),
    ):
        yield Vec(discipline_id, weekday_id, timeslot_id, audience_id)


def total_vectors_count() -> int:
    """Размер пространства одной пары (|V|)."""
    return DISCIPLINE_COUNT * WEEKDAY_COUNT * TIMESLOT_COUNT * AUDIENCE_COUNT


def schedules_count_for_size(k: int) -> int:
    """Сколько расписаний ровно из k пар существует: C(|V|, k)."""
    return math.comb(total_vectors_count(), k)


def total_schedules_count(max_pairs: int = MAX_PAIRS_PER_WEEK) -> int:
    """Сколько всего расписаний размером от 1 до max_pairs пар."""
    return sum(schedules_count_for_size(k) for k in range(1, max_pairs + 1))





def enumerate_schedules_backtracking(
    max_pairs: int = MAX_PAIRS_PER_WEEK,
    exact_size: bool = False,
    engine: Optional[ConstraintEngine] = None,
    limit: Optional[int] = None,
    materialize: bool = True,
) -> Iterator[Optional[Schedule]]:
    """
    Перебор "по разрядам" (как счётчик 0000, 0001, 0002, ...) с немедленной
    проверкой и откатом

    Алгоритм:
      1. Берём очередной вектор-кандидат (по возрастанию индекса).
      2. Сразу пробуем добавить его в ТЕКУЩЕЕ расписание -
         engine.can_add(schedule, candidate).
      3. Если проверка НЕ прошла - никуда не углубляемся, просто берём
         следующий вектор-кандидат на этом же уровне ("следующий разряд").
      4. Если проверка прошла - добавляем вектор в расписание (оно стало
         валиднее на 1 пару) и пробуем расширить его дальше.
      5. Когда ветка исследована до конца - откатываем последний
         добавленный вектор (schedule.pop()) и продолжаем со следующего
         кандидата на этом уровне.

    Каждое непустое промежуточное расписание, которое подходит по размеру,
    отдаётся как валидный результат (то есть множество валидных расписаний
    собирается постепенно, по мере перебора).

    Ключевое отличие от enumerate_schedules_naive(): здесь невалидная ветка
    обрывается на первом же нарушающем векторе и дальше по ней вообще
    ничего не строится - не нужно сначала собрать всё сочетание, чтобы
    потом его выбросить.

    Вектора пробуются по возрастанию индекса (idx, idx+1, idx+2, ...),
    а не "с нуля" на каждом уровне - иначе одно и то же множество пар
    в расписании находилось бы многократно, в разном порядке (порядок
    пар в расписании не имеет значения, важен только сам набор).

    materialize - если True (по умолчанию), на каждый найденный результат
                  отдаётся ПОЛНАЯ КОПИЯ расписания (schedule.copy()).
                  Если требуется только посчитать количество валидных
                  расписаний (не сохраняя их все), поставь materialize=False -
                  генератор будет отдавать None вместо копии, что экономит
                  и время (нет лишних аллокаций), и память. Пример:
                      count = sum(1 for _ in enumerate_schedules_backtracking(
                          max_pairs=10, engine=engine, materialize=False))
    """
    if max_pairs > MAX_PAIRS_PER_WEEK:
        raise ValueError(f"max_pairs не может превышать {MAX_PAIRS_PER_WEEK}")

    vectors: List[Vec] = list(all_vectors())
    schedule = Schedule(max_pairs=max_pairs)
    yielded = 0

    def limit_reached() -> bool:
        return limit is not None and yielded >= limit

    # Стек кадров: каждый кадр - это итератор по range(start_idx, len(vectors))
    # для соответствующего уровня перебора. Наличие кадра в стеке == то же
    # самое, что "находимся внутри вызова recurse(start_idx)" в рекурсии.
    stack: List[Iterator[int]] = [iter(range(0, len(vectors)))]

    # Проверка для нулевого уровня - в рекурсии это было самое начало
    # recurse(0), выполняющееся ДО входа в цикл for. size == 0 здесь
    # всегда (schedule только создан), так что в исходнике это условие
    # никогда не сработало бы на первом входе - но сохраняем для полной
    # симметрии с рекурсивной структурой (на случай вызова с непустым
    # schedule в будущем, и просто чтобы код буквально отражал оригинал).
    size = len(schedule)
    if size > 0 and (not exact_size or size == max_pairs):
        yield schedule.copy() if materialize else None
        yielded += 1

    while stack:
        if limit_reached():
            return

        size = len(schedule)

        if size >= max_pairs:
            # Эквивалент "return" в конце recurse() - выходим с этого
            # уровня и откатываем то, что было добавлено при входе в него.
            stack.pop()
            if schedule:
                schedule.pop()
            continue

        idx = next(stack[-1], None)

        if idx is None:
            # range() на этом уровне исчерпан - конец for, возврат на
            # уровень выше (откатываем добавленный на этом уровне вектор).
            stack.pop()
            if schedule:
                schedule.pop()
            continue

        if limit_reached():
            return

        candidate = vectors[idx]

        if engine is not None and not engine.can_add(schedule, candidate):
            continue  # проверка не прошла - следующий idx на этом же уровне

        schedule.add(candidate)

        size = len(schedule)
        if size > 0 and (not exact_size or size == max_pairs):
            yield schedule.copy() if materialize else None
            yielded += 1

        if limit_reached():
            # Сразу выходим, не углубляясь дальше - откатываем то, что
            # только что добавили, и завершаем генератор полностью.
            schedule.pop()
            return

        # "Спуск" на следующий уровень - аналог yield from recurse(idx + 1).
        stack.append(iter(range(idx + 1, len(vectors))))

# ---------------------------------------------------------------------------
# Параллельная версия (несколько процессов, все ядра CPU)
# ---------------------------------------------------------------------------
#
# Идея: ветки, у которых отличается ПЕРВЫЙ вектор расписания, полностью
# независимы друг от друга (ни общих данных, ни общего состояния).
# Поэтому можно раздать каждому процессу-воркеру свой кандидат на позицию 0
# и дальше внутри него выполнить ровно тот же перебор с откатом - результат
# будет идентичен последовательному варианту, просто посчитан параллельно.

_worker_state: dict = {}


def _init_worker(
    vectors: List[Vec],
    engine: Optional[ConstraintEngine],
    max_pairs: int,
    exact_size: bool,
    materialize: bool,
) -> None:
    """Выполняется один раз на каждый процесс-воркер при его старте -
    тяжёлые объекты (vectors, engine) передаются сюда один раз, а не на
    каждую задачу, что сильно снижает накладные расходы на pickle/IPC."""
    _worker_state["vectors"] = vectors
    _worker_state["engine"] = engine
    _worker_state["max_pairs"] = max_pairs
    _worker_state["exact_size"] = exact_size
    _worker_state["materialize"] = materialize


def _explore_recursive(
    vectors: List[Vec],
    engine: Optional[ConstraintEngine],
    max_pairs: int,
    exact_size: bool,
    start_idx: int,
    schedule: Schedule,
    materialize: bool,
    results: List[List[List[int]]],
    counter: List[int],
) -> None:
    """Использует явный стек
    кадров вместо стека вызовов интерпретатора. Это убирает риск
    RecursionError на больших max_pairs/датасетах и немного снижает
    оверхед на вызовы функций."""

    # Каждый кадр стека соответствует одному уровню рекурсии:
    # iterator - "куда мы дошли" в переборе vectors на этом уровне.
    # Сам факт наличия кадра в стеке == "мы внутри этого уровня вызова".
    stack: List[Iterator[int]] = [iter(range(start_idx, len(vectors)))]

    # Проверка для самого первого (нулевого) уровня - в рекурсивной версии
    # это была проверка в начале функции, до первого цикла for.
    size = len(schedule)
    if size > 0 and (not exact_size or size == max_pairs):
        counter[0] += 1
        if materialize:
            results.append(schedule.to_list())

    while stack:
        size = len(schedule)

        if size >= max_pairs:
            # Эквивалент "return" на текущем уровне рекурсии -
            # просто выкидываем кадр и откатываем добавленный элемент.
            stack.pop()
            if schedule:
                schedule.pop()
            continue

        idx = next(stack[-1], None)

        if idx is None:
            # Перебор range() на этом уровне закончился - эквивалент
            # выхода из for и возврата на уровень выше.
            stack.pop()
            if schedule:
                schedule.pop()
            continue

        candidate = vectors[idx]
        if engine is not None and not engine.can_add(schedule, candidate):
            continue

        schedule.add(candidate)

        size = len(schedule)
        if size > 0 and (not exact_size or size == max_pairs):
            counter[0] += 1
            if materialize:
                results.append(schedule.to_list())

        # Спускаемся на следующий уровень - аналог рекурсивного вызова
        stack.append(iter(range(idx + 1, len(vectors))))

def _explore_branch(top_idx: int):
    """Один воркер исследует одну ветку: первый вектор расписания
    зафиксирован как vectors[top_idx], дальше - обычный перебор с откатом."""
    vectors = _worker_state["vectors"]
    engine = _worker_state["engine"]
    max_pairs = _worker_state["max_pairs"]
    exact_size = _worker_state["exact_size"]
    materialize = _worker_state["materialize"]

    if engine is not None and hasattr(engine, "calls"):
        engine.calls = 0 
    
    schedule = Schedule(max_pairs=max_pairs)
    results: List[List[List[int]]] = []
    counter = [0] 

    candidate = vectors[top_idx]
    if engine is None or engine.can_add(schedule, candidate):
        schedule.add(candidate)
        _explore_recursive(
            vectors, engine, max_pairs, exact_size, top_idx + 1,
            schedule, materialize, results, counter,
        )
        schedule.pop()

    calls = engine.calls if engine is not None else 0
    return results, counter[0], calls


def enumerate_schedules_parallel(
    max_pairs: int = MAX_PAIRS_PER_WEEK,
    exact_size: bool = False,
    engine: Optional[ConstraintEngine] = None,
    workers: Optional[int] = None,
    materialize: bool = True,
):
    """
    Параллельная версия enumerate_schedules_backtracking() - использует
    несколько процессов (по умолчанию все ядра CPU, os.cpu_count()).

    Работа делится по ПЕРВОМУ вектору расписания: у каждого воркера
    зафиксирован свой кандидат на позицию 0, дальше он независимо
    выполняет тот же перебор с откатом. Поскольку ветки с разным первым
    вектором никак не пересекаются, результат идентичен последовательному
    перебору - просто выполняется параллельно на нескольких ядрах.

    workers      - количество процессов (по умолчанию os.cpu_count()).
    materialize  - если False, расписания не собираются в список (только
                   считаются) - экономит память на больших датасетах.

    Возвращает tuple (schedules, total_count, total_engine_calls):
      schedules         - список расписаний (List[List[int]] на каждое),
                           пустой список, если materialize=False.
      total_count       - сколько валидных расписаний найдено всего.
      total_engine_calls - суммарное количество вызовов can_add() по всем
                           воркерам (для сравнения со последовательным
                           вариантом).

    ВАЖНО: лимит (limit) здесь не поддерживается - параллельный режим
    предназначен для полного перебора большого датасета на всех ядрах,
    а не для быстрого превью (для превью используй
    enumerate_schedules_backtracking с limit=...).
    """
    if max_pairs > MAX_PAIRS_PER_WEEK:
        raise ValueError(f"max_pairs не может превышать {MAX_PAIRS_PER_WEEK}")

    vectors: List[Vec] = list(all_vectors())
    workers = workers or os.cpu_count() or 1

    all_results: List[List[List[int]]] = []
    total_count = 0
    total_calls = 0

    with cf.ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_worker,
        initargs=(vectors, engine, max_pairs, exact_size, materialize),
    ) as pool:
        for results, count, calls in pool.map(_explore_branch, range(len(vectors))):
            total_count += count
            total_calls += calls
            if materialize:
                all_results.extend(results)

    return all_results, total_count, total_calls
