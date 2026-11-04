"""AgendaFlow Pro: API para reservas, gestão de equipe, expediente e relatórios."""
import hashlib
import os
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db, SessionLocal
from .models import Admin, Appointment, ClientAccess, Notification, Service, Staff, TimeBlock, WorkHour
from .scheduling import get_timezone, slots_for_day, schedule_for_day
from .schemas import (BookingInput, BlockInput, LoginInput, RescheduleInput, ServiceInput,
                      StaffInput, StatusInput, WorkHourInput)
from .security import create_token, hash_password, require_admin, secret_key, verify_password


def initialize_database():
    secret_key()
    email = os.getenv('ADMIN_EMAIL', '').strip().lower()
    password = os.getenv('ADMIN_PASSWORD', '')
    if not email or len(password) < 12 or 'CHANGE_ME' in password:
        raise RuntimeError('Configure ADMIN_EMAIL e ADMIN_PASSWORD (mín. 12 caracteres) no .env')
    if engine.dialect.name == 'postgresql':
        with engine.begin() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS btree_gist'))
    Base.metadata.create_all(bind=engine)
    # Migração incremental segura para o banco da versão 1.0 existente.
    # Nunca apaga as reservas nem recria o volume do Docker.
    with engine.begin() as conn:
        if engine.dialect.name == 'postgresql':
            conn.execute(text("ALTER TABLE services ADD COLUMN IF NOT EXISTS color VARCHAR(7) NOT NULL DEFAULT '#3B9A87'"))
            conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS price_cents INTEGER NOT NULL DEFAULT 0"))
            conn.execute(text("""UPDATE appointments SET price_cents = services.price_cents
                FROM services WHERE appointments.service_id=services.id AND appointments.price_cents=0"""))
            conn.execute(text("""
                DO $$ BEGIN
                  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'appointments_staff_no_overlap') THEN
                    ALTER TABLE appointments ADD CONSTRAINT appointments_staff_no_overlap
                    EXCLUDE USING gist (staff_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&)
                    WHERE (status <> 'cancelled');
                  END IF;
                END $$;
            """))
        else:
            cols = [r[1] for r in conn.execute(text('PRAGMA table_info(services)'))]
            if 'color' not in cols:
                conn.execute(text("ALTER TABLE services ADD COLUMN color VARCHAR(7) NOT NULL DEFAULT '#3B9A87'"))
            cols = [r[1] for r in conn.execute(text('PRAGMA table_info(appointments)'))]
            if 'price_cents' not in cols:
                conn.execute(text('ALTER TABLE appointments ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0'))
                conn.execute(text('UPDATE appointments SET price_cents = (SELECT price_cents FROM services WHERE services.id = appointments.service_id)'))
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Admin)) == 0:
            db.add(Admin(email=email, password_hash=hash_password(password)))
        if db.scalar(select(func.count()).select_from(Service)) == 0:
            db.add_all([
                Service(name='Corte de cabelo', description='Um corte para renovar seu visual.', duration_minutes=45, price_cents=6500, color='#2DB6A3'),
                Service(name='Barba & acabamento', description='Barba com atenção aos detalhes.', duration_minutes=30, price_cents=4000, color='#818CF8'),
                Service(name='Escova & finalização', description='Finalização para cada ocasião.', duration_minutes=60, price_cents=8500, color='#F2AE68'),
                Service(name='Hidratação', description='Tratamento personalizado.', duration_minutes=60, price_cents=11000, color='#70A6DA'),
            ])
        if db.scalar(select(func.count()).select_from(Staff)) == 0:
            db.add_all([Staff(name='Mariana Costa', title='Especialista em beleza'), Staff(name='Rafael Lima', title='Profissional de estilo')])
        if db.scalar(select(func.count()).select_from(WorkHour).where(WorkHour.staff_id.is_(None))) == 0:
            for weekday in range(7):
                db.add(WorkHour(weekday=weekday, staff_id=None, enabled=weekday!=6,
                                opens_at=time(9), closes_at=time(18)))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(title='AgendaFlow Pro API', version='2.0.0', lifespan=lifespan)
