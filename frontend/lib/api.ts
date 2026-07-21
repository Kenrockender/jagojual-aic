const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export type ScenarioSummary = { id: string; bidang: string; judul: string; produk: string };
export type Scenario = ScenarioSummary & {
  persona: { tipe: string; deskripsi: string };
  pembuka: string;
  keberatan: string[];
};
export type ChatMessage = { role: "sales" | "pelanggan"; text: string };
export type TeknikScore = { teknik: string; skor: number; catatan: string };
export type EvaluateResponse = { skor_total: number; per_teknik: TeknikScore[]; saran: string[] };

async function jget<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
  return r.json();
}

async function jpost<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
  return r.json();
}

export const getScenarios = () => jget<ScenarioSummary[]>("/api/scenarios");
export const getScenario = (id: string) => jget<Scenario>(`/api/scenarios/${id}`);
export const sendChat = (scenario_id: string, message: string, history: ChatMessage[]) =>
  jpost<{ reply: string }>("/api/chat", { scenario_id, message, history });
export const evaluate = (scenario_id: string, history: ChatMessage[]) =>
  jpost<EvaluateResponse>("/api/evaluate", { scenario_id, history });
