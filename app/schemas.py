from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional

from app.calculator import OperationType


# ── User schemas ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(default=None, max_length=500)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @model_validator(mode="after")
    def passwords_must_differ(self):
        if self.current_password == self.new_password:
            raise ValueError("New password must differ from the current password")
        return self


class RegisterResponse(BaseModel):
    token: str
    message: str
    user: UserRead


class LoginResponse(BaseModel):
    token: str
    message: str
    user: UserRead


# ── Calculation schemas ────────────────────────────────────────────────────

class CalculationCreate(BaseModel):
    a: float
    b: float
    type: OperationType
    user_id: Optional[int] = None

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == OperationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        if self.type == OperationType.Modulus and self.b == 0:
            raise ValueError("Modulus by zero is not allowed")
        return self


class CalculationUpdate(BaseModel):
    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[OperationType] = None

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == OperationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        if self.type == OperationType.Modulus and self.b == 0:
            raise ValueError("Modulus by zero is not allowed")
        return self


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: OperationType
    result: float
    timestamp: Optional[datetime] = None
    user_id: int

    model_config = {"from_attributes": True}


class CalculationWithUser(BaseModel):
    username: str
    a: float
    b: float
    type: str
    result: float


# ── Report schemas ─────────────────────────────────────────────────────────

class ReportSummary(BaseModel):
    total_calculations: int
    most_used_operation: Optional[str]
    average_result: Optional[float]
    last_calculation: Optional[CalculationRead]
    operation_counts: dict