allowed_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',') if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins,
                   allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'PUT'],
                   allow_headers=['Authorization', 'Content-Type', 'X-Booking-Token'])


def appt_json(a: Appointment):
    return {'id': a.id, 'customer_name': a.customer_name, 'customer_email': a.customer_email,
            'customer_phone': a.customer_phone, 'notes': a.notes, 'service': a.service.name,
            'service_id': a.service_id, 'service_color': a.service.color,
            'professional': a.staff.name, 'staff_id': a.staff_id,
            'start_at': a.start_at, 'end_at': a.end_at, 'status': a.status,
            'price_cents': a.price_cents}


def public_appt_json(a: Appointment):
    return {'id': a.id, 'service': a.service.name, 'professional': a.staff.name,
            'start_at': a.start_at, 'end_at': a.end_at, 'status': a.status,
            'price_cents': a.price_cents, 'customer_name': a.customer_name}


def as_utc(value: datetime):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def slot_is_valid(db: Session, service: Service, staff: Staff, start: datetime, exclude_id=None):
    start = start.astimezone(timezone.utc)
    day = start.astimezone(get_timezone()).date()
    return any(s.astimezone(timezone.utc) == start for s in slots_for_day(db, service, staff, day, exclude_appointment_id=exclude_id))


def queue_messages(db: Session, a: Appointment, kind: str):
    now = datetime.now(timezone.utc)
    for channel in ['email', 'whatsapp']:
        db.add(Notification(appointment_id=a.id, kind=kind, channel=channel, scheduled_at=now))
    if kind == 'confirmation':
        # Apenas agendamentos com antecedência maior do que 90 minutos recebem lembrete.
        lead = as_utc(a.start_at) - now
        if lead > timedelta(minutes=90):
            when = max(now, as_utc(a.start_at) - timedelta(hours=24 if lead > timedelta(hours=25) else 1))
            for channel in ['email', 'whatsapp']:
                db.add(Notification(appointment_id=a.id, kind='reminder', channel=channel, scheduled_at=when))


def get_client_booking(db: Session, token: str | None):
    if not token or len(token) > 256:
        raise HTTPException(401, 'Link de acesso inválido')
    digest = hashlib.sha256(token.encode()).hexdigest()
    access = db.scalar(select(ClientAccess).where(ClientAccess.token_hash == digest))
    if not access:
        raise HTTPException(401, 'Link de acesso inválido')
    return db.get(Appointment, access.appointment_id)


@app.get('/health')
def health():
    return {'status':'ok', 'version':'2.0.0'}

@app.get('/public/info')
def public_info(db: Session = Depends(get_db)):
    hours = db.scalars(select(WorkHour).where(WorkHour.staff_id.is_(None)).order_by(WorkHour.weekday)).all()
    return {'business_name':os.getenv('BUSINESS_NAME','Studio Aurora'),
            'timezone':str(get_timezone()), 'hours':[hour_json(h) for h in hours]}

@app.get('/public/services')
def list_services(db: Session = Depends(get_db)):
    return db.scalars(select(Service).where(Service.active.is_(True)).order_by(Service.id)).all()

@app.get('/public/staff')
def list_staff(db: Session = Depends(get_db)):
    return db.scalars(select(Staff).where(Staff.active.is_(True)).order_by(Staff.id)).all()

@app.get('/public/slots')
def get_slots(service_id: int, staff_id: int, day: date, db: Session = Depends(get_db)):
    service, staff = db.get(Service,service_id), db.get(Staff,staff_id)
    if not service or not staff or not service.active or not staff.active:
        raise HTTPException(404, 'Serviço ou profissional indisponível')
    return {'slots': [x.isoformat() for x in slots_for_day(db,service,staff,day)]}

