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
    name VARCHAR(100) NOT NULL,
    optimal_room_type BIGINT[]
);

CREATE TABLE room_type(
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE rooms (
    id       BIGSERIAL PRIMARY KEY,
    name     VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    type     BIGINT NOT NULL  REFERENCES room_type(id) 
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


INSERT INTO groups(name, student_count) VALUES ('IA2403', 30);

INSERT INTO subjects (name) VALUES
('Databases'),
('Programming technologies'),
('Cryptography and information security'),
('Innovative entrepreneurship'),
('Physical Education');

INSERT INTO teachers (name) VALUES
('Ivan Popescu'),
('Maria Rusu'),
('Andrei Ceban'),
('Elena Munteanu'),
('Sergiu Moraru');

INSERT INTO rooms (name, capacity, type) VALUES
('A101', 100, 'LECTURE'),
('A102', 40,  'SEMINAR'),
('L201', 30,  'LAB'),
('L202', 30,  'LAB'),
('Gym', 50,   'SEMINAR');

INSERT INTO time_slots(day_of_week, slot_number) VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),
(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),
(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),
(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),
(5,1),(5,2),(5,3),(5,4),(5,5),(5,6),
(6,1),(6,2),(6,3),(6,4),(6,5),(6,6);

INSERT INTO lesson_requirements (
    group_id,
    subject_id,
    teacher_id,
    lesson_type,
    required_room_type,
    lessons_per_week
) VALUES

-- Databases
(1, 1, 1, 'LECTURE', 'LECTURE', 2),
(1, 1, 1, 'LAB',      'LAB',     3),

-- Programming technologies
(1, 2, 2, 'LECTURE', 'LECTURE', 2),
(1, 2, 2, 'LAB',     'LAB',     2),

-- Cryptography and information security
(1, 3, 3, 'LECTURE', 'LECTURE', 2),
(1, 3, 3, 'LAB',     'LAB',     3),

-- Innovative entrepreneurship
(1, 4, 4, 'LECTURE', 'LECTURE', 2),
(1, 4, 4, 'SEMINAR', 'SEMINAR', 2),

-- Physical Education
(1, 5, 5, 'LECTURE', 'LECTURE', 1),
(1, 5, 5, 'SEMINAR', 'SEMINAR', 1);