"use client";

import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { addDays, dateAt, dateLabel } from "@/lib/api";

type BookingDatePickerProps = {
  value: string;
  minDate: string;
  maxDate: string;
  onChange: (date: string) => void;
};

const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function monthTitle(month: string) {
  const [year, index] = month.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" })
    .format(new Date(Date.UTC(year, index - 1, 1)));
}

function offsetMonth(month: string, amount: number) {
  const [year, index] = month.split("-").map(Number);
  return new Date(Date.UTC(year, index - 1 + amount, 1)).toISOString().slice(0, 7);
}

function availableMonths(min: string, max: string) {
  const months: string[] = [];
  let cursor = min.slice(0, 7);
  while (cursor <= max.slice(0, 7) && months.length < 24) {
    months.push(cursor);
    cursor = offsetMonth(cursor, 1);
  }
  return months;
}

export default function BookingDatePicker({ value, minDate, maxDate, onChange }: BookingDatePickerProps) {
  const [open, setOpen] = useState(false);
  const [visibleMonth, setVisibleMonth] = useState(value.slice(0, 7));
  const rootRef = useRef<HTMLDivElement>(null);
  const pendingFocusRef = useRef<string | null>(null);
  const months = useMemo(() => availableMonths(minDate, maxDate), [minDate, maxDate]);

  const days = useMemo(() => {
    const [year, month] = visibleMonth.split("-").map(Number);
    const first = new Date(Date.UTC(year, month - 1, 1));
    const mondayOffset = (first.getUTCDay() + 6) % 7;
    return Array.from({ length: 42 }, (_, index) =>
      new Date(Date.UTC(year, month - 1, 1 - mondayOffset + index)).toISOString().slice(0, 10)
    );
  }, [visibleMonth]);

  useEffect(() => {
    setVisibleMonth(value.slice(0, 7));
  }, [value]);

  useEffect(() => {
    if (!open) return;
    function closeOnOutside(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function closeOnEscape(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        rootRef.current?.querySelector<HTMLButtonElement>(".pro-date-trigger")?.focus();
      }
    }
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  useEffect(() => {
    if (!open || !pendingFocusRef.current) return;
    const target = pendingFocusRef.current;
    const button = Array.from(rootRef.current?.querySelectorAll<HTMLButtonElement>("[data-calendar-date]") ?? [])
      .find((element) => element.dataset.calendarDate === target);
    if (button) {
      button.focus();
      pendingFocusRef.current = null;
    }
  }, [open, visibleMonth]);

  function choose(date: string) {
    if (date < minDate || date > maxDate) return;
    onChange(date);
    setOpen(false);
    rootRef.current?.querySelector<HTMLButtonElement>(".pro-date-trigger")?.focus();
  }

  function moveFocus(event: KeyboardEvent<HTMLButtonElement>, current: string) {
    const movement: Record<string, number> = {
      ArrowLeft: -1,
      ArrowRight: 1,
      ArrowUp: -7,
      ArrowDown: 7,
      Home: -((dateAt(current).getUTCDay() + 6) % 7),
      End: 6 - ((dateAt(current).getUTCDay() + 6) % 7),
    };
    if (!(event.key in movement)) return;
    event.preventDefault();
    const target = addDays(current, movement[event.key]);
    if (target < minDate || target > maxDate) return;
    pendingFocusRef.current = target;
    if (target.slice(0, 7) !== visibleMonth) {
      setVisibleMonth(target.slice(0, 7));
    } else {
      const button = Array.from(rootRef.current?.querySelectorAll<HTMLButtonElement>("[data-calendar-date]") ?? [])
        .find((element) => element.dataset.calendarDate === target);
      button?.focus();
      pendingFocusRef.current = null;
    }
  }

  const formattedDate = dateLabel(value, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const selectedMonth = months.includes(visibleMonth) ? visibleMonth : months[0];

  return (
    <div className="pro-date-picker" ref={rootRef}>
      <button
        type="button"
        className={`pro-date-trigger ${open ? "is-open" : ""}`}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => {
          setVisibleMonth(value.slice(0, 7));
          pendingFocusRef.current = value;
          setOpen((previous) => !previous);
        }}
      >
        <span className="pro-date-trigger-icon" aria-hidden="true">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="5" width="18" height="16" rx="3" />
            <path d="M7 3v4M17 3v4M3 10h18" />
          </svg>
        </span>
        <span className="pro-date-trigger-text"><b>Escolher no calendário</b><small>{formattedDate}</small></span>
        <span className="pro-date-trigger-chevron" aria-hidden="true">{open ? "⌃" : "⌄"}</span>
      </button>

      {open && (
        <div className="pro-date-popover" role="dialog" aria-label="Escolher data do agendamento">
          <div className="pro-date-intro">
            <span className="pro-date-eyebrow">AGENDA ONLINE</span>
            <strong>Qual dia funciona melhor?</strong>
            <span>Escolha uma data para consultar os horários.</span>
          </div>
          <div className="pro-date-month-row">
            <select
              className="pro-date-month-select"
              aria-label="Selecionar mês e ano"
              value={selectedMonth}
              onChange={(event) => setVisibleMonth(event.target.value)}
            >
              {months.map((month) => <option key={month} value={month}>{monthTitle(month)}</option>)}
            </select>
            <div className="pro-date-nav">
              <button type="button" aria-label="Mês anterior" disabled={visibleMonth <= minDate.slice(0, 7)} onClick={() => setVisibleMonth((m) => offsetMonth(m, -1))}>‹</button>
              <button type="button" aria-label="Próximo mês" disabled={visibleMonth >= maxDate.slice(0, 7)} onClick={() => setVisibleMonth((m) => offsetMonth(m, 1))}>›</button>
            </div>
          </div>
          <div className="pro-date-weekdays" aria-hidden="true">
            {WEEKDAYS.map((name) => <span key={name}>{name}</span>)}
          </div>
          <div className="pro-date-grid" role="group" aria-label={monthTitle(visibleMonth)}>
            {days.map((date) => {
              const selected = date === value;
              const today = date === minDate;
              const otherMonth = date.slice(0, 7) !== visibleMonth;
              const disabled = date < minDate || date > maxDate;
              return (
                <button
                  key={date}
                  type="button"
                  data-calendar-date={date}
                  className={`pro-date-day ${selected ? "is-selected" : ""} ${today ? "is-today" : ""} ${otherMonth ? "is-outside" : ""}`}
                  disabled={disabled}
                  aria-pressed={selected}
                  aria-label={dateLabel(date, { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
                  onClick={() => choose(date)}
                  onKeyDown={(event) => moveFocus(event, date)}
                >
                  <span>{Number(date.slice(-2))}</span>
                  {today && <i aria-hidden="true" />}
                </button>
              );
            })}
          </div>
          <div className="pro-date-footer">
            <div className="pro-date-legend"><span className="pro-date-legend-mark" /> Hoje</div>
            <button type="button" onClick={() => choose(minDate)}>Selecionar hoje <span aria-hidden="true">↗</span></button>
          </div>
          <p className="pro-date-help">Datas futuras podem ser selecionadas; a disponibilidade de horários aparece após a escolha.</p>
        </div>
      )}
    </div>
  );
}
