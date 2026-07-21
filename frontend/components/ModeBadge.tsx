"use client";

import { useEffect, useState } from "react";

import { getHealth, Mode } from "../lib/api";

/**
 * Menampilkan mode backend yang sedang berjalan.
 *
 * Ada dengan sengaja: di MODE=mock balasan & skor berasal dari heuristik, BUKAN dari
 * model. Menyembunyikan itu akan membuat demo terlihat seperti AI padahal bukan —
 * badge ini membuat statusnya jujur terbaca, termasuk saat direkam untuk video
 * proof of work.
 */
export default function ModeBadge() {
  const [mode, setMode] = useState<Mode | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => setMode(h.mode))
      .catch(() => setMode(null));
  }, []);

  if (!mode) return null;

  const lokal = mode === "local";
  return (
    <span
      title={
        lokal
          ? "Balasan & penilaian dihasilkan LLM lokal + adapter LoRA hasil fine-tune."
          : "Mode contoh: balasan & skor dari heuristik sederhana, bukan keluaran model."
      }
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        lokal ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${lokal ? "bg-emerald-500" : "bg-amber-500"}`} />
      {lokal ? "AI lokal aktif" : "Mode contoh (tanpa AI)"}
    </span>
  );
}
