import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: Context) {
  const { path } = await context.params;
  const allowedRoots = new Set(["public", "auth", "admin", "health"]);
  if (!path.length || !allowedRoots.has(path[0]) || path.some((part) => !/^[\w-]+$/.test(part))) {
    return NextResponse.json({ detail: "Caminho inválido" }, { status: 404 });
  }

  const api = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const url = `${api}/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  const authorization = request.headers.get("authorization");
  if (authorization) headers.set("Authorization", authorization);
  const bookingToken = request.headers.get("x-booking-token");
  if (bookingToken) headers.set("X-Booking-Token", bookingToken);

  try {
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    const content = await response.text();
    return new NextResponse(content, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({ detail: "API indisponível. Confira se o backend está funcionando." }, { status: 503 });
  }
}

export async function GET(request: NextRequest, context: Context) { return proxy(request, context); }
export async function POST(request: NextRequest, context: Context) { return proxy(request, context); }
export async function PUT(request: NextRequest, context: Context) { return proxy(request, context); }
export async function DELETE(request: NextRequest, context: Context) { return proxy(request, context); }
export async function PATCH(request: NextRequest, context: Context) { return proxy(request, context); }
