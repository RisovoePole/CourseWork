--
-- PostgreSQL database dump
--

\restrict UlHMZZfddfSNtAj4LP0lZeIqxucKHz5LlQD3rD8uUWJ9o46bOj2UctSyPLfNNfB

-- Dumped from database version 15.17
-- Dumped by pg_dump version 15.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audience; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audience (
    audience_id integer NOT NULL,
    room_name character varying(10),
    university_building integer NOT NULL,
    amount_of_seats integer NOT NULL
);


--
-- Name: audience_audience_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audience_audience_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audience_audience_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audience_audience_id_seq OWNED BY public.audience.audience_id;


--
-- Name: audience_roomtype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audience_roomtype (
    room_type_id integer NOT NULL,
    audience_id integer NOT NULL
);


--
-- Name: discipline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discipline (
    discipline_id integer NOT NULL,
    discipline_name character varying(40) NOT NULL,
    study_semester integer NOT NULL,
    required_room_type integer,
    credits double precision,
    spec_id integer NOT NULL
);


--
-- Name: discipline_discipline_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.discipline_discipline_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: discipline_discipline_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.discipline_discipline_id_seq OWNED BY public.discipline.discipline_id;


--
-- Name: faculty; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faculty (
    faculty_id integer NOT NULL,
    faculty_name character varying NOT NULL
);


--
-- Name: faculty_faculty_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.faculty_faculty_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: faculty_faculty_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.faculty_faculty_id_seq OWNED BY public.faculty.faculty_id;


--
-- Name: group_elder_student; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.group_elder_student (
    students_group_id integer NOT NULL,
    student_id integer NOT NULL
);


--
-- Name: pairtimeborders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pairtimeborders (
    pair_number integer NOT NULL,
    pair_start time without time zone NOT NULL,
    pair_end time without time zone NOT NULL
);


--
-- Name: pairtimeborders_pair_number_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pairtimeborders_pair_number_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pairtimeborders_pair_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pairtimeborders_pair_number_seq OWNED BY public.pairtimeborders.pair_number;


--
-- Name: professor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.professor (
    professor_id integer NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    email character varying NOT NULL,
    phone_number character varying NOT NULL
);


--
-- Name: professor_discipline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.professor_discipline (
    professor_id integer NOT NULL,
    discipline_id integer NOT NULL
);


--
-- Name: professor_professor_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.professor_professor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: professor_professor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.professor_professor_id_seq OWNED BY public.professor.professor_id;


--
-- Name: roomtype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roomtype (
    room_type_id integer NOT NULL,
    room_type_name character varying NOT NULL
);


--
-- Name: roomtype_room_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roomtype_room_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roomtype_room_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roomtype_room_type_id_seq OWNED BY public.roomtype.room_type_id;


--
-- Name: schedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule (
    schedule_generation_id integer NOT NULL,
    students_group_id integer,
    audience_id integer,
    discipline_id integer,
    professor_id integer,
    week_pattern integer NOT NULL,
    time_slot_id integer NOT NULL
);


--
-- Name: schedule_generation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule_generation (
    schedule_generation_id integer NOT NULL,
    created_at time without time zone
);


--
-- Name: schedule_generation_schedule_generation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schedule_generation_schedule_generation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schedule_generation_schedule_generation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schedule_generation_schedule_generation_id_seq OWNED BY public.schedule_generation.schedule_generation_id;


--
-- Name: specialization; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.specialization (
    spec_id integer NOT NULL,
    spec_name character varying NOT NULL,
    faculty_id integer NOT NULL,
    years_of_study integer NOT NULL
);


--
-- Name: specialization_spec_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.specialization_spec_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: specialization_spec_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.specialization_spec_id_seq OWNED BY public.specialization.spec_id;


--
-- Name: student; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student (
    student_id integer NOT NULL,
    students_group_id integer,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    email character varying
);


--
-- Name: student_student_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_student_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_student_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_student_id_seq OWNED BY public.student.student_id;


--
-- Name: students_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.students_group (
    students_group_id integer NOT NULL,
    group_name character varying(10) NOT NULL,
    professor_inspector integer,
    spec_id integer NOT NULL
);


--
-- Name: students_group_students_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.students_group_students_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: students_group_students_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.students_group_students_group_id_seq OWNED BY public.students_group.students_group_id;


--
-- Name: study_hours; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_hours (
    discipline_id integer NOT NULL,
    contact_study_hours double precision,
    independent_study_hours double precision,
    course_hours double precision,
    seminar_hours double precision,
    laboratories_hours double precision
);


--
-- Name: timeslot; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timeslot (
    time_slot_id integer NOT NULL,
    day_of_week integer NOT NULL,
    pair_number integer
);


--
-- Name: timeslot_time_slot_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.timeslot_time_slot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: timeslot_time_slot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.timeslot_time_slot_id_seq OWNED BY public.timeslot.time_slot_id;


