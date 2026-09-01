import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL || "http://localhost:8000/api/chat";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const upstream = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { response: "Backend unreachable. Please ensure the FastAPI server is running on port 8000." },
      { status: 503 }
    );
  }
}
