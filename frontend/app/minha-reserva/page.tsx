"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {addDays,PublicBooking,request,showDate,showTime,today} from "@/lib/api";

export default function ManageBooking(){
  const [token,setToken]=useState("");const [booking,setBooking]=useState<PublicBooking|null>(null);
  const [day,setDay]=useState(today());const [slots,setSlots]=useState<string[]>([]);const [selection,setSelection]=useState("");
  const [loading,setLoading]=useState(true);const [working,setWorking]=useState(false);
  const [error,setError]=useState("");const [info,setInfo]=useState("");
  useEffect(()=>{
    const raw=new URLSearchParams(window.location.hash.replace(/^#/,"")).get("token")||sessionStorage.getItem("booking_access")||"";
    if(raw){setToken(raw);sessionStorage.setItem("booking_access",raw);window.history.replaceState(null,"","/minha-reserva");}
    setLoading(false);
  },[]);
  useEffect(()=>{if(!token)return;
    request<PublicBooking>("/public/manage",{headers:{"X-Booking-Token":token}}).then(setBooking).catch((e:Error)=>setError(e.message));
  },[token]);
  useEffect(()=>{if(!token||!booking||booking.status!=="confirmed")return;
    request<{slots:string[]}>(`/public/manage/slots?day=${day}`,{headers:{"X-Booking-Token":token}})
      .then(data=>setSlots(data.slots)).catch((e:Error)=>setError(e.message));
  },[token,day,booking?.id,booking?.status]);
  async function cancel(){if(!confirm("Deseja cancelar este agendamento?"))return;setWorking(true);setError("");
    try{const data=await request<PublicBooking>("/public/manage/cancel",{method:"POST",headers:{"X-Booking-Token":token}});setBooking(data);setInfo("Reserva cancelada.");}
    catch(e){setError(e instanceof Error?e.message:"Não foi possível cancelar");}finally{setWorking(false);}}
  async function reschedule(){if(!selection)return;setWorking(true);setError("");
    try{const data=await request<PublicBooking>("/public/manage",{method:"PATCH",headers:{"X-Booking-Token":token},body:JSON.stringify({start_at:selection})});setBooking(data);setSelection("");setInfo("Agendamento reagendado com sucesso.");}
    catch(e){setError(e instanceof Error?e.message:"Não foi possível reagendar");}finally{setWorking(false);}}
  return <main className="portal-shell"><div className="portal-wrap"><Link href="/" className="logo"><span className="logo-glyph">✳</span> agenda<span>flow</span><b>.</b></Link><div className="portal-card"><span className="tag light">ÁREA DO CLIENTE</span><h1>Minha reserva</h1><p>Consulte seu horário e faça alterações com segurança.</p>
    {loading?<p>Carregando...</p>:!token?<p className="hint-box">Abra o link fornecido ao confirmar sua reserva. Ele é pessoal e não deve ser compartilhado.</p>:booking?<><div className="portal-info"><div><small>Serviço</small><b>{booking.service}</b></div><div><small>Profissional</small><b>{booking.professional}</b></div><div><small>Data</small><b>{showDate(booking.start_at)}</b></div><div><small>Horário</small><b>{showTime(booking.start_at)}</b></div><div><small>Status</small><span className={`state ${booking.status}`}>{booking.status==="confirmed"?"Confirmado":booking.status==="cancelled"?"Cancelado":"Concluído"}</span></div></div>
      {booking.status==="confirmed"&&<><h2>Reagendar</h2><p>Escolha um novo dia e horário. Alterações online são permitidas até 2 horas antes do atendimento.</p><div className="form-fields"><label>Nova data<input type="date" min={today()} max={addDays(today(),90)} value={day} onChange={e=>{setDay(e.target.value);setSelection("");}}/></label></div><div className="public-slots">{slots.map(s=><button type="button" key={s} className={selection===s?"active":""} onClick={()=>setSelection(s)}>{showTime(s)}</button>)}</div>{slots.length===0&&<p className="hint-box">Sem horários disponíveis nesta data.</p>}<div className="portal-actions"><button className="btn solid" disabled={!selection||working} onClick={reschedule}>Confirmar novo horário</button><button className="btn warn" disabled={working} onClick={cancel}>Cancelar reserva</button></div></>}
    </>:<p className="hint-box">Buscando reserva…</p>}{info&&<p className="success-message">{info}</p>}{error&&<p className="alert" role="alert">{error}</p>}
    <Link href="/" className="back-home">← Voltar à página inicial</Link></div></div></main>;
}
