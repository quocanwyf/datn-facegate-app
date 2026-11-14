-- =====================================================================
-- SCHEMA CSDL — App chấm công & kiểm soát ra vào bằng khuôn mặt (bản DEMO)
-- ĐATN Nguyễn Quốc An, PTIT. Theo 03-app/dac-ta-app.md v1.4 (§0a, §4–§7)
-- và 03-app/db/thiet-ke-db.md. PostgreSQL 16.
-- Đây là bản THAM CHIẾU; Alembic migration đầu tiên phải tương đương
-- (kiểm bằng pg_dump --schema-only so sánh).
-- Quy ước: id uuid; thời điểm timestamptz (lưu UTC); enum = text + CHECK.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS btree_gist;   -- cho EXCLUDE chống chồng phân ca

-- ---------- tiện ích: tự cập nhật updated_at ----------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$ LANGUAGE plpgsql;

-- =====================================================================
-- 1. TỔ CHỨC
-- =====================================================================
CREATE TABLE company (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  timezone    text NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
  settings    jsonb NOT NULL DEFAULT '{}'::jsonb,   -- tham số §4.5, L, anti_spoof_enabled
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE department (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  uuid NOT NULL REFERENCES company(id),
  name        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, name)
);

CREATE TABLE employee (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id            uuid NOT NULL REFERENCES company(id),
  department_id         uuid NOT NULL REFERENCES department(id),
  code                  text NOT NULL,                     -- mã NV, vd NV001
  full_name             text NOT NULL,
  email                 text,
  phone                 text,
  status                text NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE','SUSPENDED','TERMINATED')),
  attendance_method     text NOT NULL DEFAULT 'FACE'
                        CHECK (attendance_method IN ('FACE','MANUAL')),
  joined_at             date,
  terminated_at         timestamptz,
  face_consent_at       timestamptz,                       -- ô "Đồng ý" trên Kiosk (§0a)
  face_consent_by       uuid,                              -- FK user_account, thêm ở dưới
  biometric_deleted_at  timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, code),
  CHECK (status <> 'TERMINATED' OR terminated_at IS NOT NULL),
  CHECK ((face_consent_at IS NULL) = (face_consent_by IS NULL))
);
CREATE INDEX ix_employee_department ON employee(department_id);

