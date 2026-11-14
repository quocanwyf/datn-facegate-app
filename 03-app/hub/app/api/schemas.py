from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from jsonschema import FormatChecker

Role = Literal['OWNER', 'HR', 'MANAGER', 'SECURITY', 'EMPLOYEE']


class LoginRequest(BaseModel):
    email: str = Field(json_schema_extra={'format': 'email'})
    password: str

    @field_validator('email')
    @classmethod
    def email_format(cls, value: str):
        # OpenAPI dùng email cú pháp, không kiểm DNS/reserved TLD: seed là demo.local.
        if not FormatChecker().conforms(value, 'email') or any(char.isspace() for char in value):
            raise ValueError('Email không hợp lệ')
        return value


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class RoleGrant(BaseModel):
    role: Role
    scope_department_id: UUID | None = None


class EmployeeBrief(BaseModel):
    id: UUID
    code: str
    full_name: str
    department_id: UUID
    department_name: str


class UserMe(BaseModel):
    id: UUID
    email: str
    roles: list[RoleGrant]
    employee: EmployeeBrief | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    must_change_password: bool
    user: UserMe


class Health(BaseModel):
    status: Literal['ok', 'degraded']
    db: bool
    gpu: bool
    model_verified: bool
    gallery_size: int
    version: str


class Version(BaseModel):
    version: str
    api: str
