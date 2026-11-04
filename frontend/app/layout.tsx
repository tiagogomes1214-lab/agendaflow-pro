import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgendaFlow — Agende seu momento",
  description: "Agendamentos online simples, rápidos e organizados.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