-- =====================================================================
-- 2. TÀI KHOẢN & PHÂN QUYỀN
-- =====================================================================
CREATE TABLE user_account (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id            uuid NOT NULL REFERENCES company(id),
  email                 text NOT NULL,
  password_hash         text NOT NULL,                     -- argon2id
  status                text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','DISABLED')),
  employee_id           uuid REFERENCES employee(id),
  must_change_password  boolean NOT NULL DEFAULT true,
  kiosk_pin_hash        text,                              -- PIN cá nhân (chỉ HR/OWNER dùng)
  pin_failed_count      smallint NOT NULL DEFAULT 0,
  pin_locked_until      timestamptz,
  last_login_at         timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_user_email ON user_account (lower(email));
CREATE UNIQUE INDEX ux_user_employee ON user_account (employee_id) WHERE employee_id IS NOT NULL;

ALTER TABLE employee
  ADD CONSTRAINT fk_employee_consent_by FOREIGN KEY (face_consent_by) REFERENCES user_account(id);

CREATE TABLE user_role (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
  role                 text NOT NULL CHECK (role IN ('OWNER','HR','MANAGER','SECURITY','EMPLOYEE')),
  scope_department_id  uuid REFERENCES department(id),   -- nguồn sự thật duy nhất cho "quản lý phòng ban"
  created_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ux_user_role UNIQUE NULLS NOT DISTINCT (user_id, role, scope_department_id),
  CHECK ((role = 'MANAGER') = (scope_department_id IS NOT NULL))
);

CREATE TABLE auth_refresh_token (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
  token_hash  text NOT NULL UNIQUE,
  expires_at  timestamptz NOT NULL,
  revoked_at  timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_user ON auth_refresh_token(user_id);

-- =====================================================================
-- 3. MÔ HÌNH & NGƯỠNG (toàn cục, không theo công ty)
-- =====================================================================
CREATE TABLE recognition_model (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code               text NOT NULL UNIQUE,                 -- 'V1_S3' (bản demo chỉ 1 mô hình)
  name               text NOT NULL,
  backbone           text NOT NULL,
  manifest_id        text NOT NULL UNIQUE,                 -- id trong manifest_24.json
  source_path        text NOT NULL,
  source_sha256      char(64) NOT NULL,
  stripped_sha256    char(64) NOT NULL,                    -- = meta.sha256 trong ket_qua_blufr_lfw.json
  epoch              smallint NOT NULL,
  t_bs               real NOT NULL,                        -- b̃/s (meta.t_eq30)
  alignment_version  text NOT NULL,                        -- detector + quy tắc chọn mặt
  runtime            jsonb NOT NULL DEFAULT '{}'::jsonb,   -- python/torch/opencv/cuda/fp16 thực tế (ghi lúc khởi động)
  is_active          boolean NOT NULL DEFAULT true,
  created_at         timestamptz NOT NULL DEFAULT now()
);
-- tối đa 1 mô hình đang chạy (giữ bảng để đổi mô hình sau này mà không sửa app)
CREATE UNIQUE INDEX ux_model_one_active ON recognition_model((true)) WHERE is_active;

CREATE TABLE threshold_profile (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id       uuid NOT NULL REFERENCES recognition_model(id),
  level          text NOT NULL CHECK (level IN ('DEFAULT_VAL','STRICT_TEST')),
  cos_threshold  real NOT NULL CHECK (cos_threshold BETWEEN -1 AND 1),
  label          text NOT NULL,                            -- nhãn bắt buộc hiển thị (§4.4)
  source_ref     text NOT NULL,                            -- file + trường log
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (model_id, level)
);

-- =====================================================================
-- 4. CỬA & THIẾT BỊ
-- =====================================================================
CREATE TABLE gate (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id        uuid NOT NULL REFERENCES company(id),
  name              text NOT NULL,
  mode              text NOT NULL CHECK (mode IN ('ATTENDANCE_ACCESS','ACCESS_ONLY')),
  default_policy    text NOT NULL CHECK (default_policy IN ('ALLOW_ALL_ACTIVE','DEPARTMENTS_ONLY')),
  threshold_level   text NOT NULL CHECK (threshold_level IN ('DEFAULT_VAL','STRICT_TEST','CUSTOM')),
  custom_threshold  real CHECK (custom_threshold BETWEEN -1 AND 1),
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, name),
  CHECK ((threshold_level = 'CUSTOM') = (custom_threshold IS NOT NULL))
);

CREATE TABLE gate_allowed_department (
  gate_id        uuid NOT NULL REFERENCES gate(id) ON DELETE CASCADE,
  department_id  uuid NOT NULL REFERENCES department(id) ON DELETE CASCADE,
  PRIMARY KEY (gate_id, department_id)
);

CREATE TABLE device (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id          uuid NOT NULL REFERENCES company(id),
  gate_id             uuid NOT NULL REFERENCES gate(id),
  name                text NOT NULL,
  status              text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','ACTIVE','REVOKED')),
  pairing_code_hash   text,
  pairing_expires_at  timestamptz,
  pairing_attempts    smallint NOT NULL DEFAULT 0,
  token_hash          text UNIQUE,
  token_expires_at    timestamptz,
  last_seen_at        timestamptz,
  app_version         text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CHECK (status <> 'ACTIVE' OR token_hash IS NOT NULL)
);
CREATE INDEX ix_device_gate ON device(gate_id);

-- =====================================================================
-- 5. KHUÔN MẶT
-- =====================================================================
CREATE TABLE face_profile (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id                uuid NOT NULL REFERENCES company(id),
  employee_id               uuid NOT NULL REFERENCES employee(id),
  status                    text NOT NULL DEFAULT 'PENDING_REVIEW'
                            CHECK (status IN ('PENDING_REVIEW','ACTIVE','REJECTED','SUPERSEDED')),
  enrolled_by_user_id       uuid NOT NULL REFERENCES user_account(id),
  enrolled_device_id        uuid REFERENCES device(id),
  duplicate_of_employee_id  uuid REFERENCES employee(id), -- cảnh báo trùng lúc đăng ký
  duplicate_score           real,
  reviewed_by_user_id       uuid REFERENCES user_account(id),
  reviewed_at               timestamptz,
  review_note               text,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),
  CHECK ((status IN ('ACTIVE','REJECTED')) <= (reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL)),
  CHECK ((duplicate_of_employee_id IS NULL) = (duplicate_score IS NULL)),
  CHECK (duplicate_of_employee_id IS NULL OR duplicate_of_employee_id <> employee_id)
);
CREATE UNIQUE INDEX ux_face_profile_active  ON face_profile(employee_id) WHERE status = 'ACTIVE';
CREATE UNIQUE INDEX ux_face_profile_pending ON face_profile(employee_id) WHERE status = 'PENDING_REVIEW';
CREATE INDEX ix_face_profile_status ON face_profile(company_id, status);