@app.post('/public/appointments', status_code=status.HTTP_201_CREATED)
def make_appointment(data: BookingInput, db: Session = Depends(get_db)):
    service, staff = db.get(Service,data.service_id), db.get(Staff,data.staff_id)
    if not service or not staff or not service.active or not staff.active:
        raise HTTPException(404, 'Serviço ou profissional indisponível')
    start = data.start_at.astimezone(timezone.utc)
    if not slot_is_valid(db,service,staff,start):
        raise HTTPException(409, 'Horário indisponível. Selecione outro horário.')
    a = Appointment(service_id=service.id,staff_id=staff.id,customer_name=data.customer_name,
                    customer_email=str(data.customer_email).lower(),customer_phone=data.customer_phone,
                    notes=data.notes.strip(), start_at=start,
                    end_at=start+timedelta(minutes=service.duration_minutes), price_cents=service.price_cents)
    db.add(a)
    try:
        db.flush()
        token = secrets.token_urlsafe(36)
        db.add(ClientAccess(appointment_id=a.id, token_hash=hashlib.sha256(token.encode()).hexdigest()))
        queue_messages(db,a,'confirmation')
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Horário acabou de ser reservado. Escolha outro.') from None
    db.refresh(a)
    return {**public_appt_json(a), 'access_token':token}

