"""Fila leve de notificações. Execute uma instância (serviço 'worker' no Compose)."""
import json
import os
import smtplib
import ssl
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.request import Request, urlopen

from sqlalchemy import select
from .database import SessionLocal
from .models import Notification
from .scheduling import get_timezone


def send_email(appointment, kind):
    host = os.getenv('SMTP_HOST', '')
    user = os.getenv('SMTP_USER', '')
    password = os.getenv('SMTP_PASSWORD', '')
    sender = os.getenv('SMTP_FROM', '')
    if not all([host, user, password, sender]):
        return False
    labels = {'confirmation': 'Agendamento confirmado', 'reminder':'Lembrete de agendamento',
              'reschedule':'Agendamento reagendado', 'cancellation':'Agendamento cancelado'}
    date = appointment.start_at.astimezone(get_timezone()).strftime('%d/%m/%Y às %H:%M')
    msg = EmailMessage()
    msg['From'], msg['To'] = sender, appointment.customer_email
    msg['Subject'] = f'AgendaFlow | {labels.get(kind,"Atualização da reserva")}'
    msg.set_content(f'Olá, {appointment.customer_name}!\n\n{labels.get(kind,"Atualização da reserva")}\n'
                    f'Serviço: {appointment.service.name}\nProfissional: {appointment.staff.name}\n'
                    f'Horário: {date}\n\nEntre em contato com o estabelecimento para dúvidas.')
    port = int(os.getenv('SMTP_PORT', '587'))
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=12, context=ssl.create_default_context()) as smtp:
            smtp.login(user,password); smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=12) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user,password); smtp.send_message(msg)
    return True


def send_whatsapp(appointment, kind):
    token = os.getenv('WA_TOKEN','')
    phone_id = os.getenv('WA_PHONE_NUMBER_ID','')
    templates = {'confirmation':'WA_TEMPLATE_CONFIRMATION', 'reminder':'WA_TEMPLATE_REMINDER',
                 'reschedule':'WA_TEMPLATE_RESCHEDULE', 'cancellation':'WA_TEMPLATE_CANCELLATION'}
    template = os.getenv(templates.get(kind,''),'')
    if not all([token,phone_id,template]): return False
    # Use apenas modelos aprovados no WhatsApp Business Cloud API.
    number = ''.join(c for c in appointment.customer_phone if c.isdigit())
    if len(number) in (10, 11): number = '55' + number
    day = appointment.start_at.astimezone(get_timezone()).strftime('%d/%m às %H:%M')
    body = {'messaging_product':'whatsapp', 'to':number, 'type':'template',
            'template':{'name':template,'language':{'code':'pt_BR'},'components':[{'type':'body','parameters':[
                {'type':'text','text':appointment.customer_name},
                {'type':'text','text':appointment.service.name},
                {'type':'text','text':day},
            ]}]}}
    api_version = os.getenv('WA_API_VERSION','v26.0')
    req=Request(f'https://graph.facebook.com/{api_version}/{phone_id}/messages',
                data=json.dumps(body).encode(),
                headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'}, method='POST')
    with urlopen(req,timeout=12) as response:
        if response.status not in (200,201): raise RuntimeError('WhatsApp não confirmou entrega')
    return True


def process_batch(limit=15):
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        stmt = select(Notification).where(Notification.status=='queued', Notification.scheduled_at <= now).order_by(Notification.id).limit(limit)
        if db.bind.dialect.name == 'postgresql': stmt = stmt.with_for_update(skip_locked=True)
        for n in db.scalars(stmt).all():
            try:
                a = n.appointment
                if n.kind == 'reminder' and (a.status != 'confirmed' or (a.start_at.replace(tzinfo=timezone.utc) if a.start_at.tzinfo is None else a.start_at) <= now):
                    n.status='cancelled'
                else:
                    configured = send_email(a,n.kind) if n.channel=='email' else send_whatsapp(a,n.kind)
                    n.status = 'sent' if configured else 'skipped'
                    if configured: n.sent_at=now
            except Exception as exc:
                n.attempts += 1
                n.status = 'failed' if n.attempts >= 3 else 'queued'
                n.scheduled_at = now + timedelta(minutes=min(30,5*n.attempts))
                n.error = type(exc).__name__[:80]  # nunca registrar token, email ou resposta sensível
            db.flush()
        db.commit()


if __name__ == '__main__':
    while True:
        try: process_batch()
        except Exception as exc: print('Worker: falha temporária',type(exc).__name__,flush=True)
        time.sleep(30)
