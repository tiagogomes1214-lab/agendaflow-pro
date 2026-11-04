export type Service = {id:number; name:string; description:string; duration_minutes:number; price_cents:number; color:string; active:boolean};
export type Staff = {id:number; name:string; title:string; active:boolean};
export type BookingStatus = "confirmed" | "cancelled" | "completed";
export type Booking = {
  id:number; customer_name:string; customer_email:string; customer_phone:string; notes:string;
  service:string; service_id:number; service_color:string; professional:string; staff_id:number;
  start_at:string; end_at:string; status:BookingStatus; price_cents:number;
};
export type PublicBooking = Pick<Booking,"id"|"customer_name"|"service"|"professional"|"start_at"|"end_at"|"status"|"price_cents">;
export type Stats = {
  total:number; confirmed:number; upcoming:number; completed:number; cancelled:number;
  revenue_month_cents:number; revenue_total_cents:number; top_services:{name:string;count:number}[];
};
export type WorkHour = {
  id:number; staff_id:number|null; weekday:number; enabled:boolean;
  opens_at:string; closes_at:string; break_start:string|null; break_end:string|null;
};
export type TimeBlock = {id:number; staff_id:number|null; start_at:string; end_at:string; reason:string};
export type Notice = {id:number; appointment_id:number; kind:string; channel:string; status:string; scheduled_at:string; sent_at:string|null; attempts:number; error:string};
export type PublicInfo = {business_name:string; timezone:string; hours:WorkHour[]};
export type BookingSuccess = PublicBooking & {access_token:string};

const locale = "pt-BR";
export const money = (cents:number) => new Intl.NumberFormat(locale,{style:"currency",currency:"BRL"}).format(cents / 100);
export const localDate = (value:string|Date) => new Intl.DateTimeFormat("en-CA",{timeZone:"America/Sao_Paulo",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date(value));
export const today = () => localDate(new Date());
export const showTime = (value:string|Date) => new Intl.DateTimeFormat(locale,{timeZone:"America/Sao_Paulo",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).format(new Date(value));
export const showDate = (value:string|Date) => new Intl.DateTimeFormat(locale,{timeZone:"America/Sao_Paulo",day:"2-digit",month:"long",year:"numeric"}).format(new Date(value));
export const showShortDate = (value:string|Date) => new Intl.DateTimeFormat(locale,{timeZone:"America/Sao_Paulo",day:"2-digit",month:"short"}).format(new Date(value));
export function dateAt(ymd:string){return new Date(`${ymd}T12:00:00Z`);}
export function addDays(ymd:string,days:number){const d=dateAt(ymd); d.setUTCDate(d.getUTCDate()+days); return d.toISOString().slice(0,10);}
export function startOfWeek(ymd:string){return addDays(ymd,-((dateAt(ymd).getUTCDay()+6)%7));}
export function dateLabel(ymd:string, options?:Intl.DateTimeFormatOptions){return new Intl.DateTimeFormat(locale,{timeZone:"UTC",...options}).format(dateAt(ymd));}
export function toMoneyInput(cents:number){return (cents/100).toFixed(2).replace(".",",");}
export function inputToCents(value:string){return Math.round(Number(value.replace(",","."))*100);}
export const statusLabel:Record<BookingStatus,string>={confirmed:"Confirmado",cancelled:"Cancelado",completed:"Concluído"};

export async function request<T>(path:string,options?:RequestInit):Promise<T>{
  const res=await fetch(`/api${path}`,{cache:"no-store",...options,headers:{"Content-Type":"application/json",...options?.headers}});
  let data:unknown;
  try{data=await res.json();}catch{data={};}
  if(!res.ok){
    const detail=(data as {detail?:unknown}).detail;
    if(Array.isArray(detail)){
      throw new Error(detail.map((d:{msg?:string})=>d.msg??"Dados inválidos").join("; "));
    }
    throw new Error(typeof detail==="string"?detail:"Não foi possível concluir a operação.");
  }
  return data as T;
}
