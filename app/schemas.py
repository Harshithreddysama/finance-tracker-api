from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from app.models.transaction import TransactionType


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if not v.isalnum():
            raise ValueError("Username must contain only letters and numbers.")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    category: str
    date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Category cannot be empty.")
        return v.strip().title()


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return round(v, 2) if v else v


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: float
    type: TransactionType
    category: str
    date: datetime
    notes: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    transactions: list[TransactionResponse]


class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int


class MonthlyTotals(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    current_balance: float
    total_transactions: int
    income_by_category: list[CategoryBreakdown]
    expense_by_category: list[CategoryBreakdown]
    monthly_totals: list[MonthlyTotals]
    recent_transactions: list[TransactionResponse]
