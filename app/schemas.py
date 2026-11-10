from datetime import datetime, time
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class BookingInput(BaseModel):
    service_id: int = Field(gt=0)
    staff_id: int = Field(gt=0)
    start_at: datetime
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=8, max_length=30)
    notes: str = Field(default='', max_length=500)

    @field_validator('start_at')
    @classmethod
    def timezone_required(cls, v):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError('Informe o fuso horário')
        return v

    @field_validator('customer_name')
    @classmethod
    def name_required(cls, v):
        if not v.strip(): raise ValueError('Informe seu nome')
        return v.strip()

    @field_validator('customer_phone')
    @classmethod
    def phone_required(cls, v):
        digits = ''.join(c for c in v if c.isdigit())
        if not 10 <= len(digits) <= 13: raise ValueError('Informe um telefone com DDD')
        return v.strip()

class StatusInput(BaseModel):
    status: Literal['confirmed','cancelled','completed']

class ServiceInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default='', max_length=255)
    duration_minutes: int = Field(ge=15, le=480, multiple_of=15)
    price_cents: int = Field(ge=0, le=100_000_000)
    color: str = Field(default='#3B9A87', pattern=r'^#[0-9A-Fa-f]{6}$')
    active: bool = True

class StaffInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    title: str = Field(default='Profissional', max_length=100)
    active: bool = True

class WorkHourInput(BaseModel):
    staff_id: int | None = Field(default=None, gt=0)
    weekday: int = Field(ge=0, le=6)
    enabled: bool = True
    opens_at: time
    closes_at: time
    break_start: time | None = None
    break_end: time | None = None

    @model_validator(mode='after')
    def validate_hours(self):
        if self.opens_at >= self.closes_at:
            raise ValueError('O horário de abertura deve ser anterior ao fechamento')
        if (self.break_start is None) != (self.break_end is None):
            raise ValueError('Preencha início e fim do intervalo')
        if self.break_start and not (self.opens_at <= self.break_start < self.break_end <= self.closes_at):
            raise ValueError('Intervalo precisa estar dentro do expediente')
        return self

class BlockInput(BaseModel):
    staff_id: int | None = Field(default=None, gt=0)
    start_at: datetime
    end_at: datetime
    reason: str = Field(default='Indisponível', max_length=120)

    @model_validator(mode='after')
    def dates_valid(self):
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError('Datas precisam incluir fuso horário')
        if self.end_at <= self.start_at:
            raise ValueError('O fim deve ser posterior ao início')
        if (self.end_at - self.start_at).days > 30:
            raise ValueError('Bloqueios de até 30 dias por vez')
        return self

class RescheduleInput(BaseModel):
    start_at: datetime
    @field_validator('start_at')
    @classmethod
    def timezone_required(cls, v):
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError('Informe o fuso horário')
        return v