@app.get('/public/manage')
def client_manage(x_booking_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    return public_appt_json(get_client_booking(db,x_booking_token))

@app.get('/public/manage/slots')
def client_slots(day: date, x_booking_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    a = get_client_booking(db,x_booking_token)
    if a.status != 'confirmed': return {'slots':[]}
    return {'slots':[s.isoformat() for s in slots_for_day(db,a.service,a.staff,day,exclude_appointment_id=a.id)]}

@app.patch('/public/manage')
def client_reschedule(data: RescheduleInput, x_booking_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    a = get_client_booking(db,x_booking_token)
    if a.status != 'confirmed' or as_utc(a.start_at) <= datetime.now(timezone.utc) + timedelta(hours=2):
        raise HTTPException(409, 'Não é possível reagendar este atendimento pela internet')
    start = data.start_at.astimezone(timezone.utc)
    if not slot_is_valid(db,a.service,a.staff,start,exclude_id=a.id):
        raise HTTPException(409, 'Horário não disponível')
    a.start_at, a.end_at = start, start+timedelta(minutes=a.service.duration_minutes)
    db.query(Notification).filter(Notification.appointment_id==a.id,Notification.status=='queued').update({'status':'cancelled'})
    queue_messages(db,a,'reschedule')
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Esse horário foi reservado por outra pessoa') from None
    return public_appt_json(a)

@app.post('/public/manage/cancel')
def client_cancel(x_booking_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    a = get_client_booking(db,x_booking_token)
    if a.status != 'confirmed' or as_utc(a.start_at) <= datetime.now(timezone.utc) + timedelta(hours=2):
        raise HTTPException(409, 'Cancelamento online indisponível para esta reserva')
    a.status = 'cancelled'
    db.query(Notification).filter(Notification.appointment_id==a.id,Notification.status=='queued').update({'status':'cancelled'})
    queue_messages(db,a,'cancellation')
    db.commit()
    return public_appt_json(a)

@app.post('/auth/login')
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(Admin).where(Admin.email==str(data.email).lower()))
    if not user or not verify_password(data.password,user.password_hash):
        raise HTTPException(401,'E-mail ou senha incorretos')
    return {'access_token':create_token(user.id),'token_type':'bearer'}

@app.get('/auth/me')
def me(admin: Admin = Depends(require_admin)):
    return {'email':admin.email}

@app.get('/admin/stats')
def stats(db: Session = Depends(get_db), _admin: Admin = Depends(require_admin)):
    appts = db.scalars(select(Appointment)).all()
    now = datetime.now(timezone.utc)
    completed = [a for a in appts if a.status=='completed']
    month = now.astimezone(get_timezone()).strftime('%Y-%m')
    revenue_month = sum(a.price_cents for a in completed if as_utc(a.start_at).astimezone(get_timezone()).strftime('%Y-%m')==month)
    service_counts = {}
    for a in completed:
        label = a.service.name
        service_counts[label] = service_counts.get(label,0)+1
    return {'total':len(appts),'confirmed':sum(a.status=='confirmed' for a in appts),
            'upcoming':sum(a.status=='confirmed' and as_utc(a.start_at) > now for a in appts),
            'completed':len(completed),'cancelled':sum(a.status=='cancelled' for a in appts),
            'revenue_month_cents':revenue_month,
            'revenue_total_cents':sum(a.price_cents for a in completed),
            'top_services':[{'name':name,'count':count} for name,count in sorted(service_counts.items(),key=lambda x:-x[1])[:6]]}

@app.get('/admin/appointments')
def admin_appointments(start_date: date | None = None, end_date: date | None = None,
                       day: date | None = None, limit: int = Query(default=1000, ge=1, le=2000),
                       db: Session=Depends(get_db),_admin: Admin=Depends(require_admin)):
    if day: start_date,end_date=day,day
    stmt = select(Appointment).order_by(Appointment.start_at.desc()).limit(limit)
    tz = get_timezone()
    if start_date: stmt=stmt.where(Appointment.start_at >= datetime.combine(start_date,time.min,tzinfo=tz).astimezone(timezone.utc))
    if end_date: stmt=stmt.where(Appointment.start_at < datetime.combine(end_date+timedelta(days=1),time.min,tzinfo=tz).astimezone(timezone.utc))
    return [appt_json(a) for a in db.scalars(stmt).all()]

@app.patch('/admin/appointments/{appointment_id}')
def change_status(appointment_id: int,data: StatusInput,db: Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    a=db.get(Appointment,appointment_id)
    if not a: raise HTTPException(404,'Agendamento não encontrado')
    if a.status=='cancelled' and data.status!='cancelled':
        raise HTTPException(409,'Agendamento cancelado não pode ser reativado')
    old_status=a.status
    a.status=data.status
    if data.status=='cancelled' and old_status!='cancelled':
        db.query(Notification).filter(Notification.appointment_id==a.id,Notification.status=='queued').update({'status':'cancelled'})
        queue_messages(db,a,'cancellation')
    if data.status=='completed':
        db.query(Notification).filter(Notification.appointment_id==a.id,Notification.status=='queued').update({'status':'cancelled'})
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Conflito ao atualizar agendamento') from None
    return {'id':a.id,'status':a.status}

@app.post('/admin/appointments',status_code=201)
def admin_create_booking(data:BookingInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    return make_appointment(data,db)

@app.get('/admin/services')
def admin_services(db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    return db.scalars(select(Service).order_by(Service.id)).all()

@app.post('/admin/services',status_code=201)
def create_service(data:ServiceInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=Service(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item

@app.put('/admin/services/{item_id}')
def update_service(item_id:int,data:ServiceInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(Service,item_id)
    if not item: raise HTTPException(404,'Serviço não encontrado')
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.commit();db.refresh(item);return item

@app.delete('/admin/services/{item_id}')
def delete_service(item_id:int,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(Service,item_id)
    if not item: raise HTTPException(404,'Serviço não encontrado')
    item.active=False;db.commit()
    return {'ok':True,'message':'Serviço arquivado; histórico preservado'}

@app.get('/admin/staff')
def admin_staff(db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    return db.scalars(select(Staff).order_by(Staff.id)).all()

@app.post('/admin/staff',status_code=201)
def create_staff(data:StaffInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=Staff(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item

@app.put('/admin/staff/{item_id}')
def update_staff(item_id:int,data:StaffInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(Staff,item_id)
    if not item: raise HTTPException(404,'Profissional não encontrado')
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.commit();db.refresh(item);return item

@app.delete('/admin/staff/{item_id}')
def delete_staff(item_id:int,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(Staff,item_id)
    if not item: raise HTTPException(404,'Profissional não encontrado')
    item.active=False;db.commit()
    return {'ok':True,'message':'Profissional arquivado; histórico preservado'}


def hour_json(h:WorkHour):
    return {'id':h.id,'staff_id':h.staff_id,'weekday':h.weekday,'enabled':h.enabled,
            'opens_at':h.opens_at.strftime('%H:%M'),'closes_at':h.closes_at.strftime('%H:%M'),
            'break_start':h.break_start.strftime('%H:%M') if h.break_start else None,
            'break_end':h.break_end.strftime('%H:%M') if h.break_end else None}

@app.get('/admin/hours')
def list_hours(db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    return [hour_json(x) for x in db.scalars(select(WorkHour).order_by(WorkHour.weekday,WorkHour.staff_id)).all()]

@app.put('/admin/hours')
def upsert_hours(data:WorkHourInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    if data.staff_id and not db.get(Staff,data.staff_id): raise HTTPException(404,'Profissional não encontrado')
    query=select(WorkHour).where(WorkHour.weekday==data.weekday)
    query=query.where(WorkHour.staff_id==data.staff_id) if data.staff_id else query.where(WorkHour.staff_id.is_(None))
    item=db.scalar(query)
    if item is None: item=WorkHour();db.add(item)
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.commit();db.refresh(item);return hour_json(item)

@app.delete('/admin/hours/{hour_id}')
def remove_hour_override(hour_id:int,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(WorkHour,hour_id)
    if not item or item.staff_id is None:
        raise HTTPException(400,'Só é possível excluir horários específicos de profissionais')
    db.delete(item);db.commit();return {'ok':True}


def block_json(b:TimeBlock):
    return {'id':b.id,'staff_id':b.staff_id,'start_at':b.start_at,'end_at':b.end_at,'reason':b.reason}

@app.get('/admin/blocks')
def list_blocks(db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    return [block_json(b) for b in db.scalars(select(TimeBlock).order_by(TimeBlock.start_at.desc()).limit(500)).all()]

@app.post('/admin/blocks',status_code=201)
def create_block(data:BlockInput,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    if data.staff_id and not db.get(Staff,data.staff_id):raise HTTPException(404,'Profissional não encontrado')
    start,end=data.start_at.astimezone(timezone.utc),data.end_at.astimezone(timezone.utc)
    # O bloqueio não pode invalidar reservas já confirmadas.
    conflict=db.scalar(select(Appointment.id).where(Appointment.status=='confirmed',
                        Appointment.start_at<end,Appointment.end_at>start,
                        ((Appointment.staff_id==data.staff_id) if data.staff_id else text('1=1'))).limit(1))
    if conflict:raise HTTPException(409,'Existem agendamentos confirmados neste período; cancele ou reagende antes')
    item=TimeBlock(staff_id=data.staff_id,start_at=start,end_at=end,reason=data.reason.strip() or 'Indisponível')
    db.add(item);db.commit();db.refresh(item);return block_json(item)

@app.delete('/admin/blocks/{block_id}')
def delete_block(block_id:int,db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    item=db.get(TimeBlock,block_id)
    if not item:raise HTTPException(404,'Bloqueio não encontrado')
    db.delete(item);db.commit();return {'ok':True}

@app.get('/admin/notifications')
def list_notifications(db:Session=Depends(get_db),_admin:Admin=Depends(require_admin)):
    rows=db.scalars(select(Notification).order_by(Notification.id.desc()).limit(100)).all()
    return [{'id':n.id,'kind':n.kind,'channel':n.channel,'status':n.status,
             'scheduled_at':n.scheduled_at,'sent_at':n.sent_at,'attempts':n.attempts,
             'error':n.error, 'appointment_id':n.appointment_id} for n in rows]