--
-- Name: audience audience_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience ALTER COLUMN audience_id SET DEFAULT nextval('public.audience_audience_id_seq'::regclass);


--
-- Name: discipline discipline_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discipline ALTER COLUMN discipline_id SET DEFAULT nextval('public.discipline_discipline_id_seq'::regclass);


--
-- Name: faculty faculty_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty ALTER COLUMN faculty_id SET DEFAULT nextval('public.faculty_faculty_id_seq'::regclass);


--
-- Name: pairtimeborders pair_number; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairtimeborders ALTER COLUMN pair_number SET DEFAULT nextval('public.pairtimeborders_pair_number_seq'::regclass);


--
-- Name: professor professor_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professor ALTER COLUMN professor_id SET DEFAULT nextval('public.professor_professor_id_seq'::regclass);


--
-- Name: roomtype room_type_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roomtype ALTER COLUMN room_type_id SET DEFAULT nextval('public.roomtype_room_type_id_seq'::regclass);


--
-- Name: schedule_generation schedule_generation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_generation ALTER COLUMN schedule_generation_id SET DEFAULT nextval('public.schedule_generation_schedule_generation_id_seq'::regclass);


--
-- Name: specialization spec_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialization ALTER COLUMN spec_id SET DEFAULT nextval('public.specialization_spec_id_seq'::regclass);


--
-- Name: student student_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student ALTER COLUMN student_id SET DEFAULT nextval('public.student_student_id_seq'::regclass);


--
-- Name: students_group students_group_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students_group ALTER COLUMN students_group_id SET DEFAULT nextval('public.students_group_students_group_id_seq'::regclass);


--
-- Name: timeslot time_slot_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timeslot ALTER COLUMN time_slot_id SET DEFAULT nextval('public.timeslot_time_slot_id_seq'::regclass);


--
-- Name: audience audience_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience
    ADD CONSTRAINT audience_pkey PRIMARY KEY (audience_id);


--
-- Name: audience audience_room_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience
    ADD CONSTRAINT audience_room_name_key UNIQUE (room_name);


--
-- Name: audience_roomtype audience_roomtype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_roomtype
    ADD CONSTRAINT audience_roomtype_pkey PRIMARY KEY (room_type_id, audience_id);


--
-- Name: discipline discipline_discipline_name_study_semester_spec_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discipline
    ADD CONSTRAINT discipline_discipline_name_study_semester_spec_id_key UNIQUE (discipline_name, study_semester, spec_id);


--
-- Name: discipline discipline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discipline
    ADD CONSTRAINT discipline_pkey PRIMARY KEY (discipline_id);


--
-- Name: faculty faculty_faculty_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty
    ADD CONSTRAINT faculty_faculty_name_key UNIQUE (faculty_name);


--
-- Name: faculty faculty_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty
    ADD CONSTRAINT faculty_pkey PRIMARY KEY (faculty_id);


--
-- Name: group_elder_student group_elder_student_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.group_elder_student
    ADD CONSTRAINT group_elder_student_pkey PRIMARY KEY (students_group_id, student_id);


--
-- Name: pairtimeborders pairtimeborders_pair_start_pair_end_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairtimeborders
    ADD CONSTRAINT pairtimeborders_pair_start_pair_end_key UNIQUE (pair_start, pair_end);


--
-- Name: pairtimeborders pairtimeborders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pairtimeborders
    ADD CONSTRAINT pairtimeborders_pkey PRIMARY KEY (pair_number);


--
-- Name: professor_discipline professor_discipline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professor_discipline
    ADD CONSTRAINT professor_discipline_pkey PRIMARY KEY (professor_id, discipline_id);


--
-- Name: professor professor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professor
    ADD CONSTRAINT professor_pkey PRIMARY KEY (professor_id);


--
-- Name: roomtype roomtype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roomtype
    ADD CONSTRAINT roomtype_pkey PRIMARY KEY (room_type_id);


--
-- Name: schedule_generation schedule_generation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_generation
    ADD CONSTRAINT schedule_generation_pkey PRIMARY KEY (schedule_generation_id);


--
-- Name: schedule schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_pkey PRIMARY KEY (schedule_generation_id, week_pattern, time_slot_id);


--
-- Name: schedule schedule_schedule_generation_id_week_pattern_time_slot_id_d_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_schedule_generation_id_week_pattern_time_slot_id_d_key UNIQUE (schedule_generation_id, week_pattern, time_slot_id, discipline_id);


--
-- Name: schedule schedule_schedule_generation_id_week_pattern_time_slot_id_p_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_schedule_generation_id_week_pattern_time_slot_id_p_key UNIQUE (schedule_generation_id, week_pattern, time_slot_id, professor_id);


