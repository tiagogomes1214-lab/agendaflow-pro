"use client";
import Link from "next/link";
import {FormEvent,useEffect,useMemo,useState} from "react";
import {addDays,BookingSuccess,dateAt,dateLabel,money,PublicInfo,request,Service,showDate,showTime,Staff,today} from "@/lib/api";

const icons=["✦","◈","✳","✧"];
export default function Home(){
  const [services,setServices]=useState<Service[]>([]);
  const [staff,setStaff]=useState<Staff[]>([]);
  const [info,setInfo]=useState<PublicInfo|null>(null);
  const [serviceId,setServiceId]=useState(0);
  const [staffId,setStaffId]=useState(0);
  const [day,setDay]=useState(today());
  const [monthOffset,setMonthOffset]=useState(0);
  const [slots,setSlots]=useState<string[]>([]);
  const [slot,setSlot]=useState("");
  const [name,setName]=useState("");
  const [email,setEmail]=useState("");
  const [phone,setPhone]=useState("");
  const [notes,setNotes]=useState("");
  const [loading,setLoading]=useState(false);
  const [saving,setSaving]=useState(false);
  const [error,setError]=useState("");
  const [success,setSuccess]=useState<BookingSuccess|null>(null);
  const service=services.find(s=>s.id===serviceId);
  const person=staff.find(s=>s.id===staffId);
  const days=useMemo(()=>Array.from({length:7},(_,i)=>addDays(today(),monthOffset*7+i)),[monthOffset]);

  useEffect(()=>{Promise.all([request<Service[]>("/public/services"),request<Staff[]>("/public/staff"),request<PublicInfo>("/public/info")])
    .then(([s,p,b])=>{setServices(s);setStaff(p);setInfo(b);})
    .catch((e:Error)=>setError(e.message));},[]);
  useEffect(()=>{
    setSlot(""); if(!serviceId||!staffId||!day){setSlots([]);return;}
    let ignore=false;setLoading(true);setError("");
    request<{slots:string[]}>(`/public/slots?service_id=${serviceId}&staff_id=${staffId}&day=${day}`)
      .then(data=>{if(!ignore)setSlots(data.slots);})
      .catch((e:Error)=>{if(!ignore)setError(e.message);})
      .finally(()=>{if(!ignore)setLoading(false);});
    return()=>{ignore=true;};
  },[serviceId,staffId,day]);

  async function submit(e:FormEvent){e.preventDefault();if(!slot)return;setSaving(true);setError("");
    try{
      const booking=await request<BookingSuccess>("/public/appointments",{method:"POST",body:JSON.stringify({service_id:serviceId,staff_id:staffId,start_at:slot,customer_name:name,customer_email:email,customer_phone:phone,notes})});
      setSuccess(booking);
    }catch(err){setError(err instanceof Error?err.message:"Falha ao reservar");
      request<{slots:string[]}>(`/public/slots?service_id=${serviceId}&staff_id=${staffId}&day=${day}`).then(data=>setSlots(data.slots)).catch(()=>{});
    }finally{setSaving(false);}
  }
  const publicLink=success && typeof window!=="undefined" ? `${window.location.origin}/minha-reserva#token=${encodeURIComponent(success.access_token)}`:"";
  return <div className="public-root">
    <header className="public-nav wrap"><Link href="/" className="logo"><span className="logo-glyph">✳</span> agenda<span>flow</span><b>.</b></Link><div className="public-nav-actions"><span className="nav-mini">Gestão de tempo simplificada</span><Link href="/admin" className="pill-link">Área do gestor <span>↗</span></Link></div></header>
    <section className="public-hero wrap"><div><span className="tag"><span className="green-dot"/> SEU TEMPO, DO SEU JEITO</span><h1>Um bom momento<br/>começa com um <em>bom horário.</em></h1><p>Escolha o serviço, encontre seu profissional favorito e reserve em poucos cliques. Sem filas, sem complicações.</p><a className="btn solid" href="#reservar">Agendar agora <span>↗</span></a></div><div className="hero-preview"><div className="hero-glow"/><div className="hero-window"><div className="hero-window-head"><span>Agenda da semana</span><span className="hero-mini-dot">● Disponível</span></div><div className="hero-weekheads"><span>SEG</span><span>TER</span><span>QUA</span><span>QUI</span><span>SEX</span></div><div className="hero-faux-grid">{Array.from({length:25},(_,i)=><span key={i} className={i===6||i===12||i===17||i===23?'fake-event':i===3||i===14?'fake-event alt':''}/>)}</div><div className="hero-status">✳ &nbsp; Tudo organizado em um só lugar</div></div></div></section>
    <section className="public-section" id="reservar"><div className="wrap"><div className="section-title"><div><span className="tag light">AGENDA ONLINE</span><h2>Seu próximo agendamento</h2><p>Quatro passos para reservar um horário perfeito para você.</p></div><span className="section-count">01 <small>/ 04</small></span></div>
      {success?<div className="done-box"><span className="done-icon">✓</span><span className="tag light">RESERVA CONFIRMADA</span><h2>Está tudo certo, {name.split(" ")[0]}!</h2><p>Seu horário foi reservado. Salve o link abaixo para poder reagendar ou cancelar com segurança.</p><div className="done-grid"><div><small>Serviço</small><b>{success.service}</b></div><div><small>Profissional</small><b>{success.professional}</b></div><div><small>Quando</small><b>{showDate(success.start_at)} · {showTime(success.start_at)}</b></div><div><small>Reserva</small><b>#{success.id.toString().padStart(5,"0")}</b></div></div><div className="done-actions"><button className="btn solid" onClick={()=>navigator.clipboard.writeText(publicLink).then(()=>alert("Link copiado!"))}>Copiar link da reserva</button><Link href={`/minha-reserva#token=${encodeURIComponent(success.access_token)}`} className="btn outline">Gerenciar minha reserva ↗</Link><button className="btn ghost" onClick={()=>{setSuccess(null);setName("");setEmail("");setPhone("");setNotes("");setSlot("");}}>Nova reserva</button></div></div>:
      <div className="public-booking-grid"><form className="public-form" onSubmit={submit}>
        <div className="form-step"><span>01</span><div><h3>Escolha seu serviço</h3><p>Como podemos cuidar de você?</p></div></div>
        <div className="services-layout">{services.map((s,i)=><button key={s.id} className={`choice-service ${serviceId===s.id?'active':''}`} type="button" onClick={()=>setServiceId(s.id)}><span className="service-ico" style={{color:s.color}}>{icons[i%4]}</span><strong>{s.name}</strong><small>{s.description}</small><span className="choice-service-foot"><b>{money(s.price_cents)}</b><small>{s.duration_minutes} min</small></span><span className="select-tick">{serviceId===s.id?'✓':''}</span></button>)}</div>
        <div className="form-step separate"><span>02</span><div><h3>Selecione seu profissional</h3><p>Quem vai atender você?</p></div></div>
        <div className="people-layout">{staff.map((s,i)=><button className={`person-choice ${staffId===s.id?'active':''}`} type="button" key={s.id} onClick={()=>setStaffId(s.id)}><span className={`person-avatar a${i%4}`}>{s.name.split(" ").map(n=>n[0]).slice(0,2).join("")}</span><span><b>{s.name}</b><small>{s.title}</small></span><span className="person-radio">{staffId===s.id?'✓':''}</span></button>)}</div>
        <div className="form-step separate"><span>03</span><div><h3>Escolha uma data e horário</h3><p>Horários disponíveis atualizados automaticamente.</p></div></div>
        <div className="booking-calendar"><div className="booking-cal-head"><div><strong>Selecione o dia</strong><span>{dateLabel(day,{month:"long",year:"numeric"})}</span></div><div className="booking-cal-arrows"><button type="button" disabled={monthOffset===0} aria-label="Semana anterior" onClick={()=>setMonthOffset(n=>Math.max(0,n-1))}>‹</button><button type="button" disabled={monthOffset>=12} aria-label="Próxima semana" onClick={()=>setMonthOffset(n=>Math.min(12,n+1))}>›</button></div></div><div className="calendar-days">{days.map(d=><button type="button" className={`calendar-day ${day===d?'active':''} ${dateAt(d).getUTCDay()===0?'closed':''}`} key={d} onClick={()=>setDay(d)}><small>{dateLabel(d,{weekday:"short"}).replace(".","")}</small><b>{d.slice(-2)}</b><span/></button>)}</div><div className="cal-date-alt"><label htmlFor="public-date">Ou escolher uma data</label><input id="public-date" type="date" min={today()} max={addDays(today(),90)} value={day} onChange={e=>setDay(e.target.value)}/></div></div>
        <p className="slot-label">Horários disponíveis</p>{!serviceId||!staffId?<p className="hint-box">Selecione um serviço e um profissional para ver os horários.</p>:loading?<p className="hint-box">Buscando horários disponíveis…</p>:slots.length===0?<p className="hint-box">Não existem horários disponíveis nesse dia. Experimente outra data.</p>:<div className="public-slots">{slots.map(s=><button key={s} type="button" onClick={()=>setSlot(s)} className={slot===s?'active':''}>{showTime(s)}</button>)}</div>}
        <div className="form-step separate"><span>04</span><div><h3>Seus dados</h3><p>Precisamos deles para confirmar sua reserva.</p></div></div>
        <div className="form-fields"><label className="wide">Nome completo<input required minLength={2} maxLength={120} autoComplete="name" placeholder="Seu nome" value={name} onChange={e=>setName(e.target.value)}/></label><label>E-mail<input type="email" required autoComplete="email" placeholder="voce@email.com" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Telefone com DDD<input type="tel" required autoComplete="tel" placeholder="(11) 99999-9999" value={phone} onChange={e=>setPhone(e.target.value)}/></label><label className="wide">Observações (opcional)<textarea rows={3} maxLength={500} placeholder="Algo que devamos saber?" value={notes} onChange={e=>setNotes(e.target.value)}/></label></div>
        <p className="helper-small">Seus dados são utilizados para gerenciar sua reserva. Não há cobrança de pagamento nesta etapa.</p>{error&&<p className="alert" role="alert">{error}</p>}<button className="btn solid book-submit" type="submit" disabled={!serviceId||!staffId||!slot||saving}>{saving?'Confirmando…':'Confirmar meu agendamento'} <span>↗</span></button>
      </form><aside className="booking-summary"><div className="summary-top"><span>✳</span> RESUMO DA RESERVA</div><h3>Seu tempo.<br/><em>Seu momento.</em></h3><div className="summary-rule"/><div className="summary-data"><small>ESTABELECIMENTO</small><b>{info?.business_name||'Studio Aurora'}</b></div><div className="summary-data"><small>SERVIÇO</small><b>{service?.name||'A escolher'}</b></div><div className="summary-data"><small>PROFISSIONAL</small><b>{person?.name||'A escolher'}</b></div><div className="summary-data"><small>DATA E HORÁRIO</small><b>{slot?`${showDate(slot)} às ${showTime(slot)}`:'A escolher'}</b></div><div className="summary-rule"/><div className="summary-price"><span>Total estimado</span><b>{service?money(service.price_cents):'—'}</b></div><p>Agende com tranquilidade. Você poderá reagendar ou cancelar até 2 horas antes do horário.</p></aside></div>}
    </div></section><footer className="public-footer wrap"><Link href="/" className="logo"><span className="logo-glyph">✳</span> agenda<span>flow</span><b>.</b></Link><span>© {new Date().getFullYear()} AgendaFlow · Agendamento inteligente</span><Link href="/admin">Painel do gestor ↗</Link></footer>
  </div>;
}
