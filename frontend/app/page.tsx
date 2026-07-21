"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import ModeBadge from "../components/ModeBadge";
import { getScenarios, ScenarioSummary } from "../lib/api";

const JUDUL_BIDANG: Record<string, string> = {
  otomotif: "Showroom mobil",
  elektronik: "Toko elektronik",
};

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
    <main className="mx-auto max-w-3xl px-6 py-12 sm:py-16">
      <header className="border-b border-garis pb-8">
        <div className="flex items-start justify-between gap-4">
          <p className="eyebrow">Latihan percakapan penjualan</p>
          <ModeBadge />
        </div>
        <h1 className="mt-3 font-display text-5xl font-bold tracking-tight sm:text-6xl">JagoJual</h1>
        <p className="mt-4 max-w-xl text-[0.975rem] leading-relaxed text-tinta-lembut">
          Hadapi pelanggan yang keras kepala tanpa risiko kehilangan penjualan sungguhan.
          Pilih satu situasi, layani sampai tuntas, lalu lihat teknik mana yang sudah kuat
          dan mana yang bocor.
        </p>
      </header>

      {err && (
        <p role="alert" className="mt-8 border-l-2 border-lemah bg-bata-muda/40 px-4 py-3 text-sm text-bata-tua">
          {err}
        </p>
      )}

      {bidangs.map((b) => (
        <section key={b} className="mt-12">
          <div className="flex items-baseline gap-4">
            <h2 className="eyebrow">{JUDUL_BIDANG[b] ?? b}</h2>
            <span className="h-px flex-1 bg-garis" />
          </div>

          <ul className="mt-5 space-y-3">
            {scenarios
              .filter((s) => s.bidang === b)
              .map((s) => (
                <li key={s.id}>
                  <Link
                    href={`/latihan?id=${s.id}`}
                    className="group flex items-center gap-4 border border-garis bg-white/70 px-5 py-4 transition hover:border-bata hover:bg-white"
                  >
                    {/* Batang aksen: penanda arah yang tenang saat diam, tegas saat disorot. */}
                    <span className="h-9 w-0.5 shrink-0 bg-garis-tua transition group-hover:bg-bata" />
                    <span className="min-w-0 flex-1">
                      <span className="block font-medium leading-snug">{s.judul}</span>
                      <span className="mt-0.5 block text-sm text-tinta-samar">{s.produk}</span>
                    </span>
                    <span
                      aria-hidden
                      className="shrink-0 text-tinta-samar transition group-hover:translate-x-0.5 group-hover:text-bata"
                    >
                      →
                    </span>
                  </Link>
                </li>
              ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
