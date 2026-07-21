"use client";

import { useEffect, useState } from "react";

import { getHealth, Mode } from "../lib/api";

/**
 * Menampilkan mode backend yang sedang berjalan.
 *
 * Ada dengan sengaja: di MODE=mock balasan & skor berasal dari heuristik kata kunci,
 * BUKAN dari model. Menyembunyikan itu akan membuat demo terlihat seperti AI padahal
 * bukan — badge ini membuat statusnya jujur terbaca, termasuk saat layar direkam
 * untuk video proof of work.
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
          : "Mode contoh: balasan & skor dari heuristik kata kunci, bukan keluaran model."
      }
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.7rem] font-medium ${
        lokal
          ? "border-kuat/25 bg-kuat/5 text-kuat"
          : "border-garis-tua bg-kertas-tua text-tinta-lembut"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${lokal ? "bg-kuat" : "bg-tinta-samar"}`} />
      {lokal ? "AI lokal aktif" : "Mode contoh · tanpa AI"}
    </span>
  );
}