--
-- Name: schedule schedule_schedule_generation_id_week_pattern_time_slot_id_s_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_schedule_generation_id_week_pattern_time_slot_id_s_key UNIQUE (schedule_generation_id, week_pattern, time_slot_id, students_group_id);


--
-- Name: specialization specialization_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialization
    ADD CONSTRAINT specialization_pkey PRIMARY KEY (spec_id);


--
-- Name: student student_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_pkey PRIMARY KEY (student_id);


--
-- Name: students_group students_group_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students_group
    ADD CONSTRAINT students_group_group_name_key UNIQUE (group_name);


--
-- Name: students_group students_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students_group
    ADD CONSTRAINT students_group_pkey PRIMARY KEY (students_group_id);


--
-- Name: study_hours study_hours_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_hours
    ADD CONSTRAINT study_hours_pkey PRIMARY KEY (discipline_id);


--
-- Name: timeslot timeslot_day_of_week_pair_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timeslot
    ADD CONSTRAINT timeslot_day_of_week_pair_number_key UNIQUE (day_of_week, pair_number);


--
-- Name: timeslot timeslot_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timeslot
    ADD CONSTRAINT timeslot_pkey PRIMARY KEY (time_slot_id);


--
-- Name: audience_roomtype audience_roomtype_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_roomtype
    ADD CONSTRAINT audience_roomtype_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.audience(audience_id);


--
-- Name: audience_roomtype audience_roomtype_room_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audience_roomtype
    ADD CONSTRAINT audience_roomtype_room_type_id_fkey FOREIGN KEY (room_type_id) REFERENCES public.roomtype(room_type_id);


--
-- Name: discipline discipline_required_room_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discipline
    ADD CONSTRAINT discipline_required_room_type_fkey FOREIGN KEY (required_room_type) REFERENCES public.roomtype(room_type_id);


--
-- Name: discipline discipline_spec_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discipline
    ADD CONSTRAINT discipline_spec_id_fkey FOREIGN KEY (spec_id) REFERENCES public.specialization(spec_id);


--
-- Name: group_elder_student group_elder_student_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.group_elder_student
    ADD CONSTRAINT group_elder_student_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.student(student_id);


--
-- Name: group_elder_student group_elder_student_students_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.group_elder_student
    ADD CONSTRAINT group_elder_student_students_group_id_fkey FOREIGN KEY (students_group_id) REFERENCES public.students_group(students_group_id);


--
-- Name: professor_discipline professor_discipline_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professor_discipline
    ADD CONSTRAINT professor_discipline_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.discipline(discipline_id);


--
-- Name: professor_discipline professor_discipline_professor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.professor_discipline
    ADD CONSTRAINT professor_discipline_professor_id_fkey FOREIGN KEY (professor_id) REFERENCES public.professor(professor_id);


--
-- Name: schedule schedule_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.audience(audience_id);


--
-- Name: schedule schedule_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.discipline(discipline_id);


--
-- Name: schedule schedule_professor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_professor_id_fkey FOREIGN KEY (professor_id) REFERENCES public.professor(professor_id);


--
-- Name: schedule schedule_schedule_generation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_schedule_generation_id_fkey FOREIGN KEY (schedule_generation_id) REFERENCES public.schedule_generation(schedule_generation_id);


--
-- Name: schedule schedule_students_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_students_group_id_fkey FOREIGN KEY (students_group_id) REFERENCES public.students_group(students_group_id);


--
-- Name: schedule schedule_time_slot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_time_slot_id_fkey FOREIGN KEY (time_slot_id) REFERENCES public.timeslot(time_slot_id);


--
-- Name: specialization specialization_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialization
    ADD CONSTRAINT specialization_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES public.faculty(faculty_id);


--
-- Name: student student_students_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student
    ADD CONSTRAINT student_students_group_id_fkey FOREIGN KEY (students_group_id) REFERENCES public.students_group(students_group_id);


--
-- Name: students_group students_group_professor_inspector_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students_group
    ADD CONSTRAINT students_group_professor_inspector_fkey FOREIGN KEY (professor_inspector) REFERENCES public.professor(professor_id);


--
-- Name: students_group students_group_spec_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students_group
    ADD CONSTRAINT students_group_spec_id_fkey FOREIGN KEY (spec_id) REFERENCES public.specialization(spec_id);


--
-- Name: study_hours study_hours_discipline_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_hours
    ADD CONSTRAINT study_hours_discipline_id_fkey FOREIGN KEY (discipline_id) REFERENCES public.discipline(discipline_id);


--
-- Name: timeslot timeslot_pair_number_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timeslot
    ADD CONSTRAINT timeslot_pair_number_fkey FOREIGN KEY (pair_number) REFERENCES public.pairtimeborders(pair_number);


--
-- PostgreSQL database dump complete
--

\unrestrict UlHMZZfddfSNtAj4LP0lZeIqxucKHz5LlQD3rD8uUWJ9o46bOj2UctSyPLfNNfB

