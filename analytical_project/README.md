# Tests

**recursive**:

``` bash
python_app  | ----ultra_easy-----
python_app  | run_parallel: 0.069 s
python_app  | run_backtracking: 0.002 s
python_app  | ----very_easy-----
python_app  | run_parallel: 1.050 s
python_app  | run_backtracking: 2.229 s
python_app  | ----medium-----
python_app  | run_parallel: 64.246 s
python_app  | run_backtracking: 162.009 s
python_app  | .
python_app  | ----------------------------------------------------------------------
python_app  | Ran 1 test in 229.635s
python_app  | 
python_app  | OK
```

**iterative**:

```bash
python_app  | ----ultra_easy-----
python_app  | run_parallel: 0.069 s
python_app  | run_backtracking: 0.002 s
python_app  | ----very_easy-----
python_app  | run_parallel: 1.013 s
python_app  | run_backtracking: 1.780 s
python_app  | ----medium-----
python_app  | run_parallel: 59.587 s
python_app  | run_backtracking: 130.856 s
python_app  | .
python_app  | ----------------------------------------------------------------------
python_app  | Ran 1 test in 193.337s
python_app  | 
python_app  | OK
```

``` python
def enumerate_schedules_backtracking(
    max_pairs: int = MAX_PAIRS_PER_WEEK,
    exact_size: bool = False,
    engine: Optional[ConstraintEngine] = None,
    limit: Optional[int] = None,
    materialize: bool = True,
) -> Iterator[Optional[Schedule]]:
    """
    Перебор "по разрядам" (как счётчик 0000, 0001, 0002, ...) с немедленной
    проверкой и откатом - именно так должен работать полный перебор
    валидных расписаний.

    Алгоритм:
      1. Берём очередной вектор-кандидат (по возрастанию индекса).
      2. Сразу пробуем добавить его в ТЕКУЩЕЕ расписание -
         engine.can_add(schedule, candidate).
      3. Если проверка НЕ прошла - никуда не углубляемся, просто берём
         следующий вектор-кандидат на этом же уровне ("следующий разряд").
      4. Если проверка прошла - добавляем вектор в расписание (оно стало
         валиднее на 1 пару) и рекурсивно пробуем расширить его дальше.
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
    state = {"yielded": 0}

    def limit_reached() -> bool:
        return limit is not None and state["yielded"] >= limit

    def recurse(start_idx: int) -> Iterator[Optional[Schedule]]:
        size = len(schedule)

        # текущее расписание валидно по построению - отдаём его,
        # если оно подходит по требуемому размеру
        if size > 0 and (not exact_size or size == max_pairs):
            yield schedule.copy() if materialize else None
            state["yielded"] += 1

        if limit_reached() or size >= max_pairs:
            return

        for idx in range(start_idx, len(vectors)):
            if limit_reached():
                return

            candidate = vectors[idx]

            if engine is not None and not engine.can_add(schedule, candidate):
                continue  # проверка не прошла - пробуем следующий вектор

            schedule.add(candidate)
            yield from recurse(idx + 1)
            schedule.pop()  # откат: возвращаемся к состоянию до candidate

    yield from recurse(0)

```

```python
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
    """Та же логика, что и в enumerate_schedules_backtracking(), но в виде
    обычной (не генераторной) функции - удобно дёргать из воркер-процесса."""
    size = len(schedule)
    if size > 0 and (not exact_size or size == max_pairs):
        counter[0] += 1
        if materialize:
            results.append(schedule.to_list())

    if size >= max_pairs:
        return

    for idx in range(start_idx, len(vectors)):
        candidate = vectors[idx]
        if engine is not None and not engine.can_add(schedule, candidate):
            continue
        schedule.add(candidate)
        _explore_recursive(
            vectors, engine, max_pairs, exact_size, idx + 1,
            schedule, materialize, results, counter,
        )
        schedule.pop()
```