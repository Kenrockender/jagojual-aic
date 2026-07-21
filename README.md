# JagoJual — AI Sales Trainer untuk Toko Offline

Simulator latihan percakapan penjualan berbasis AI untuk tenaga sales lintas
industri di Indonesia (MVP: **otomotif** & **elektronik**). Trainee berlatih
melawan **pelanggan AI**, lalu mendapat **skor + feedback** per teknik jualan.

Pilar AIC COMPFEST 18: **Smart Commerce** (sales operasional). Lihat
[`../PLAN.md`](../PLAN.md) untuk desain lengkap.

## Arsitektur

```
Frontend (Next.js 14)  ──►  Backend (FastAPI)  ──►  LLM fine-tuned (LoRA, lokal)
  pilih skenario             /api/chat  → mode Pelanggan (role-play)
  role-play + skor           /api/evaluate → mode Pelatih (skor + saran)
```

- **Model:** Qwen2.5-7B-Instruct + adapter LoRA (di-fine-tune di Kaggle). Lihat `model/training/`.
- **MODE=mock** (default): jalan **tanpa GPU/model** — untuk scaffold & verifikasi panitia.
- **MODE=local**: pakai LLM + adapter (diimplementasikan M3).

## Menjalankan (Docker)

```bash
docker compose up --build
```

- UI: http://localhost:3000
- API docs: http://localhost:8000/docs

Berjalan dalam **mock mode** (tanpa GPU). Balasan pelanggan & skor berasal dari
skrip/heuristik — cukup untuk mendemokan alur end-to-end.

## Menjalankan (tanpa Docker)

**Backend**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Tes backend
```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

## Struktur
```
JagoJual/
├── backend/       FastAPI (mock + hook ke LLM lokal)
├── frontend/      Next.js 14 (2 layar: pilih skenario → role-play)
├── model/         training (Kaggle) + checkpoints (adapter LoRA)
└── data/          dataset dialog sintetik + skema
```

## Status
| Tahap | Status |
|---|---|
| M0 — Scaffold (mock mode jalan) | ✅ |
| M1 — Dataset dialog sintetik | ⬜ |
| M2 — Fine-tune QLoRA (Kaggle) | ⬜ |
| M3 — Integrasi LLM lokal (MODE=local) | ⬜ |
| M4 — Polish frontend | ⬜ |

## Konvensi commit (Conventional Commits — wajib rulebook)
- `feat: <deskripsi>` — fitur baru
- `fix: <deskripsi>` — perbaikan bug
- `refactor: <deskripsi>` — perubahan struktur tanpa ubah fungsionalitas
- `docs: <deskripsi>` — dokumentasi

Panduan: https://www.conventionalcommits.org
