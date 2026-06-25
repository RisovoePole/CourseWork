INSERT INTO groups(name, student_count) VALUES ('IA2403', 30);

INSERT INTO subjects (name) VALUES
('Databases'),
('Programming technologies'),
('Cryptography and information security'),
('Innovative entrepreneurship'),
('Physical Education')

INSERT INTO curriculum (
    group_id,
    subject_id,
    lecture_hours_per_week,
    seminar_hours_per_week,
    lab_hours_per_week
) VALUES

(1, 1, 30, 0, 46),  -- Databases
(1, 2, 30, 0, 30),  -- Programming technologies
(1, 3, 30, 0, 46),  -- Cryptography and information security
(1, 4, 30, 44, 0),  -- Innovative entrepreneurship
(1, 5, 30, 0, 0)    -- Physical Education