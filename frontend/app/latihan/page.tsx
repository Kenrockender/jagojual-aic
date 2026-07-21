import { Suspense } from "react";

import LatihanInner from "./inner";

export default function Page() {
  return (
    <Suspense fallback={<main className="p-6 text-slate-500">Memuat…</main>}>
      <LatihanInner />
    </Suspense>
  );
}
