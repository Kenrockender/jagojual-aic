"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  ChatMessage,
  evaluate,
  EvaluateResponse,
  getScenario,
  Scenario,
  sendChat,
} from "../../lib/api";

export default function LatihanInner() {
  const id = useSearchParams().get("id") || "";
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvaluateResponse | null>(null);

  useEffect(() => {
    if (!id) return;
    getScenario(id).then((s) => {
      setScenario(s);
      setHistory([{ role: "pelanggan", text: s.pembuka }]);
    });
  }, [id]);

  async function kirim() {
    if (!input.trim() || !scenario) return;
    const salesMsg: ChatMessage = { role: "sales", text: input.trim() };
    const next = [...history, salesMsg];
    setHistory(next);
    setInput("");
    setLoading(true);
    try {
      const { reply } = await sendChat(scenario.id, salesMsg.text, next);
      setHistory((h) => [...h, { role: "pelanggan", text: reply }]);
    } finally {
      setLoading(false);
    }
  }

  async function selesai() {
    if (!scenario) return;
    setLoading(true);
    try {
      setResult(await evaluate(scenario.id, history));
    } finally {
      setLoading(false);
    }
  }

  if (!scenario) return <main className="p-6 text-slate-500">Memuat…</main>;

  if (result) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <h1 className="text-2xl font-bold">Hasil Latihan</h1>
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5">
          <div className="text-4xl font-bold">
            {result.skor_total}
            <span className="text-lg font-normal text-slate-400">/100</span>
          </div>
          <div className="mt-5 space-y-2">
            {result.per_teknik.map((t) => (
              <div key={t.teknik} className="flex items-center gap-3">
                <div className="w-40 text-sm capitalize">{t.teknik.replace(/_/g, " ")}</div>
                <div className="h-2 flex-1 rounded bg-slate-100">
                  <div className="h-2 rounded bg-slate-800" style={{ width: `${t.skor}%` }} />
                </div>
                <div className="w-10 text-right text-sm tabular-nums">{t.skor}</div>
              </div>
            ))}
          </div>
          <h2 className="mt-6 font-semibold">Saran perbaikan</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {result.saran.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
        <Link href="/" className="mt-6 inline-block rounded-lg bg-slate-800 px-4 py-2 text-sm text-white">
          Latihan lagi
        </Link>
      </main>
    );
  }

  const adaRespons = history.some((m) => m.role === "sales");

  return (
    <main className="mx-auto max-w-2xl p-6">
      <Link href="/" className="text-sm text-slate-500 hover:text-slate-700">
        ← Ganti skenario
      </Link>
      <h1 className="mt-2 text-xl font-bold">{scenario.judul}</h1>
      <p className="text-sm text-slate-500">
        {scenario.produk} · persona: {scenario.persona.tipe}
      </p>

      <div className="mt-5 space-y-3">
        {history.map((m, i) => (
          <div key={i} className={m.role === "sales" ? "text-right" : ""}>
            <span
              className={`inline-block max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                m.role === "sales" ? "bg-slate-800 text-white" : "border border-slate-200 bg-white"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
        {loading && <div className="text-sm text-slate-400">…</div>}
      </div>

      <div className="mt-5 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && kirim()}
          placeholder="Ketik respons jualan Anda…"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
        />
        <button
          onClick={kirim}
          disabled={loading}
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Kirim
        </button>
      </div>

      <button
        onClick={selesai}
        disabled={loading || !adaRespons}
        className="mt-3 w-full rounded-lg border border-slate-300 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
      >
        Selesai &amp; Nilai
      </button>
    </main>
  );
}