CREATE TABLE face_sample (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id  uuid NOT NULL REFERENCES face_profile(id) ON DELETE CASCADE,
  image_path  text NOT NULL,                               -- PNG 112x112 RGB đã căn chỉnh
  det_score   real NOT NULL,
  yaw_ratio   real NOT NULL,
  p_live      real,                                        -- NULL khi tắt chống giả mạo
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_face_sample_profile ON face_sample(profile_id);

CREATE TABLE face_embedding (
  sample_id   uuid NOT NULL REFERENCES face_sample(id) ON DELETE CASCADE,
  model_id    uuid NOT NULL REFERENCES recognition_model(id),
  vector      real[] NOT NULL CHECK (array_ndims(vector) = 1 AND array_length(vector, 1) = 512),
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (sample_id, model_id)
);

CREATE TABLE face_template (
  profile_id  uuid NOT NULL REFERENCES face_profile(id) ON DELETE CASCADE,
  model_id    uuid NOT NULL REFERENCES recognition_model(id),
  vector      real[] NOT NULL CHECK (array_ndims(vector) = 1 AND array_length(vector, 1) = 512),
  n_samples   smallint NOT NULL CHECK (n_samples > 0),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (profile_id, model_id)
);

-- =====================================================================
-- 6. CA LÀM & LỊCH
-- =====================================================================
CREATE TABLE shift (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id     uuid NOT NULL REFERENCES company(id),
  name           text NOT NULL,
  start_time     time NOT NULL,
  end_time       time NOT NULL,
  break_start    time,
  break_end      time,
  grace_in_min   smallint NOT NULL DEFAULT 5 CHECK (grace_in_min BETWEEN 0 AND 120),
  grace_out_min  smallint NOT NULL DEFAULT 5 CHECK (grace_out_min BETWEEN 0 AND 120),
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, name),
  CHECK (end_time > start_time),                           -- MVP: không qua nửa đêm
  CHECK (end_time - start_time <= interval '17 hours'),    -- để cửa sổ [start-3h, end+4h] hai ngày không chồng
  CHECK ((break_start IS NULL) = (break_end IS NULL)),
  CHECK (break_start IS NULL OR (break_start >= start_time AND break_end <= end_time AND break_end > break_start))
);

CREATE TABLE shift_assignment (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id      uuid NOT NULL REFERENCES company(id),
  shift_id        uuid NOT NULL REFERENCES shift(id),
  employee_id     uuid REFERENCES employee(id),
  department_id   uuid REFERENCES department(id),
  weekday         smallint NOT NULL CHECK (weekday BETWEEN 1 AND 7),   -- ISO: 1 = Thứ Hai
  effective_from  date NOT NULL,
  effective_to    date,                                                -- NULL = không thời hạn
  effective       daterange GENERATED ALWAYS AS (daterange(effective_from, effective_to, '[]')) STORED,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CHECK ((employee_id IS NULL) <> (department_id IS NULL)),
  CHECK (effective_to IS NULL OR effective_to >= effective_from),
  CONSTRAINT ex_assign_employee EXCLUDE USING gist
    (employee_id WITH =, weekday WITH =, effective WITH &&) WHERE (employee_id IS NOT NULL),
  CONSTRAINT ex_assign_department EXCLUDE USING gist
    (department_id WITH =, weekday WITH =, effective WITH &&) WHERE (department_id IS NOT NULL)
);
-- Quy tắc ưu tiên (ở tầng ứng dụng): phân ca cá nhân > phân ca phòng ban.

CREATE TABLE holiday (
  company_id  uuid NOT NULL REFERENCES company(id),
  date        date NOT NULL,
  name        text NOT NULL,
  PRIMARY KEY (company_id, date)
);

