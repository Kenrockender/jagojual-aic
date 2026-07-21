const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type Mode = "mock" | "local";
export type Health = { status: string; mode: Mode };

export type ScenarioSummary = { id: string; bidang: string; judul: string; produk: string };
export type Scenario = ScenarioSummary & {
  persona: { tipe: string; deskripsi: string; emosi_awal: string };
  pembuka: string;
  keberatan: string[];
};
export type ChatMessage = { role: "sales" | "pelanggan"; text: string };
export type TeknikScore = { teknik: string; skor: number; catatan: string };
export type EvaluateResponse = { skor_total: number; per_teknik: TeknikScore[]; saran: string[] };

/** Pesan backend yang layak ditunjukkan ke pengguna (mis. 503 saat MODE=local gagal). */
export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function urai(r: Response, path: string): Promise<never> {
  // FastAPI menaruh sebab yang bisa ditindaklanjuti di `detail`; tanpa ini pengguna
  // cuma melihat kotak error kosong padahal backend sudah menjelaskan masalahnya.
  let detail = "";
  try {
    detail = (await r.json())?.detail ?? "";
  } catch {
    /* body bukan JSON — pakai pesan generik di bawah */
  }
  throw new ApiError(r.status, detail || `Permintaan ke ${path} gagal (${r.status}).`);
}

/**
 * Backend mati sama sekali → fetch melempar TypeError "Failed to fetch" sebelum
 * ada response untuk dibaca. Pesan itu tidak berarti apa-apa bagi pengguna, jadi
 * diterjemahkan ke instruksi yang bisa ditindaklanjuti.
 */
async function ambil(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError(0, `Tidak bisa menghubungi backend di ${BASE}. Pastikan backend sudah berjalan.`);
  }
}

async function jget<T>(path: string): Promise<T> {
  const r = await ambil(path);
  if (!r.ok) await urai(r, path);
  return r.json();
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const r = await ambil(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) await urai(r, path);
  return r.json();
}

export const getHealth = () => jget<Health>("/api/health");
export const getScenarios = () => jget<ScenarioSummary[]>("/api/scenarios");
export const getScenario = (id: string) => jget<Scenario>(`/api/scenarios/${id}`);
export const sendChat = (scenario_id: string, message: string, history: ChatMessage[]) =>
  jpost<{ reply: string }>("/api/chat", { scenario_id, message, history });
export const evaluate = (scenario_id: string, history: ChatMessage[]) =>
  jpost<EvaluateResponse>("/api/evaluate", { scenario_id, history });
