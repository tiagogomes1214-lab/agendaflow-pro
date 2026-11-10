from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Appointment, Service, Staff, WorkHour, TimeBlock

SLOT_STEP = timedelta(minutes=15)
MAX_ADVANCE_DAYS = 90

def get_timezone() -> ZoneInfo:
    import os
    return ZoneInfo(os.getenv('BUSINESS_TIMEZONE', 'America/Sao_Paulo'))

def interval_overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and a_end > b_start

def schedule_for_day(db: Session, staff_id: int, day: date):
    # Horário específico do funcionário prevalece; caso contrário, usa o global.
    rows = db.scalars(select(WorkHour).where(WorkHour.weekday == day.weekday(),
                                             (WorkHour.staff_id == staff_id) | WorkHour.staff_id.is_(None))).all()
    chosen = next((r for r in rows if r.staff_id == staff_id), None)
    if chosen is None: chosen = next((r for r in rows if r.staff_id is None), None)
    if chosen: return chosen
    # Compatibilidade com ambientes antigos antes da primeira inicialização do novo seed
    if day.weekday() == 6: return None
    return WorkHour(staff_id=None, weekday=day.weekday(), enabled=True,
                    opens_at=time(9), closes_at=time(18))

def slots_for_day(db: Session, service: Service, staff: Staff, day: date,
                  now: datetime | None = None, exclude_appointment_id: int | None = None) -> list[datetime]:
    tz = get_timezone()
    current = (now or datetime.now(timezone.utc)).astimezone(tz)
    if not service.active or not staff.active:
        return []
    if day < current.date() or day > current.date() + timedelta(days=MAX_ADVANCE_DAYS):
        return []
    hours = schedule_for_day(db, staff.id, day)
    if not hours or not hours.enabled:
        return []
    start_day = datetime.combine(day, time.min, tzinfo=tz)
    end_day = start_day + timedelta(days=1)
    lower = start_day.astimezone(timezone.utc)
    upper = end_day.astimezone(timezone.utc)
    query = select(Appointment).where(Appointment.staff_id == staff.id,
                   Appointment.status != 'cancelled', Appointment.start_at < upper,
                   Appointment.end_at > lower)
    if exclude_appointment_id:
        query = query.where(Appointment.id != exclude_appointment_id)
    busy = db.scalars(query).all()
    blocks = db.scalars(select(TimeBlock).where(
        (TimeBlock.staff_id == staff.id) | TimeBlock.staff_id.is_(None),
        TimeBlock.start_at < upper, TimeBlock.end_at > lower)).all()
    cursor = datetime.combine(day, hours.opens_at, tzinfo=tz)
    close = datetime.combine(day, hours.closes_at, tzinfo=tz)
    br_start = datetime.combine(day, hours.break_start, tzinfo=tz) if hours.break_start else None
    br_end = datetime.combine(day, hours.break_end, tzinfo=tz) if hours.break_end else None
    duration = timedelta(minutes=service.duration_minutes)
    available = []
    while cursor + duration <= close:
        end = cursor + duration
        start_utc, end_utc = cursor.astimezone(timezone.utc), end.astimezone(timezone.utc)
        overlaps_break = br_start and interval_overlap(cursor, end, br_start, br_end)
        if cursor >= current + timedelta(minutes=15) and not overlaps_break and not any(
            interval_overlap(start_utc, end_utc, a.start_at.astimezone(timezone.utc), a.end_at.astimezone(timezone.utc)) for a in busy
        ) and not any(interval_overlap(start_utc, end_utc, b.start_at.astimezone(timezone.utc), b.end_at.astimezone(timezone.utc)) for b in blocks):
            available.append(cursor)
        cursor += SLOT_STEP
    return available