-- =====================================================================
-- 7. SỰ KIỆN NHẬN DẠNG (dữ liệu gốc, chỉ thêm)
-- =====================================================================
CREATE TABLE recognition_event (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id            uuid NOT NULL REFERENCES company(id),
  gate_id               uuid NOT NULL REFERENCES gate(id),
  device_id             uuid REFERENCES device(id),
  occurred_at           timestamptz NOT NULL,
  result                text NOT NULL CHECK (result IN
                          ('MATCH','UNKNOWN','SPOOF','DENIED_RULE','DENIED_INACTIVE',
                           'MANUAL_OPEN','MANUAL_ATTENDANCE')),
  employee_id           uuid REFERENCES employee(id),
  model_id              uuid REFERENCES recognition_model(id),
  top1_score            real,
  threshold_used        real,
  threshold_level       text CHECK (threshold_level IN ('DEFAULT_VAL','STRICT_TEST','CUSTOM')),
  p_live_min            real,
  n_frames              smallint,
  door_action           text NOT NULL DEFAULT 'NONE' CHECK (door_action IN ('OPEN','NONE')),
  snapshot_path         text,                              -- chỉ UNKNOWN/SPOOF
  performed_by_user_id  uuid REFERENCES user_account(id),  -- MANUAL_*
  reason                text,                              -- MANUAL_*
  created_at            timestamptz NOT NULL DEFAULT now(),
  -- kết quả từ nhận dạng: phải có mô hình, điểm, ngưỡng, thiết bị
  CHECK (result NOT IN ('MATCH','UNKNOWN','SPOOF','DENIED_RULE','DENIED_INACTIVE')
         OR (model_id IS NOT NULL AND device_id IS NOT NULL AND n_frames IS NOT NULL)),
  CHECK (result NOT IN ('MATCH','DENIED_RULE','DENIED_INACTIVE')
         OR (employee_id IS NOT NULL AND top1_score IS NOT NULL AND threshold_used IS NOT NULL)),
  CHECK (result NOT IN ('UNKNOWN','SPOOF') OR employee_id IS NULL),
  CHECK (result NOT IN ('MATCH','DENIED_RULE','DENIED_INACTIVE','MANUAL_OPEN','MANUAL_ATTENDANCE')
         OR snapshot_path IS NULL),                         -- không lưu ảnh cho người đã nhận ra
  CHECK (result NOT IN ('MANUAL_OPEN','MANUAL_ATTENDANCE')
         OR (performed_by_user_id IS NOT NULL AND reason IS NOT NULL AND length(trim(reason)) > 0)),
  CHECK (result <> 'MANUAL_ATTENDANCE' OR employee_id IS NOT NULL),
  CHECK ((door_action = 'OPEN') = (result IN ('MATCH','MANUAL_OPEN')))
);
CREATE INDEX ix_event_gate_time     ON recognition_event(gate_id, occurred_at DESC);
CREATE INDEX ix_event_employee_time ON recognition_event(employee_id, occurred_at DESC) WHERE employee_id IS NOT NULL;
CREATE INDEX ix_event_result_time   ON recognition_event(company_id, result, occurred_at DESC);
CREATE INDEX ix_event_manual_by     ON recognition_event(performed_by_user_id, occurred_at DESC)
  WHERE result = 'MANUAL_ATTENDANCE';

-- Chỉ thêm: cấm DELETE; UPDATE chỉ được đặt snapshot_path về NULL (xoá ảnh khi xoá dữ liệu khuôn mặt).
CREATE OR REPLACE FUNCTION recognition_event_guard() RETURNS trigger AS $$
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
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_recognition_event_guard
  BEFORE UPDATE OR DELETE ON recognition_event
  FOR EACH ROW EXECUTE FUNCTION recognition_event_guard();

CREATE TABLE event_handling (
  event_id            uuid PRIMARY KEY REFERENCES recognition_event(id),
  status              text NOT NULL CHECK (status IN ('RESOLVED','FALSE_ALARM','IS_EMPLOYEE')),
  linked_employee_id  uuid REFERENCES employee(id),
  handled_by_user_id  uuid NOT NULL REFERENCES user_account(id),
  handled_at          timestamptz NOT NULL DEFAULT now(),
  note                text,
  CHECK ((status = 'IS_EMPLOYEE') = (linked_employee_id IS NOT NULL))
);
CREATE INDEX ix_event_handling_linked ON event_handling(linked_employee_id) WHERE linked_employee_id IS NOT NULL;

-- Chỉ xử lý được cảnh báo (UNKNOWN / SPOOF)
CREATE OR REPLACE FUNCTION event_handling_check() RETURNS trigger AS $$
DECLARE r text;
BEGIN
  SELECT result INTO r FROM recognition_event WHERE id = NEW.event_id;
  IF r NOT IN ('UNKNOWN','SPOOF') THEN
    RAISE EXCEPTION 'event_handling chỉ áp dụng cho UNKNOWN/SPOOF (nhận %)', r;
  END IF;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_event_handling_check
  BEFORE INSERT OR UPDATE ON event_handling
  FOR EACH ROW EXECUTE FUNCTION event_handling_check();

