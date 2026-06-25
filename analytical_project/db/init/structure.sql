-- ============================================
-- ВХОДНЫЕ ДАННЫЕ (общие для всех алгоритмов)
-- ============================================

CREATE TABLE groups (
    id            BIGSERIAL PRIMARY KEY,
    name          VARCHAR(50) NOT NULL,
    student_count INT NOT NULL
);

CREATE TABLE teachers (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE subjects (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE rooms (
    id       BIGSERIAL PRIMARY KEY,
    name     VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    type     VARCHAR(20) NOT NULL  -- LECTURE / LAB / SEMINAR
);

CREATE TABLE time_slots (
    id          BIGSERIAL PRIMARY KEY,
    day_of_week SMALLINT NOT NULL,  -- 1..6
    slot_number SMALLINT NOT NULL   -- номер пары за день
);

-- Это и есть "задача": что нужно расставить в расписание
CREATE TABLE lesson_requirements (
    id                 BIGSERIAL PRIMARY KEY,
    group_id           BIGINT NOT NULL REFERENCES groups(id),
    subject_id         BIGINT NOT NULL REFERENCES subjects(id),
    teacher_id         BIGINT NOT NULL REFERENCES teachers(id),
    lesson_type        VARCHAR(20) NOT NULL,  -- LECTURE / SEMINAR / LAB
    required_room_type VARCHAR(20) NOT NULL,
    lessons_per_week   INT NOT NULL
);

-- ============================================
-- РЕЗУЛЬТАТЫ ПРОГОНОВ (для сравнения алгоритмов)
-- ============================================

CREATE TABLE algorithm_runs (
    id                 BIGSERIAL PRIMARY KEY,
    algorithm_name     VARCHAR(50) NOT NULL,   -- 'GENETIC', 'GREEDY', 'SIMULATED_ANNEALING'...
    parameters         JSONB,                  -- гиперпараметры конкретного запуска
    started_at         TIMESTAMP NOT NULL DEFAULT now(),
    execution_time_ms  BIGINT,
    hard_violations    INT,
    soft_violations    INT,
    fitness_score      DOUBLE PRECISION,
    extra_metrics      JSONB                   -- всё, что не влезает в стандартные колонки
);

CREATE TABLE scheduled_lessons (
    id                     BIGSERIAL PRIMARY KEY,
    run_id                 BIGINT NOT NULL REFERENCES algorithm_runs(id) ON DELETE CASCADE,
    lesson_requirement_id  BIGINT NOT NULL REFERENCES lesson_requirements(id),
    time_slot_id           BIGINT NOT NULL REFERENCES time_slots(id),
    room_id                BIGINT NOT NULL REFERENCES rooms(id)
);

CREATE INDEX idx_scheduled_lessons_run ON scheduled_lessons(run_id);

CREATE TABLE curriculum (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES groups(id),
    subject_id BIGINT NOT NULL REFERENCES subjects(id),

    lecture_hours_per_week INT NOT NULL DEFAULT 0,
    seminar_hours_per_week INT NOT NULL DEFAULT 0,
    lab_hours_per_week INT NOT NULL DEFAULT 0
);