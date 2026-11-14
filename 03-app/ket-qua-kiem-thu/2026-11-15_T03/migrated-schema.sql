--
-- PostgreSQL database dump
--

\restrict hOuC6hlnKeNp7ER3LWMySHB2uEQa1m9aicbeoFW7OcsfE3MwzgGO1m0CH3sj3l0

-- Dumped from database version 16.16
-- Dumped by pg_dump version 16.16

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

--
-- Name: btree_gist; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION btree_gist; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';


--
-- Name: event_handling_check(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.event_handling_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE r text;
BEGIN
  SELECT result INTO r FROM recognition_event WHERE id = NEW.event_id;
  IF r NOT IN ('UNKNOWN','SPOOF') THEN
    RAISE EXCEPTION 'event_handling chỉ áp dụng cho UNKNOWN/SPOOF (nhận %)', r;
  END IF;
  RETURN NEW;
END $$;


--
-- Name: recognition_event_guard(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.recognition_event_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'recognition_event là dữ liệu chỉ thêm: không được DELETE';
  END IF;
  IF NEW.snapshot_path IS NOT NULL AND NEW.snapshot_path IS DISTINCT FROM OLD.snapshot_path THEN
    RAISE EXCEPTION 'recognition_event: snapshot_path chỉ được đặt về NULL';
  END IF;
  IF (to_jsonb(NEW) - 'snapshot_path') IS DISTINCT FROM (to_jsonb(OLD) - 'snapshot_path') THEN
    RAISE EXCEPTION 'recognition_event là dữ liệu chỉ thêm: chỉ được xoá snapshot_path';
  END IF;
  RETURN NEW;
END $$;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attendance_day; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendance_day (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    work_date date NOT NULL,
    shift_id uuid,
    check_in_at timestamp with time zone,
    check_out_at timestamp with time zone,
    check_in_event_id uuid,
    check_out_event_id uuid,
    status text NOT NULL,
    suspect_forgot_out boolean DEFAULT false NOT NULL,
    late_min smallint DEFAULT 0 NOT NULL,
    early_min smallint DEFAULT 0 NOT NULL,
    worked_min smallint DEFAULT 0 NOT NULL,
    source text DEFAULT 'AUTO'::text NOT NULL,
    finalized boolean DEFAULT false NOT NULL,
    edited_by_user_id uuid,
    edit_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT attendance_day_check CHECK (((check_out_at IS NULL) OR ((check_in_at IS NOT NULL) AND (check_out_at >= check_in_at)))),
    CONSTRAINT attendance_day_check1 CHECK (((source <> 'MANUAL'::text) OR ((edited_by_user_id IS NOT NULL) AND (edit_reason IS NOT NULL)))),
    CONSTRAINT attendance_day_check2 CHECK (((NOT suspect_forgot_out) OR (status = 'MISSING_OUT'::text))),
    CONSTRAINT attendance_day_check3 CHECK (((status <> ALL (ARRAY['NORMAL'::text, 'LATE'::text, 'EARLY'::text, 'LATE_EARLY'::text])) OR (check_out_at IS NOT NULL))),
    CONSTRAINT attendance_day_check4 CHECK (((status <> ALL (ARRAY['IN_PROGRESS'::text, 'MISSING_OUT'::text])) OR (check_in_at IS NOT NULL))),
    CONSTRAINT attendance_day_check5 CHECK (((status <> 'WAITING_IN'::text) OR ((check_in_at IS NULL) AND (NOT finalized)))),
    CONSTRAINT attendance_day_early_min_check CHECK ((early_min >= 0)),
    CONSTRAINT attendance_day_late_min_check CHECK ((late_min >= 0)),
    CONSTRAINT attendance_day_source_check CHECK ((source = ANY (ARRAY['AUTO'::text, 'ADJUSTED'::text, 'MANUAL'::text]))),
    CONSTRAINT attendance_day_status_check CHECK ((status = ANY (ARRAY['HOLIDAY'::text, 'LEAVE'::text, 'OFF'::text, 'NOT_STARTED'::text, 'WAITING_IN'::text, 'IN_PROGRESS'::text, 'ABSENT'::text, 'MISSING_OUT'::text, 'NORMAL'::text, 'LATE'::text, 'EARLY'::text, 'LATE_EARLY'::text]))),
    CONSTRAINT attendance_day_worked_min_check CHECK ((worked_min >= 0))
);


--
-- Name: attendance_request; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendance_request (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    requested_by_user_id uuid NOT NULL,
    work_date date NOT NULL,
    type text NOT NULL,
    requested_in timestamp with time zone,
    requested_out timestamp with time zone,
    reason text NOT NULL,
    status text DEFAULT 'PENDING'::text NOT NULL,
    reviewer_user_id uuid,
    reviewed_at timestamp with time zone,
    review_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT attendance_request_check CHECK (((status = ANY (ARRAY['APPROVED'::text, 'REJECTED'::text])) = ((reviewer_user_id IS NOT NULL) AND (reviewed_at IS NOT NULL)))),
    CONSTRAINT attendance_request_check1 CHECK (((reviewer_user_id IS NULL) OR (reviewer_user_id <> requested_by_user_id))),
    CONSTRAINT attendance_request_check2 CHECK (((type <> 'FORGOT_IN'::text) OR (requested_in IS NOT NULL))),
    CONSTRAINT attendance_request_check3 CHECK (((type <> 'FORGOT_OUT'::text) OR (requested_out IS NOT NULL))),
    CONSTRAINT attendance_request_check4 CHECK (((requested_in IS NULL) OR (requested_out IS NULL) OR (requested_out > requested_in))),
    CONSTRAINT attendance_request_reason_check CHECK ((length(TRIM(BOTH FROM reason)) > 0)),
    CONSTRAINT attendance_request_status_check CHECK ((status = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'CANCELLED'::text]))),
    CONSTRAINT attendance_request_type_check CHECK ((type = ANY (ARRAY['FORGOT_IN'::text, 'FORGOT_OUT'::text, 'NOT_RECOGNIZED'::text, 'BUSINESS_TRIP'::text, 'OTHER'::text])))
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id bigint NOT NULL,
    company_id uuid,
    actor_user_id uuid,
    actor_device_id uuid,
    action text NOT NULL,
    entity text NOT NULL,
    entity_id text,
    detail jsonb,
    at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: auth_refresh_token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_refresh_token (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: company; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    timezone text DEFAULT 'Asia/Ho_Chi_Minh'::text NOT NULL,
    settings jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: department; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.department (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.device (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    gate_id uuid NOT NULL,
    name text NOT NULL,
    status text DEFAULT 'PENDING'::text NOT NULL,
    pairing_code_hash text,
    pairing_expires_at timestamp with time zone,
    pairing_attempts smallint DEFAULT 0 NOT NULL,
    token_hash text,
    token_expires_at timestamp with time zone,
    last_seen_at timestamp with time zone,
    app_version text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT device_check CHECK (((status <> 'ACTIVE'::text) OR (token_hash IS NOT NULL))),
    CONSTRAINT device_status_check CHECK ((status = ANY (ARRAY['PENDING'::text, 'ACTIVE'::text, 'REVOKED'::text])))
);


--
-- Name: employee; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    department_id uuid NOT NULL,
    code text NOT NULL,
    full_name text NOT NULL,
    email text,
    phone text,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    attendance_method text DEFAULT 'FACE'::text NOT NULL,
    joined_at date,
    terminated_at timestamp with time zone,
    face_consent_at timestamp with time zone,
    face_consent_by uuid,
    biometric_deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT employee_attendance_method_check CHECK ((attendance_method = ANY (ARRAY['FACE'::text, 'MANUAL'::text]))),
    CONSTRAINT employee_check CHECK (((status <> 'TERMINATED'::text) OR (terminated_at IS NOT NULL))),
    CONSTRAINT employee_check1 CHECK (((face_consent_at IS NULL) = (face_consent_by IS NULL))),
    CONSTRAINT employee_status_check CHECK ((status = ANY (ARRAY['ACTIVE'::text, 'SUSPENDED'::text, 'TERMINATED'::text])))
);


--
-- Name: event_handling; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_handling (
    event_id uuid NOT NULL,
    status text NOT NULL,
    linked_employee_id uuid,
    handled_by_user_id uuid NOT NULL,
    handled_at timestamp with time zone DEFAULT now() NOT NULL,
    note text,
    CONSTRAINT event_handling_check CHECK (((status = 'IS_EMPLOYEE'::text) = (linked_employee_id IS NOT NULL))),
    CONSTRAINT event_handling_status_check CHECK ((status = ANY (ARRAY['RESOLVED'::text, 'FALSE_ALARM'::text, 'IS_EMPLOYEE'::text])))
);


--
-- Name: face_embedding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_embedding (
    sample_id uuid NOT NULL,
    model_id uuid NOT NULL,
    vector real[] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT face_embedding_vector_check CHECK (((array_ndims(vector) = 1) AND (array_length(vector, 1) = 512)))
);


--
-- Name: face_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_profile (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    employee_id uuid NOT NULL,
    status text DEFAULT 'PENDING_REVIEW'::text NOT NULL,
    enrolled_by_user_id uuid NOT NULL,
    enrolled_device_id uuid,
    duplicate_of_employee_id uuid,
    duplicate_score real,
    reviewed_by_user_id uuid,
    reviewed_at timestamp with time zone,
    review_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT face_profile_check CHECK (((status = ANY (ARRAY['ACTIVE'::text, 'REJECTED'::text])) <= ((reviewed_by_user_id IS NOT NULL) AND (reviewed_at IS NOT NULL)))),
    CONSTRAINT face_profile_check1 CHECK (((duplicate_of_employee_id IS NULL) = (duplicate_score IS NULL))),
    CONSTRAINT face_profile_check2 CHECK (((duplicate_of_employee_id IS NULL) OR (duplicate_of_employee_id <> employee_id))),
    CONSTRAINT face_profile_status_check CHECK ((status = ANY (ARRAY['PENDING_REVIEW'::text, 'ACTIVE'::text, 'REJECTED'::text, 'SUPERSEDED'::text])))
);


--
-- Name: face_sample; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_sample (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    profile_id uuid NOT NULL,
    image_path text NOT NULL,
    det_score real NOT NULL,
    yaw_ratio real NOT NULL,
    p_live real,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: face_template; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.face_template (
    profile_id uuid NOT NULL,
    model_id uuid NOT NULL,
    vector real[] NOT NULL,
    n_samples smallint NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT face_template_n_samples_check CHECK ((n_samples > 0)),
    CONSTRAINT face_template_vector_check CHECK (((array_ndims(vector) = 1) AND (array_length(vector, 1) = 512)))
);


--
-- Name: gate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gate (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    name text NOT NULL,
    mode text NOT NULL,
    default_policy text NOT NULL,
    threshold_level text NOT NULL,
    custom_threshold real,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT gate_check CHECK (((threshold_level = 'CUSTOM'::text) = (custom_threshold IS NOT NULL))),
    CONSTRAINT gate_custom_threshold_check CHECK (((custom_threshold >= ('-1'::integer)::double precision) AND (custom_threshold <= (1)::double precision))),
    CONSTRAINT gate_default_policy_check CHECK ((default_policy = ANY (ARRAY['ALLOW_ALL_ACTIVE'::text, 'DEPARTMENTS_ONLY'::text]))),
    CONSTRAINT gate_mode_check CHECK ((mode = ANY (ARRAY['ATTENDANCE_ACCESS'::text, 'ACCESS_ONLY'::text]))),
    CONSTRAINT gate_threshold_level_check CHECK ((threshold_level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text, 'CUSTOM'::text])))
);


--
-- Name: gate_allowed_department; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gate_allowed_department (
    gate_id uuid NOT NULL,
    department_id uuid NOT NULL
);


--
-- Name: holiday; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.holiday (
    company_id uuid NOT NULL,
    date date NOT NULL,
    name text NOT NULL
);


--
-- Name: recognition_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recognition_event (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    gate_id uuid NOT NULL,
    device_id uuid,
    occurred_at timestamp with time zone NOT NULL,
    result text NOT NULL,
    employee_id uuid,
    model_id uuid,
    top1_score real,
    threshold_used real,
    threshold_level text,
    p_live_min real,
    n_frames smallint,
    door_action text DEFAULT 'NONE'::text NOT NULL,
    snapshot_path text,
    performed_by_user_id uuid,
    reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT recognition_event_check CHECK (((result <> ALL (ARRAY['MATCH'::text, 'UNKNOWN'::text, 'SPOOF'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text])) OR ((model_id IS NOT NULL) AND (device_id IS NOT NULL) AND (n_frames IS NOT NULL)))),
    CONSTRAINT recognition_event_check1 CHECK (((result <> ALL (ARRAY['MATCH'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text])) OR ((employee_id IS NOT NULL) AND (top1_score IS NOT NULL) AND (threshold_used IS NOT NULL)))),
    CONSTRAINT recognition_event_check2 CHECK (((result <> ALL (ARRAY['UNKNOWN'::text, 'SPOOF'::text])) OR (employee_id IS NULL))),
    CONSTRAINT recognition_event_check3 CHECK (((result <> ALL (ARRAY['MATCH'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text, 'MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text])) OR (snapshot_path IS NULL))),
    CONSTRAINT recognition_event_check4 CHECK (((result <> ALL (ARRAY['MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text])) OR ((performed_by_user_id IS NOT NULL) AND (reason IS NOT NULL) AND (length(TRIM(BOTH FROM reason)) > 0)))),
    CONSTRAINT recognition_event_check5 CHECK (((result <> 'MANUAL_ATTENDANCE'::text) OR (employee_id IS NOT NULL))),
    CONSTRAINT recognition_event_check6 CHECK (((door_action = 'OPEN'::text) = (result = ANY (ARRAY['MATCH'::text, 'MANUAL_OPEN'::text])))),
    CONSTRAINT recognition_event_door_action_check CHECK ((door_action = ANY (ARRAY['OPEN'::text, 'NONE'::text]))),
    CONSTRAINT recognition_event_result_check CHECK ((result = ANY (ARRAY['MATCH'::text, 'UNKNOWN'::text, 'SPOOF'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text, 'MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text]))),
    CONSTRAINT recognition_event_threshold_level_check CHECK ((threshold_level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text, 'CUSTOM'::text])))
);


--
-- Name: recognition_model; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recognition_model (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    backbone text NOT NULL,
    manifest_id text NOT NULL,
    source_path text NOT NULL,
    source_sha256 character(64) NOT NULL,
    stripped_sha256 character(64) NOT NULL,
    epoch smallint NOT NULL,
    t_bs real NOT NULL,
    alignment_version text NOT NULL,
    runtime jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: shift; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    name text NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    break_start time without time zone,
    break_end time without time zone,
    grace_in_min smallint DEFAULT 5 NOT NULL,
    grace_out_min smallint DEFAULT 5 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT shift_check CHECK ((end_time > start_time)),
    CONSTRAINT shift_check1 CHECK (((end_time - start_time) <= '17:00:00'::interval)),
    CONSTRAINT shift_check2 CHECK (((break_start IS NULL) = (break_end IS NULL))),
    CONSTRAINT shift_check3 CHECK (((break_start IS NULL) OR ((break_start >= start_time) AND (break_end <= end_time) AND (break_end > break_start)))),
    CONSTRAINT shift_grace_in_min_check CHECK (((grace_in_min >= 0) AND (grace_in_min <= 120))),
    CONSTRAINT shift_grace_out_min_check CHECK (((grace_out_min >= 0) AND (grace_out_min <= 120)))
);


--
-- Name: shift_assignment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shift_assignment (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    shift_id uuid NOT NULL,
    employee_id uuid,
    department_id uuid,
    weekday smallint NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    effective daterange GENERATED ALWAYS AS (daterange(effective_from, effective_to, '[]'::text)) STORED,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT shift_assignment_check CHECK (((employee_id IS NULL) <> (department_id IS NULL))),
    CONSTRAINT shift_assignment_check1 CHECK (((effective_to IS NULL) OR (effective_to >= effective_from))),
    CONSTRAINT shift_assignment_weekday_check CHECK (((weekday >= 1) AND (weekday <= 7)))
);


--
-- Name: threshold_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.threshold_profile (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    model_id uuid NOT NULL,
    level text NOT NULL,
    cos_threshold real NOT NULL,
    label text NOT NULL,
    source_ref text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT threshold_profile_cos_threshold_check CHECK (((cos_threshold >= ('-1'::integer)::double precision) AND (cos_threshold <= (1)::double precision))),
    CONSTRAINT threshold_profile_level_check CHECK ((level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text])))
);


--
-- Name: user_account; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_account (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    company_id uuid NOT NULL,
    email text NOT NULL,
    password_hash text NOT NULL,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    employee_id uuid,
    must_change_password boolean DEFAULT true NOT NULL,
    kiosk_pin_hash text,
    pin_failed_count smallint DEFAULT 0 NOT NULL,
    pin_locked_until timestamp with time zone,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_account_status_check CHECK ((status = ANY (ARRAY['ACTIVE'::text, 'DISABLED'::text])))
);


--
-- Name: user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_role (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    role text NOT NULL,
    scope_department_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_role_check CHECK (((role = 'MANAGER'::text) = (scope_department_id IS NOT NULL))),
    CONSTRAINT user_role_role_check CHECK ((role = ANY (ARRAY['OWNER'::text, 'HR'::text, 'MANAGER'::text, 'SECURITY'::text, 'EMPLOYEE'::text])))
);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: attendance_day attendance_day_employee_id_work_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_employee_id_work_date_key UNIQUE (employee_id, work_date);


--
-- Name: attendance_day attendance_day_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_pkey PRIMARY KEY (id);


--
-- Name: attendance_request attendance_request_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_request
    ADD CONSTRAINT attendance_request_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: auth_refresh_token auth_refresh_token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_refresh_token
    ADD CONSTRAINT auth_refresh_token_pkey PRIMARY KEY (id);


--
-- Name: auth_refresh_token auth_refresh_token_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_refresh_token
    ADD CONSTRAINT auth_refresh_token_token_hash_key UNIQUE (token_hash);


--
-- Name: company company_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company
    ADD CONSTRAINT company_pkey PRIMARY KEY (id);


--
-- Name: department department_company_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_company_id_name_key UNIQUE (company_id, name);


--
-- Name: department department_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_pkey PRIMARY KEY (id);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (id);


--
-- Name: device device_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_token_hash_key UNIQUE (token_hash);


--
-- Name: employee employee_company_id_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_company_id_code_key UNIQUE (company_id, code);


--
-- Name: employee employee_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_pkey PRIMARY KEY (id);


--
-- Name: event_handling event_handling_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_handling
    ADD CONSTRAINT event_handling_pkey PRIMARY KEY (event_id);


--
-- Name: shift_assignment ex_assign_department; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT ex_assign_department EXCLUDE USING gist (department_id WITH =, weekday WITH =, effective WITH &&) WHERE ((department_id IS NOT NULL));


--
-- Name: shift_assignment ex_assign_employee; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT ex_assign_employee EXCLUDE USING gist (employee_id WITH =, weekday WITH =, effective WITH &&) WHERE ((employee_id IS NOT NULL));


--
-- Name: face_embedding face_embedding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_embedding
    ADD CONSTRAINT face_embedding_pkey PRIMARY KEY (sample_id, model_id);


--
-- Name: face_profile face_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_pkey PRIMARY KEY (id);


--
-- Name: face_sample face_sample_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_sample
    ADD CONSTRAINT face_sample_pkey PRIMARY KEY (id);


--
-- Name: face_template face_template_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_template
    ADD CONSTRAINT face_template_pkey PRIMARY KEY (profile_id, model_id);


--
-- Name: gate_allowed_department gate_allowed_department_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate_allowed_department
    ADD CONSTRAINT gate_allowed_department_pkey PRIMARY KEY (gate_id, department_id);


--
-- Name: gate gate_company_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate
    ADD CONSTRAINT gate_company_id_name_key UNIQUE (company_id, name);


--
-- Name: gate gate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate
    ADD CONSTRAINT gate_pkey PRIMARY KEY (id);


--
-- Name: holiday holiday_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.holiday
    ADD CONSTRAINT holiday_pkey PRIMARY KEY (company_id, date);


--
-- Name: recognition_event recognition_event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_pkey PRIMARY KEY (id);


--
-- Name: recognition_model recognition_model_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_model
    ADD CONSTRAINT recognition_model_code_key UNIQUE (code);


--
-- Name: recognition_model recognition_model_manifest_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_model
    ADD CONSTRAINT recognition_model_manifest_id_key UNIQUE (manifest_id);


--
-- Name: recognition_model recognition_model_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_model
    ADD CONSTRAINT recognition_model_pkey PRIMARY KEY (id);


--
-- Name: shift_assignment shift_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT shift_assignment_pkey PRIMARY KEY (id);


--
-- Name: shift shift_company_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_company_id_name_key UNIQUE (company_id, name);


--
-- Name: shift shift_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_pkey PRIMARY KEY (id);


--
-- Name: threshold_profile threshold_profile_model_id_level_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threshold_profile
    ADD CONSTRAINT threshold_profile_model_id_level_key UNIQUE (model_id, level);


--
-- Name: threshold_profile threshold_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threshold_profile
    ADD CONSTRAINT threshold_profile_pkey PRIMARY KEY (id);


--
-- Name: user_account user_account_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_pkey PRIMARY KEY (id);


--
-- Name: user_role user_role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_pkey PRIMARY KEY (id);


--
-- Name: user_role ux_user_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT ux_user_role UNIQUE NULLS NOT DISTINCT (user_id, role, scope_department_id);


--
-- Name: ix_attendance_company_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_attendance_company_date ON public.attendance_day USING btree (company_id, work_date);


--
-- Name: ix_audit_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_actor ON public.audit_log USING btree (actor_user_id, at DESC);


--
-- Name: ix_audit_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_at ON public.audit_log USING btree (at DESC);


--
-- Name: ix_device_gate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_device_gate ON public.device USING btree (gate_id);


--
-- Name: ix_employee_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_employee_department ON public.employee USING btree (department_id);


--
-- Name: ix_event_employee_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_employee_time ON public.recognition_event USING btree (employee_id, occurred_at DESC) WHERE (employee_id IS NOT NULL);


--
-- Name: ix_event_gate_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_gate_time ON public.recognition_event USING btree (gate_id, occurred_at DESC);


--
-- Name: ix_event_handling_linked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_handling_linked ON public.event_handling USING btree (linked_employee_id) WHERE (linked_employee_id IS NOT NULL);


--
-- Name: ix_event_manual_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_manual_by ON public.recognition_event USING btree (performed_by_user_id, occurred_at DESC) WHERE (result = 'MANUAL_ATTENDANCE'::text);


--
-- Name: ix_event_result_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_result_time ON public.recognition_event USING btree (company_id, result, occurred_at DESC);


--
-- Name: ix_face_profile_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_face_profile_status ON public.face_profile USING btree (company_id, status);


--
-- Name: ix_face_sample_profile; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_face_sample_profile ON public.face_sample USING btree (profile_id);


--
-- Name: ix_refresh_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_refresh_user ON public.auth_refresh_token USING btree (user_id);


--
-- Name: ix_request_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_request_status ON public.attendance_request USING btree (company_id, status, created_at DESC);


--
-- Name: ux_face_profile_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_face_profile_active ON public.face_profile USING btree (employee_id) WHERE (status = 'ACTIVE'::text);


--
-- Name: ux_face_profile_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_face_profile_pending ON public.face_profile USING btree (employee_id) WHERE (status = 'PENDING_REVIEW'::text);


--
-- Name: ux_model_one_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_model_one_active ON public.recognition_model USING btree ((true)) WHERE is_active;


--
-- Name: ux_request_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_request_pending ON public.attendance_request USING btree (employee_id, work_date) WHERE (status = 'PENDING'::text);


--
-- Name: ux_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_user_email ON public.user_account USING btree (lower(email));


--
-- Name: ux_user_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_user_employee ON public.user_account USING btree (employee_id) WHERE (employee_id IS NOT NULL);


--
-- Name: attendance_day trg_attendance_day_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_attendance_day_updated BEFORE UPDATE ON public.attendance_day FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: attendance_request trg_attendance_request_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_attendance_request_updated BEFORE UPDATE ON public.attendance_request FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: company trg_company_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_company_updated BEFORE UPDATE ON public.company FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: department trg_department_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_department_updated BEFORE UPDATE ON public.department FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: device trg_device_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_device_updated BEFORE UPDATE ON public.device FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: employee trg_employee_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_employee_updated BEFORE UPDATE ON public.employee FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: event_handling trg_event_handling_check; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_event_handling_check BEFORE INSERT OR UPDATE ON public.event_handling FOR EACH ROW EXECUTE FUNCTION public.event_handling_check();


--
-- Name: face_profile trg_face_profile_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_face_profile_updated BEFORE UPDATE ON public.face_profile FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: gate trg_gate_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_gate_updated BEFORE UPDATE ON public.gate FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: recognition_event trg_recognition_event_guard; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_recognition_event_guard BEFORE DELETE OR UPDATE ON public.recognition_event FOR EACH ROW EXECUTE FUNCTION public.recognition_event_guard();


--
-- Name: shift trg_shift_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_shift_updated BEFORE UPDATE ON public.shift FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: user_account trg_user_account_updated; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_user_account_updated BEFORE UPDATE ON public.user_account FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: attendance_day attendance_day_check_in_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_check_in_event_id_fkey FOREIGN KEY (check_in_event_id) REFERENCES public.recognition_event(id);


--
-- Name: attendance_day attendance_day_check_out_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_check_out_event_id_fkey FOREIGN KEY (check_out_event_id) REFERENCES public.recognition_event(id);


--
-- Name: attendance_day attendance_day_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: attendance_day attendance_day_edited_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_edited_by_user_id_fkey FOREIGN KEY (edited_by_user_id) REFERENCES public.user_account(id);


--
-- Name: attendance_day attendance_day_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: attendance_day attendance_day_shift_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_day
    ADD CONSTRAINT attendance_day_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES public.shift(id);


--
-- Name: attendance_request attendance_request_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_request
    ADD CONSTRAINT attendance_request_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: attendance_request attendance_request_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_request
    ADD CONSTRAINT attendance_request_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: attendance_request attendance_request_requested_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_request
    ADD CONSTRAINT attendance_request_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES public.user_account(id);


--
-- Name: attendance_request attendance_request_reviewer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance_request
    ADD CONSTRAINT attendance_request_reviewer_user_id_fkey FOREIGN KEY (reviewer_user_id) REFERENCES public.user_account(id);


--
-- Name: audit_log audit_log_actor_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_actor_device_id_fkey FOREIGN KEY (actor_device_id) REFERENCES public.device(id);


--
-- Name: audit_log audit_log_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.user_account(id);


--
-- Name: audit_log audit_log_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: auth_refresh_token auth_refresh_token_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_refresh_token
    ADD CONSTRAINT auth_refresh_token_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_account(id) ON DELETE CASCADE;


--
-- Name: department department_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.department
    ADD CONSTRAINT department_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: device device_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: device device_gate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.device
    ADD CONSTRAINT device_gate_id_fkey FOREIGN KEY (gate_id) REFERENCES public.gate(id);


--
-- Name: employee employee_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: employee employee_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(id);


--
-- Name: event_handling event_handling_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_handling
    ADD CONSTRAINT event_handling_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.recognition_event(id);


--
-- Name: event_handling event_handling_handled_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_handling
    ADD CONSTRAINT event_handling_handled_by_user_id_fkey FOREIGN KEY (handled_by_user_id) REFERENCES public.user_account(id);


--
-- Name: event_handling event_handling_linked_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_handling
    ADD CONSTRAINT event_handling_linked_employee_id_fkey FOREIGN KEY (linked_employee_id) REFERENCES public.employee(id);


--
-- Name: face_embedding face_embedding_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_embedding
    ADD CONSTRAINT face_embedding_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.recognition_model(id);


--
-- Name: face_embedding face_embedding_sample_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_embedding
    ADD CONSTRAINT face_embedding_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES public.face_sample(id) ON DELETE CASCADE;


--
-- Name: face_profile face_profile_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: face_profile face_profile_duplicate_of_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_duplicate_of_employee_id_fkey FOREIGN KEY (duplicate_of_employee_id) REFERENCES public.employee(id);


--
-- Name: face_profile face_profile_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: face_profile face_profile_enrolled_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_enrolled_by_user_id_fkey FOREIGN KEY (enrolled_by_user_id) REFERENCES public.user_account(id);


--
-- Name: face_profile face_profile_enrolled_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_enrolled_device_id_fkey FOREIGN KEY (enrolled_device_id) REFERENCES public.device(id);


--
-- Name: face_profile face_profile_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_profile
    ADD CONSTRAINT face_profile_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.user_account(id);


--
-- Name: face_sample face_sample_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_sample
    ADD CONSTRAINT face_sample_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.face_profile(id) ON DELETE CASCADE;


--
-- Name: face_template face_template_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_template
    ADD CONSTRAINT face_template_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.recognition_model(id);


--
-- Name: face_template face_template_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.face_template
    ADD CONSTRAINT face_template_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.face_profile(id) ON DELETE CASCADE;


--
-- Name: employee fk_employee_consent_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT fk_employee_consent_by FOREIGN KEY (face_consent_by) REFERENCES public.user_account(id);


--
-- Name: gate_allowed_department gate_allowed_department_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate_allowed_department
    ADD CONSTRAINT gate_allowed_department_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(id) ON DELETE CASCADE;


--
-- Name: gate_allowed_department gate_allowed_department_gate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate_allowed_department
    ADD CONSTRAINT gate_allowed_department_gate_id_fkey FOREIGN KEY (gate_id) REFERENCES public.gate(id) ON DELETE CASCADE;


--
-- Name: gate gate_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gate
    ADD CONSTRAINT gate_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: holiday holiday_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.holiday
    ADD CONSTRAINT holiday_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: recognition_event recognition_event_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: recognition_event recognition_event_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.device(id);


--
-- Name: recognition_event recognition_event_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: recognition_event recognition_event_gate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_gate_id_fkey FOREIGN KEY (gate_id) REFERENCES public.gate(id);


--
-- Name: recognition_event recognition_event_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.recognition_model(id);


--
-- Name: recognition_event recognition_event_performed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recognition_event
    ADD CONSTRAINT recognition_event_performed_by_user_id_fkey FOREIGN KEY (performed_by_user_id) REFERENCES public.user_account(id);


--
-- Name: shift_assignment shift_assignment_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT shift_assignment_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: shift_assignment shift_assignment_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT shift_assignment_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(id);


--
-- Name: shift_assignment shift_assignment_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT shift_assignment_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: shift_assignment shift_assignment_shift_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift_assignment
    ADD CONSTRAINT shift_assignment_shift_id_fkey FOREIGN KEY (shift_id) REFERENCES public.shift(id);


--
-- Name: shift shift_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shift
    ADD CONSTRAINT shift_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: threshold_profile threshold_profile_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threshold_profile
    ADD CONSTRAINT threshold_profile_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.recognition_model(id);


--
-- Name: user_account user_account_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id);


--
-- Name: user_account user_account_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employee(id);


--
-- Name: user_role user_role_scope_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_scope_department_id_fkey FOREIGN KEY (scope_department_id) REFERENCES public.department(id);


--
-- Name: user_role user_role_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_account(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict hOuC6hlnKeNp7ER3LWMySHB2uEQa1m9aicbeoFW7OcsfE3MwzgGO1m0CH3sj3l0

