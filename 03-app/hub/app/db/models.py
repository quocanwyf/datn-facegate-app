"""23 bảng PostgreSQL tham chiếu; trigger nằm trong revision SQL cố định.

Khởi tạo từ phản chiếu schema bằng sqlacodegen 4.0.4; đã bổ sung EXCLUDE,
NULLS NOT DISTINCT, biểu thức và chiều index mà trình sinh không giữ đủ.
Không dùng create_all để thay Alembic hoặc bỏ trigger.
"""
from typing import Optional
import datetime
import uuid

from sqlalchemy import BigInteger, Boolean, CHAR, CheckConstraint, Column, Computed, Date, DateTime, ForeignKeyConstraint, Index, PrimaryKeyConstraint, REAL, SmallInteger, Table, Text, Time, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import ARRAY, DATERANGE, JSONB, ExcludeConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = 'company'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='company_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'Asia/Ho_Chi_Minh'::text"))
    settings: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class Employee(Base):
    __tablename__ = 'employee'
    __table_args__ = (
        CheckConstraint('(face_consent_at IS NULL) = (face_consent_by IS NULL)', name='employee_check1'),
        CheckConstraint("attendance_method = ANY (ARRAY['FACE'::text, 'MANUAL'::text])", name='employee_attendance_method_check'),
        CheckConstraint("status <> 'TERMINATED'::text OR terminated_at IS NOT NULL", name='employee_check'),
        CheckConstraint("status = ANY (ARRAY['ACTIVE'::text, 'SUSPENDED'::text, 'TERMINATED'::text])", name='employee_status_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='employee_company_id_fkey'),
        ForeignKeyConstraint(['department_id'], ['department.id'], name='employee_department_id_fkey'),
        ForeignKeyConstraint(['face_consent_by'], ['user_account.id'], name='fk_employee_consent_by'),
        PrimaryKeyConstraint('id', name='employee_pkey'),
        UniqueConstraint('company_id', 'code', name='employee_company_id_code_key'),
        Index('ix_employee_department', 'department_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'ACTIVE'::text"))
    attendance_method: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'FACE'::text"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    joined_at: Mapped[Optional[datetime.date]] = mapped_column(Date)
    terminated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    face_consent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    face_consent_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    biometric_deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    company: Mapped['Company'] = relationship('Company')
    department: Mapped['Department'] = relationship('Department')
    user_account: Mapped[Optional['UserAccount']] = relationship('UserAccount', foreign_keys=[face_consent_by])


class RecognitionModel(Base):
    __tablename__ = 'recognition_model'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='recognition_model_pkey'),
        UniqueConstraint('code', name='recognition_model_code_key'),
        UniqueConstraint('manifest_id', name='recognition_model_manifest_id_key'),
        Index('ux_model_one_active', text('(true)'), postgresql_where=text('is_active'), unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    backbone: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    stripped_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    epoch: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    t_bs: Mapped[float] = mapped_column(REAL, nullable=False)
    alignment_version: Mapped[str] = mapped_column(Text, nullable=False)
    runtime: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class UserAccount(Base):
    __tablename__ = 'user_account'
    __table_args__ = (
        CheckConstraint("status = ANY (ARRAY['ACTIVE'::text, 'DISABLED'::text])", name='user_account_status_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='user_account_company_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='user_account_employee_id_fkey'),
        PrimaryKeyConstraint('id', name='user_account_pkey'),
        Index('ux_user_email', text('lower(email)'), unique=True),
        Index('ux_user_employee', 'employee_id', postgresql_where=text('(employee_id IS NOT NULL)'), unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'ACTIVE'::text"))
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    pin_failed_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    kiosk_pin_hash: Mapped[Optional[str]] = mapped_column(Text)
    pin_locked_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    company: Mapped['Company'] = relationship('Company')
    employee: Mapped[Optional['Employee']] = relationship('Employee', foreign_keys=[employee_id])


class AttendanceRequest(Base):
    __tablename__ = 'attendance_request'
    __table_args__ = (
        CheckConstraint("(status = ANY (ARRAY['APPROVED'::text, 'REJECTED'::text])) = (reviewer_user_id IS NOT NULL AND reviewed_at IS NOT NULL)", name='attendance_request_check'),
        CheckConstraint('length(TRIM(BOTH FROM reason)) > 0', name='attendance_request_reason_check'),
        CheckConstraint('requested_in IS NULL OR requested_out IS NULL OR requested_out > requested_in', name='attendance_request_check4'),
        CheckConstraint('reviewer_user_id IS NULL OR reviewer_user_id <> requested_by_user_id', name='attendance_request_check1'),
        CheckConstraint("status = ANY (ARRAY['PENDING'::text, 'APPROVED'::text, 'REJECTED'::text, 'CANCELLED'::text])", name='attendance_request_status_check'),
        CheckConstraint("type <> 'FORGOT_IN'::text OR requested_in IS NOT NULL", name='attendance_request_check2'),
        CheckConstraint("type <> 'FORGOT_OUT'::text OR requested_out IS NOT NULL", name='attendance_request_check3'),
        CheckConstraint("type = ANY (ARRAY['FORGOT_IN'::text, 'FORGOT_OUT'::text, 'NOT_RECOGNIZED'::text, 'BUSINESS_TRIP'::text, 'OTHER'::text])", name='attendance_request_type_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='attendance_request_company_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='attendance_request_employee_id_fkey'),
        ForeignKeyConstraint(['requested_by_user_id'], ['user_account.id'], name='attendance_request_requested_by_user_id_fkey'),
        ForeignKeyConstraint(['reviewer_user_id'], ['user_account.id'], name='attendance_request_reviewer_user_id_fkey'),
        PrimaryKeyConstraint('id', name='attendance_request_pkey'),
        Index('ix_request_status', 'company_id', 'status', text('created_at DESC')),
        Index('ux_request_pending', 'employee_id', 'work_date', postgresql_where=text("(status = 'PENDING'::text)"), unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    work_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PENDING'::text"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    requested_in: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    requested_out: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    reviewer_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    review_note: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped['Company'] = relationship('Company')
    employee: Mapped['Employee'] = relationship('Employee')
    requested_by_user: Mapped['UserAccount'] = relationship('UserAccount', foreign_keys=[requested_by_user_id])
    reviewer_user: Mapped[Optional['UserAccount']] = relationship('UserAccount', foreign_keys=[reviewer_user_id])


class AuthRefreshToken(Base):
    __tablename__ = 'auth_refresh_token'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['user_account.id'], ondelete='CASCADE', name='auth_refresh_token_user_id_fkey'),
        PrimaryKeyConstraint('id', name='auth_refresh_token_pkey'),
        UniqueConstraint('token_hash', name='auth_refresh_token_token_hash_key'),
        Index('ix_refresh_user', 'user_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    user: Mapped['UserAccount'] = relationship('UserAccount')


class Department(Base):
    __tablename__ = 'department'
    __table_args__ = (
        ForeignKeyConstraint(['company_id'], ['company.id'], name='department_company_id_fkey'),
        PrimaryKeyConstraint('id', name='department_pkey'),
        UniqueConstraint('company_id', 'name', name='department_company_id_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    company: Mapped['Company'] = relationship('Company')
    gate: Mapped[list['Gate']] = relationship('Gate', secondary='gate_allowed_department')


class Gate(Base):
    __tablename__ = 'gate'
    __table_args__ = (
        CheckConstraint("(threshold_level = 'CUSTOM'::text) = (custom_threshold IS NOT NULL)", name='gate_check'),
        CheckConstraint("custom_threshold >= '-1'::integer::double precision AND custom_threshold <= 1::double precision", name='gate_custom_threshold_check'),
        CheckConstraint("default_policy = ANY (ARRAY['ALLOW_ALL_ACTIVE'::text, 'DEPARTMENTS_ONLY'::text])", name='gate_default_policy_check'),
        CheckConstraint("mode = ANY (ARRAY['ATTENDANCE_ACCESS'::text, 'ACCESS_ONLY'::text])", name='gate_mode_check'),
        CheckConstraint("threshold_level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text, 'CUSTOM'::text])", name='gate_threshold_level_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='gate_company_id_fkey'),
        PrimaryKeyConstraint('id', name='gate_pkey'),
        UniqueConstraint('company_id', 'name', name='gate_company_id_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    default_policy: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_level: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    custom_threshold: Mapped[Optional[float]] = mapped_column(REAL)

    company: Mapped['Company'] = relationship('Company')


class Holiday(Base):
    __tablename__ = 'holiday'
    __table_args__ = (
        ForeignKeyConstraint(['company_id'], ['company.id'], name='holiday_company_id_fkey'),
        PrimaryKeyConstraint('company_id', 'date', name='holiday_pkey')
    )

    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    company: Mapped['Company'] = relationship('Company')


class Shift(Base):
    __tablename__ = 'shift'
    __table_args__ = (
        CheckConstraint('(break_start IS NULL) = (break_end IS NULL)', name='shift_check2'),
        CheckConstraint("(end_time - start_time) <= '17:00:00'::interval", name='shift_check1'),
        CheckConstraint('break_start IS NULL OR break_start >= start_time AND break_end <= end_time AND break_end > break_start', name='shift_check3'),
        CheckConstraint('end_time > start_time', name='shift_check'),
        CheckConstraint('grace_in_min >= 0 AND grace_in_min <= 120', name='shift_grace_in_min_check'),
        CheckConstraint('grace_out_min >= 0 AND grace_out_min <= 120', name='shift_grace_out_min_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='shift_company_id_fkey'),
        PrimaryKeyConstraint('id', name='shift_pkey'),
        UniqueConstraint('company_id', 'name', name='shift_company_id_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    grace_in_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('5'))
    grace_out_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('5'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    break_start: Mapped[Optional[datetime.time]] = mapped_column(Time)
    break_end: Mapped[Optional[datetime.time]] = mapped_column(Time)

    company: Mapped['Company'] = relationship('Company')


class ThresholdProfile(Base):
    __tablename__ = 'threshold_profile'
    __table_args__ = (
        CheckConstraint("cos_threshold >= '-1'::integer::double precision AND cos_threshold <= 1::double precision", name='threshold_profile_cos_threshold_check'),
        CheckConstraint("level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text])", name='threshold_profile_level_check'),
        ForeignKeyConstraint(['model_id'], ['recognition_model.id'], name='threshold_profile_model_id_fkey'),
        PrimaryKeyConstraint('id', name='threshold_profile_pkey'),
        UniqueConstraint('model_id', 'level', name='threshold_profile_model_id_level_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    model_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    level: Mapped[str] = mapped_column(Text, nullable=False)
    cos_threshold: Mapped[float] = mapped_column(REAL, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    model: Mapped['RecognitionModel'] = relationship('RecognitionModel')


class Device(Base):
    __tablename__ = 'device'
    __table_args__ = (
        CheckConstraint("status <> 'ACTIVE'::text OR token_hash IS NOT NULL", name='device_check'),
        CheckConstraint("status = ANY (ARRAY['PENDING'::text, 'ACTIVE'::text, 'REVOKED'::text])", name='device_status_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='device_company_id_fkey'),
        ForeignKeyConstraint(['gate_id'], ['gate.id'], name='device_gate_id_fkey'),
        PrimaryKeyConstraint('id', name='device_pkey'),
        UniqueConstraint('token_hash', name='device_token_hash_key'),
        Index('ix_device_gate', 'gate_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    gate_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PENDING'::text"))
    pairing_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    pairing_code_hash: Mapped[Optional[str]] = mapped_column(Text)
    pairing_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    token_hash: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    last_seen_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    app_version: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped['Company'] = relationship('Company')
    gate: Mapped['Gate'] = relationship('Gate')


t_gate_allowed_department = Table(
    'gate_allowed_department', Base.metadata,
    Column('gate_id', Uuid, primary_key=True),
    Column('department_id', Uuid, primary_key=True),
    ForeignKeyConstraint(['department_id'], ['department.id'], ondelete='CASCADE', name='gate_allowed_department_department_id_fkey'),
    ForeignKeyConstraint(['gate_id'], ['gate.id'], ondelete='CASCADE', name='gate_allowed_department_gate_id_fkey'),
    PrimaryKeyConstraint('gate_id', 'department_id', name='gate_allowed_department_pkey')
)


class ShiftAssignment(Base):
    __tablename__ = 'shift_assignment'
    __table_args__ = (
        CheckConstraint('(employee_id IS NULL) <> (department_id IS NULL)', name='shift_assignment_check'),
        CheckConstraint('effective_to IS NULL OR effective_to >= effective_from', name='shift_assignment_check1'),
        CheckConstraint('weekday >= 1 AND weekday <= 7', name='shift_assignment_weekday_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='shift_assignment_company_id_fkey'),
        ForeignKeyConstraint(['department_id'], ['department.id'], name='shift_assignment_department_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='shift_assignment_employee_id_fkey'),
        ForeignKeyConstraint(['shift_id'], ['shift.id'], name='shift_assignment_shift_id_fkey'),
        PrimaryKeyConstraint('id', name='shift_assignment_pkey'),
        ExcludeConstraint(('employee_id', '='), ('weekday', '='), ('effective', '&&'),
                          name='ex_assign_employee', using='gist', where=text('employee_id IS NOT NULL')),
        ExcludeConstraint(('department_id', '='), ('weekday', '='), ('effective', '&&'),
                          name='ex_assign_department', using='gist', where=text('department_id IS NOT NULL'))
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    shift_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    effective_from: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    effective_to: Mapped[Optional[datetime.date]] = mapped_column(Date)
    effective: Mapped[Optional[object]] = mapped_column(DATERANGE, Computed("daterange(effective_from, effective_to, '[]'::text)", persisted=True))

    company: Mapped['Company'] = relationship('Company')
    department: Mapped[Optional['Department']] = relationship('Department')
    employee: Mapped[Optional['Employee']] = relationship('Employee')
    shift: Mapped['Shift'] = relationship('Shift')


class UserRole(Base):
    __tablename__ = 'user_role'
    __table_args__ = (
        CheckConstraint("(role = 'MANAGER'::text) = (scope_department_id IS NOT NULL)", name='user_role_check'),
        CheckConstraint("role = ANY (ARRAY['OWNER'::text, 'HR'::text, 'MANAGER'::text, 'SECURITY'::text, 'EMPLOYEE'::text])", name='user_role_role_check'),
        ForeignKeyConstraint(['scope_department_id'], ['department.id'], name='user_role_scope_department_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['user_account.id'], ondelete='CASCADE', name='user_role_user_id_fkey'),
        PrimaryKeyConstraint('id', name='user_role_pkey'),
        UniqueConstraint('user_id', 'role', 'scope_department_id', name='ux_user_role', postgresql_nulls_not_distinct=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    scope_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    scope_department: Mapped[Optional['Department']] = relationship('Department')
    user: Mapped['UserAccount'] = relationship('UserAccount')


class AuditLog(Base):
    __tablename__ = 'audit_log'
    __table_args__ = (
        ForeignKeyConstraint(['actor_device_id'], ['device.id'], name='audit_log_actor_device_id_fkey'),
        ForeignKeyConstraint(['actor_user_id'], ['user_account.id'], name='audit_log_actor_user_id_fkey'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='audit_log_company_id_fkey'),
        PrimaryKeyConstraint('id', name='audit_log_pkey'),
        Index('ix_audit_actor', 'actor_user_id', text('at DESC')),
        Index('ix_audit_at', text('at DESC'))
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    actor_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    entity_id: Mapped[Optional[str]] = mapped_column(Text)
    detail: Mapped[Optional[object]] = mapped_column(JSONB)

    actor_device: Mapped[Optional['Device']] = relationship('Device')
    actor_user: Mapped[Optional['UserAccount']] = relationship('UserAccount')
    company: Mapped[Optional['Company']] = relationship('Company')


class FaceProfile(Base):
    __tablename__ = 'face_profile'
    __table_args__ = (
        CheckConstraint('(duplicate_of_employee_id IS NULL) = (duplicate_score IS NULL)', name='face_profile_check1'),
        CheckConstraint("(status = ANY (ARRAY['ACTIVE'::text, 'REJECTED'::text])) <= (reviewed_by_user_id IS NOT NULL AND reviewed_at IS NOT NULL)", name='face_profile_check'),
        CheckConstraint('duplicate_of_employee_id IS NULL OR duplicate_of_employee_id <> employee_id', name='face_profile_check2'),
        CheckConstraint("status = ANY (ARRAY['PENDING_REVIEW'::text, 'ACTIVE'::text, 'REJECTED'::text, 'SUPERSEDED'::text])", name='face_profile_status_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='face_profile_company_id_fkey'),
        ForeignKeyConstraint(['duplicate_of_employee_id'], ['employee.id'], name='face_profile_duplicate_of_employee_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='face_profile_employee_id_fkey'),
        ForeignKeyConstraint(['enrolled_by_user_id'], ['user_account.id'], name='face_profile_enrolled_by_user_id_fkey'),
        ForeignKeyConstraint(['enrolled_device_id'], ['device.id'], name='face_profile_enrolled_device_id_fkey'),
        ForeignKeyConstraint(['reviewed_by_user_id'], ['user_account.id'], name='face_profile_reviewed_by_user_id_fkey'),
        PrimaryKeyConstraint('id', name='face_profile_pkey'),
        Index('ix_face_profile_status', 'company_id', 'status'),
        Index('ux_face_profile_active', 'employee_id', postgresql_where=text("(status = 'ACTIVE'::text)"), unique=True),
        Index('ux_face_profile_pending', 'employee_id', postgresql_where=text("(status = 'PENDING_REVIEW'::text)"), unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PENDING_REVIEW'::text"))
    enrolled_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    enrolled_device_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    duplicate_of_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    duplicate_score: Mapped[Optional[float]] = mapped_column(REAL)
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    review_note: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped['Company'] = relationship('Company')
    duplicate_of_employee: Mapped[Optional['Employee']] = relationship('Employee', foreign_keys=[duplicate_of_employee_id])
    employee: Mapped['Employee'] = relationship('Employee', foreign_keys=[employee_id])
    enrolled_by_user: Mapped['UserAccount'] = relationship('UserAccount', foreign_keys=[enrolled_by_user_id])
    enrolled_device: Mapped[Optional['Device']] = relationship('Device')
    reviewed_by_user: Mapped[Optional['UserAccount']] = relationship('UserAccount', foreign_keys=[reviewed_by_user_id])


class RecognitionEvent(Base):
    __tablename__ = 'recognition_event'
    __table_args__ = (
        CheckConstraint("(door_action = 'OPEN'::text) = (result = ANY (ARRAY['MATCH'::text, 'MANUAL_OPEN'::text]))", name='recognition_event_check6'),
        CheckConstraint("(result <> ALL (ARRAY['MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text])) OR performed_by_user_id IS NOT NULL AND reason IS NOT NULL AND length(TRIM(BOTH FROM reason)) > 0", name='recognition_event_check4'),
        CheckConstraint("(result <> ALL (ARRAY['MATCH'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text, 'MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text])) OR snapshot_path IS NULL", name='recognition_event_check3'),
        CheckConstraint("(result <> ALL (ARRAY['MATCH'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text])) OR employee_id IS NOT NULL AND top1_score IS NOT NULL AND threshold_used IS NOT NULL", name='recognition_event_check1'),
        CheckConstraint("(result <> ALL (ARRAY['MATCH'::text, 'UNKNOWN'::text, 'SPOOF'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text])) OR model_id IS NOT NULL AND device_id IS NOT NULL AND n_frames IS NOT NULL", name='recognition_event_check'),
        CheckConstraint("(result <> ALL (ARRAY['UNKNOWN'::text, 'SPOOF'::text])) OR employee_id IS NULL", name='recognition_event_check2'),
        CheckConstraint("door_action = ANY (ARRAY['OPEN'::text, 'NONE'::text])", name='recognition_event_door_action_check'),
        CheckConstraint("result <> 'MANUAL_ATTENDANCE'::text OR employee_id IS NOT NULL", name='recognition_event_check5'),
        CheckConstraint("result = ANY (ARRAY['MATCH'::text, 'UNKNOWN'::text, 'SPOOF'::text, 'DENIED_RULE'::text, 'DENIED_INACTIVE'::text, 'MANUAL_OPEN'::text, 'MANUAL_ATTENDANCE'::text])", name='recognition_event_result_check'),
        CheckConstraint("threshold_level = ANY (ARRAY['DEFAULT_VAL'::text, 'STRICT_TEST'::text, 'CUSTOM'::text])", name='recognition_event_threshold_level_check'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='recognition_event_company_id_fkey'),
        ForeignKeyConstraint(['device_id'], ['device.id'], name='recognition_event_device_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='recognition_event_employee_id_fkey'),
        ForeignKeyConstraint(['gate_id'], ['gate.id'], name='recognition_event_gate_id_fkey'),
        ForeignKeyConstraint(['model_id'], ['recognition_model.id'], name='recognition_event_model_id_fkey'),
        ForeignKeyConstraint(['performed_by_user_id'], ['user_account.id'], name='recognition_event_performed_by_user_id_fkey'),
        PrimaryKeyConstraint('id', name='recognition_event_pkey'),
        Index('ix_event_employee_time', 'employee_id', text('occurred_at DESC'), postgresql_where=text('(employee_id IS NOT NULL)')),
        Index('ix_event_gate_time', 'gate_id', text('occurred_at DESC')),
        Index('ix_event_manual_by', 'performed_by_user_id', text('occurred_at DESC'), postgresql_where=text("(result = 'MANUAL_ATTENDANCE'::text)")),
        Index('ix_event_result_time', 'company_id', 'result', text('occurred_at DESC'))
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    gate_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    door_action: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'NONE'::text"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    top1_score: Mapped[Optional[float]] = mapped_column(REAL)
    threshold_used: Mapped[Optional[float]] = mapped_column(REAL)
    threshold_level: Mapped[Optional[str]] = mapped_column(Text)
    p_live_min: Mapped[Optional[float]] = mapped_column(REAL)
    n_frames: Mapped[Optional[int]] = mapped_column(SmallInteger)
    snapshot_path: Mapped[Optional[str]] = mapped_column(Text)
    performed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    reason: Mapped[Optional[str]] = mapped_column(Text)

    company: Mapped['Company'] = relationship('Company')
    device: Mapped[Optional['Device']] = relationship('Device')
    employee: Mapped[Optional['Employee']] = relationship('Employee')
    gate: Mapped['Gate'] = relationship('Gate')
    model: Mapped[Optional['RecognitionModel']] = relationship('RecognitionModel')
    performed_by_user: Mapped[Optional['UserAccount']] = relationship('UserAccount')


class AttendanceDay(Base):
    __tablename__ = 'attendance_day'
    __table_args__ = (
        CheckConstraint("(status <> ALL (ARRAY['IN_PROGRESS'::text, 'MISSING_OUT'::text])) OR check_in_at IS NOT NULL", name='attendance_day_check4'),
        CheckConstraint("(status <> ALL (ARRAY['NORMAL'::text, 'LATE'::text, 'EARLY'::text, 'LATE_EARLY'::text])) OR check_out_at IS NOT NULL", name='attendance_day_check3'),
        CheckConstraint("NOT suspect_forgot_out OR status = 'MISSING_OUT'::text", name='attendance_day_check2'),
        CheckConstraint('check_out_at IS NULL OR check_in_at IS NOT NULL AND check_out_at >= check_in_at', name='attendance_day_check'),
        CheckConstraint('early_min >= 0', name='attendance_day_early_min_check'),
        CheckConstraint('late_min >= 0', name='attendance_day_late_min_check'),
        CheckConstraint("source <> 'MANUAL'::text OR edited_by_user_id IS NOT NULL AND edit_reason IS NOT NULL", name='attendance_day_check1'),
        CheckConstraint("source = ANY (ARRAY['AUTO'::text, 'ADJUSTED'::text, 'MANUAL'::text])", name='attendance_day_source_check'),
        CheckConstraint("status <> 'WAITING_IN'::text OR check_in_at IS NULL AND NOT finalized", name='attendance_day_check5'),
        CheckConstraint("status = ANY (ARRAY['HOLIDAY'::text, 'LEAVE'::text, 'OFF'::text, 'NOT_STARTED'::text, 'WAITING_IN'::text, 'IN_PROGRESS'::text, 'ABSENT'::text, 'MISSING_OUT'::text, 'NORMAL'::text, 'LATE'::text, 'EARLY'::text, 'LATE_EARLY'::text])", name='attendance_day_status_check'),
        CheckConstraint('worked_min >= 0', name='attendance_day_worked_min_check'),
        ForeignKeyConstraint(['check_in_event_id'], ['recognition_event.id'], name='attendance_day_check_in_event_id_fkey'),
        ForeignKeyConstraint(['check_out_event_id'], ['recognition_event.id'], name='attendance_day_check_out_event_id_fkey'),
        ForeignKeyConstraint(['company_id'], ['company.id'], name='attendance_day_company_id_fkey'),
        ForeignKeyConstraint(['edited_by_user_id'], ['user_account.id'], name='attendance_day_edited_by_user_id_fkey'),
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='attendance_day_employee_id_fkey'),
        ForeignKeyConstraint(['shift_id'], ['shift.id'], name='attendance_day_shift_id_fkey'),
        PrimaryKeyConstraint('id', name='attendance_day_pkey'),
        UniqueConstraint('employee_id', 'work_date', name='attendance_day_employee_id_work_date_key'),
        Index('ix_attendance_company_date', 'company_id', 'work_date')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    company_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    work_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    suspect_forgot_out: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    late_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    early_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    worked_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text('0'))
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'AUTO'::text"))
    finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    shift_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    check_in_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    check_out_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    check_in_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    check_out_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    edited_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    edit_reason: Mapped[Optional[str]] = mapped_column(Text)

    check_in_event: Mapped[Optional['RecognitionEvent']] = relationship('RecognitionEvent', foreign_keys=[check_in_event_id])
    check_out_event: Mapped[Optional['RecognitionEvent']] = relationship('RecognitionEvent', foreign_keys=[check_out_event_id])
    company: Mapped['Company'] = relationship('Company')
    edited_by_user: Mapped[Optional['UserAccount']] = relationship('UserAccount')
    employee: Mapped['Employee'] = relationship('Employee')
    shift: Mapped[Optional['Shift']] = relationship('Shift')


class EventHandling(Base):
    __tablename__ = 'event_handling'
    __table_args__ = (
        CheckConstraint("(status = 'IS_EMPLOYEE'::text) = (linked_employee_id IS NOT NULL)", name='event_handling_check'),
        CheckConstraint("status = ANY (ARRAY['RESOLVED'::text, 'FALSE_ALARM'::text, 'IS_EMPLOYEE'::text])", name='event_handling_status_check'),
        ForeignKeyConstraint(['event_id'], ['recognition_event.id'], name='event_handling_event_id_fkey'),
        ForeignKeyConstraint(['handled_by_user_id'], ['user_account.id'], name='event_handling_handled_by_user_id_fkey'),
        ForeignKeyConstraint(['linked_employee_id'], ['employee.id'], name='event_handling_linked_employee_id_fkey'),
        PrimaryKeyConstraint('event_id', name='event_handling_pkey'),
        Index('ix_event_handling_linked', 'linked_employee_id', postgresql_where=text('(linked_employee_id IS NOT NULL)'))
    )

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    handled_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    handled_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    linked_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    note: Mapped[Optional[str]] = mapped_column(Text)

    event: Mapped['RecognitionEvent'] = relationship('RecognitionEvent')
    handled_by_user: Mapped['UserAccount'] = relationship('UserAccount')
    linked_employee: Mapped[Optional['Employee']] = relationship('Employee')


class FaceSample(Base):
    __tablename__ = 'face_sample'
    __table_args__ = (
        ForeignKeyConstraint(['profile_id'], ['face_profile.id'], ondelete='CASCADE', name='face_sample_profile_id_fkey'),
        PrimaryKeyConstraint('id', name='face_sample_pkey'),
        Index('ix_face_sample_profile', 'profile_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    det_score: Mapped[float] = mapped_column(REAL, nullable=False)
    yaw_ratio: Mapped[float] = mapped_column(REAL, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    p_live: Mapped[Optional[float]] = mapped_column(REAL)

    profile: Mapped['FaceProfile'] = relationship('FaceProfile')


class FaceTemplate(Base):
    __tablename__ = 'face_template'
    __table_args__ = (
        CheckConstraint('array_ndims(vector) = 1 AND array_length(vector, 1) = 512', name='face_template_vector_check'),
        CheckConstraint('n_samples > 0', name='face_template_n_samples_check'),
        ForeignKeyConstraint(['model_id'], ['recognition_model.id'], name='face_template_model_id_fkey'),
        ForeignKeyConstraint(['profile_id'], ['face_profile.id'], ondelete='CASCADE', name='face_template_profile_id_fkey'),
        PrimaryKeyConstraint('profile_id', 'model_id', name='face_template_pkey')
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    model_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    vector: Mapped[list[float]] = mapped_column(ARRAY(REAL()), nullable=False)
    n_samples: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    model: Mapped['RecognitionModel'] = relationship('RecognitionModel')
    profile: Mapped['FaceProfile'] = relationship('FaceProfile')


class FaceEmbedding(Base):
    __tablename__ = 'face_embedding'
    __table_args__ = (
        CheckConstraint('array_ndims(vector) = 1 AND array_length(vector, 1) = 512', name='face_embedding_vector_check'),
        ForeignKeyConstraint(['model_id'], ['recognition_model.id'], name='face_embedding_model_id_fkey'),
        ForeignKeyConstraint(['sample_id'], ['face_sample.id'], ondelete='CASCADE', name='face_embedding_sample_id_fkey'),
        PrimaryKeyConstraint('sample_id', 'model_id', name='face_embedding_pkey')
    )

    sample_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    model_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    vector: Mapped[list[float]] = mapped_column(ARRAY(REAL()), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    model: Mapped['RecognitionModel'] = relationship('RecognitionModel')
    sample: Mapped['FaceSample'] = relationship('FaceSample')
