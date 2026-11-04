from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Appointment, Service, Staff
from app.scheduling import slots_for_day

TZ = ZoneInfo("America/Sao_Paulo")


def test_slots_avoid_overlap():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    day = date(2027, 1, 4)  # segunda
    now = datetime(2027, 1, 3, 8, tzinfo=TZ).astimezone(timezone.utc)
    with Session(engine) as db:
        service = Service(name="Teste", description="", duration_minutes=60, price_cents=5000)
        professional = Staff(name="Pessoa", title="Profissional")
        db.add_all([service, professional]); db.commit()
        db.refresh(service); db.refresh(professional)
        start = datetime(2027, 1, 4, 10, tzinfo=TZ).astimezone(timezone.utc)
        db.add(Appointment(service_id=service.id, staff_id=professional.id,
                           customer_name="Exemplo", customer_email="exemplo@teste.com", customer_phone="11999999999",
                           start_at=start, end_at=start + timedelta(minutes=60), status="confirmed"))
        db.commit()
        times = [x.strftime("%H:%M") for x in slots_for_day(db, service, professional, day, now)]
        assert "09:00" in times
        assert "09:30" not in times
        assert "10:00" not in times
        assert "10:30" not in times
        assert "11:00" in times


def test_sunday_is_closed():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        service = Service(id=1, name="Teste", description="", duration_minutes=45, price_cents=2000)
        professional = Staff(id=1, name="Pessoa", title="Profissional")
        assert slots_for_day(db, service, professional, date(2027, 1, 3), datetime(2027, 1, 2, tzinfo=TZ)) == []
