"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import ModeBadge from "../components/ModeBadge";
import { getScenarios, ScenarioSummary } from "../lib/api";

export default function Home() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch((e) => setErr(e?.message ?? "Gagal memuat skenario."));
  }, []);

  const bidangs = Array.from(new Set(scenarios.map((s) => s.bidang)));

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-bold tracking-tight">JagoJual</h1>
        <ModeBadge />
      </div>
      <p className="mt-1 text-slate-600">
        Latihan percakapan jualan dengan pelanggan AI. Pilih skenario untuk mulai:
      </p>

      {err && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{err}</p>}

      {bidangs.map((b) => (
        <section key={b} className="mt-8">
          <h2 className="text-lg font-semibold capitalize">{b}</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {scenarios
              .filter((s) => s.bidang === b)
              .map((s) => (
                <Link
                  key={s.id}
                  href={`/latihan?id=${s.id}`}
                  className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-slate-400 hover:shadow-sm"
                >
                  <div className="font-medium">{s.judul}</div>
                  <div className="mt-0.5 text-sm text-slate-500">{s.produk}</div>
                </Link>
              ))}
          </div>
        </section>
      ))}
    </main>
  );
}
