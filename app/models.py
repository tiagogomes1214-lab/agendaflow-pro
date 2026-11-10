from datetime import datetime, time, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)

class Admin(Base):
    __tablename__ = 'admins'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))

class Service(Base):
    __tablename__ = 'services'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), default='')
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[str] = mapped_column(String(7), default='#3B9A87')

class Staff(Base):
    __tablename__ = 'staff'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100), default='Profissional')
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Appointment(Base):
    __tablename__ = 'appointments'
    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id', ondelete='RESTRICT'), index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey('staff.id', ondelete='RESTRICT'), index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_email: Mapped[str] = mapped_column(String(255))
    customer_phone: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str] = mapped_column(Text, default='')
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default='confirmed', index=True)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    service: Mapped[Service] = relationship()
    staff: Mapped[Staff] = relationship()

class WorkHour(Base):
    __tablename__ = 'work_hours'
    __table_args__ = (UniqueConstraint('staff_id', 'weekday', name='uq_work_hours_staff_day'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey('staff.id', ondelete='CASCADE'), nullable=True, index=True)
    weekday: Mapped[int] = mapped_column(Integer) # segunda=0
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    opens_at: Mapped[time] = mapped_column(Time)
    closes_at: Mapped[time] = mapped_column(Time)
    break_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    break_end: Mapped[time | None] = mapped_column(Time, nullable=True)

class TimeBlock(Base):
    __tablename__ = 'time_blocks'
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey('staff.id', ondelete='CASCADE'), nullable=True, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(120), default='Indisponível')

class ClientAccess(Base):
    __tablename__ = 'client_access'
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey('appointments.id', ondelete='CASCADE'), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    appointment: Mapped[Appointment] = relationship()

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey('appointments.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    channel: Mapped[str] = mapped_column(String(20))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(24), default='queued', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str] = mapped_column(String(255), default='')
    appointment: Mapped[Appointment] = relationship()