-- =====================================================================
-- 8. CHẤM CÔNG (dữ liệu dẫn xuất) & GIẢI TRÌNH
-- =====================================================================
CREATE TABLE attendance_day (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id          uuid NOT NULL REFERENCES company(id),
  employee_id         uuid NOT NULL REFERENCES employee(id),
  work_date           date NOT NULL,
  shift_id            uuid REFERENCES shift(id),
  check_in_at         timestamptz,
  check_out_at        timestamptz,
  check_in_event_id   uuid REFERENCES recognition_event(id),
  check_out_event_id  uuid REFERENCES recognition_event(id),
  status              text NOT NULL CHECK (status IN
                        ('HOLIDAY','LEAVE','OFF','NOT_STARTED','WAITING_IN','IN_PROGRESS','ABSENT','MISSING_OUT',
                         'NORMAL','LATE','EARLY','LATE_EARLY')),
  suspect_forgot_out  boolean NOT NULL DEFAULT false,
  late_min            smallint NOT NULL DEFAULT 0 CHECK (late_min >= 0),
  early_min           smallint NOT NULL DEFAULT 0 CHECK (early_min >= 0),
  worked_min          smallint NOT NULL DEFAULT 0 CHECK (worked_min >= 0),
  source              text NOT NULL DEFAULT 'AUTO' CHECK (source IN ('AUTO','ADJUSTED','MANUAL')),
  finalized           boolean NOT NULL DEFAULT false,
  edited_by_user_id   uuid REFERENCES user_account(id),
  edit_reason         text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (employee_id, work_date),
  CHECK (check_out_at IS NULL OR (check_in_at IS NOT NULL AND check_out_at >= check_in_at)),
  CHECK (source <> 'MANUAL' OR (edited_by_user_id IS NOT NULL AND edit_reason IS NOT NULL)),
  CHECK (NOT suspect_forgot_out OR status = 'MISSING_OUT'),
  CHECK (status NOT IN ('NORMAL','LATE','EARLY','LATE_EARLY') OR check_out_at IS NOT NULL),
  CHECK (status NOT IN ('IN_PROGRESS','MISSING_OUT') OR check_in_at IS NOT NULL),
  CHECK (status <> 'WAITING_IN' OR (check_in_at IS NULL AND NOT finalized))
);
CREATE INDEX ix_attendance_company_date ON attendance_day(company_id, work_date);

CREATE TABLE attendance_request (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id            uuid NOT NULL REFERENCES company(id),
  employee_id           uuid NOT NULL REFERENCES employee(id),
  requested_by_user_id  uuid NOT NULL REFERENCES user_account(id),
  work_date             date NOT NULL,
  type                  text NOT NULL CHECK (type IN
                          ('FORGOT_IN','FORGOT_OUT','NOT_RECOGNIZED','BUSINESS_TRIP','OTHER')),
  requested_in          timestamptz,
  requested_out         timestamptz,
  reason                text NOT NULL CHECK (length(trim(reason)) > 0),
  status                text NOT NULL DEFAULT 'PENDING'
                        CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED')),
  reviewer_user_id      uuid REFERENCES user_account(id),
  reviewed_at           timestamptz,
  review_note           text,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CHECK ((status IN ('APPROVED','REJECTED')) = (reviewer_user_id IS NOT NULL AND reviewed_at IS NOT NULL)),
  CHECK (reviewer_user_id IS NULL OR reviewer_user_id <> requested_by_user_id),   -- người duyệt ≠ người gửi
  CHECK (type <> 'FORGOT_IN'  OR requested_in  IS NOT NULL),
  CHECK (type <> 'FORGOT_OUT' OR requested_out IS NOT NULL),
  CHECK (requested_in IS NULL OR requested_out IS NULL OR requested_out > requested_in)
);
CREATE UNIQUE INDEX ux_request_pending ON attendance_request(employee_id, work_date) WHERE status = 'PENDING';
CREATE INDEX ix_request_status ON attendance_request(company_id, status, created_at DESC);

-- =====================================================================
-- 9. NHẬT KÝ THAO TÁC (bản demo: action + entity, không before/after)
-- =====================================================================
CREATE TABLE audit_log (
  id               bigserial PRIMARY KEY,
  company_id       uuid REFERENCES company(id),
  actor_user_id    uuid REFERENCES user_account(id),
  actor_device_id  uuid REFERENCES device(id),
  action           text NOT NULL,                          -- vd FACE_APPROVE, EMPLOYEE_TERMINATE, COMPARE_SESSION
  entity           text NOT NULL,
  entity_id        text,
  detail           jsonb,
  at               timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_at ON audit_log(at DESC);
CREATE INDEX ix_audit_actor ON audit_log(actor_user_id, at DESC);

-- ---------- trigger updated_at ----------
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['company','department','employee','user_account','gate','device',
                           'face_profile','shift','attendance_day','attendance_request']
  LOOP
    EXECUTE format('CREATE TRIGGER trg_%I_updated BEFORE UPDATE ON %I
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at()', t, t);
  END LOOP;
END $$;
