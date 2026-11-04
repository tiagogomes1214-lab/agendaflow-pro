from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Appointment, Service, Staff, TimeBlock, WorkHour
from app.scheduling import slots_for_day

TZ = ZoneInfo('America/Sao_Paulo')


def create_context():
    engine = create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


def test_break_and_staff_schedule_and_block():
    engine = create_context()
    day = date(2027,1,4) # segunda
    now = datetime(2027,1,3,8,tzinfo=TZ).astimezone(timezone.utc)
    with Session(engine) as db:
        s = Service(name='Corte',description='',duration_minutes=60,price_cents=5000)
        p = Staff(name='Profissional',title='Cabelo')
        db.add_all([s,p]);db.flush()
        db.add(WorkHour(staff_id=None,weekday=0,enabled=True,opens_at=time(8),closes_at=time(20)))
        db.add(WorkHour(staff_id=p.id,weekday=0,enabled=True,opens_at=time(10),closes_at=time(17),break_start=time(12),break_end=time(13)))
        db.commit()
        valid = {x.strftime('%H:%M') for x in slots_for_day(db,s,p,day,now)}
        assert '09:00' not in valid
        assert '10:00' in valid
        assert '11:30' not in valid
        assert '12:00' not in valid
        assert '13:00' in valid
        assert '16:00' in valid
        assert '16:15' not in valid
        db.add(TimeBlock(staff_id=p.id,start_at=datetime(2027,1,4,13,tzinfo=TZ).astimezone(timezone.utc),
                         end_at=datetime(2027,1,4,14,tzinfo=TZ).astimezone(timezone.utc),reason='Folga'))
        db.commit()
        valid = {x.strftime('%H:%M') for x in slots_for_day(db,s,p,day,now)}
        assert '13:00' not in valid
        assert '14:00' in valid


def test_cancelled_appointment_releases_slot():
    engine = create_context()
    day = date(2027,1,5)
    now = datetime(2027,1,4,8,tzinfo=TZ).astimezone(timezone.utc)
    with Session(engine) as db:
        s = Service(name='Escova',description='',duration_minutes=45,price_cents=5000)
        p = Staff(name='Pessoa',title='Profissional')
        db.add_all([s,p]);db.flush()
        start = datetime(2027,1,5,10,tzinfo=TZ).astimezone(timezone.utc)
        a=Appointment(service_id=s.id,staff_id=p.id,customer_name='Cliente',customer_email='teste@example.com',
                      customer_phone='11999999999',start_at=start,end_at=start+timedelta(minutes=45),status='confirmed')
        db.add(a);db.commit()
        valid = {x.strftime('%H:%M') for x in slots_for_day(db,s,p,day,now)}
        assert '10:00' not in valid
        a.status='cancelled';db.commit()
        valid = {x.strftime('%H:%M') for x in slots_for_day(db,s,p,day,now)}
        assert '10:00' in valid
