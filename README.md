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
- **MODE=mock** (default): jalan **tanpa GPU/model** — jalur yang dijamin bisa dijalankan panitia.
- **MODE=local**: LLM lokal 4-bit + adapter LoRA. Butuh GPU NVIDIA.

## Menjalankan (Docker)

```bash
docker compose up --build
```

- UI: http://localhost:3000
- API docs: http://localhost:8000/docs

Berjalan dalam **mock mode** (tanpa GPU). Balasan pelanggan & skor berasal dari
skrip/heuristik — cukup untuk mendemokan alur end-to-end. UI menampilkan badge
**"Mode contoh (tanpa AI)"** supaya statusnya tidak tertukar dengan keluaran model.

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

## Menjalankan dengan LLM lokal (MODE=local)

Butuh GPU NVIDIA (dikembangkan & didemokan di RTX 4050 6GB, 4-bit) dan adapter LoRA
hasil `model/training/3_finetune_qlora.py` di `model/checkpoints/`.

```bash
cd backend
pip install -r requirements.txt -r requirements-model.txt   # torch: sesuaikan versi CUDA
JAGOJUAL_MODE=local uvicorn app.main:app
```

Bobot base (~5 GB terkuantisasi) diunduh otomatis dari Hugging Face saat start pertama.
Model dimuat **sekali** ke proses; tidak ada training, auto-tuning, atau feedback loop
saat demo — parameter statis sesuai batasan MVP rulebook.

Kalau model/adapter tidak bisa dimuat, API menjawab **503 dengan sebab yang jelas** dan
**tidak** diam-diam berpindah ke mock: hasil mock bukan penilaian AI, jadi menyajikannya
seolah-olah keluaran model akan menyesatkan. Untuk sekadar mencoba alurnya, pilih
`JAGOJUAL_MODE=mock` secara sadar.

## Tes backend
```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

Tes mencakup endpoint di mock mode serta prompt & normalisasi keluaran MODE=local
(tanpa GPU — pemuatan model tidak ikut diuji).

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
| M1 — Pipeline dataset (matriks → generate → validasi → SFT) | ✅ pipeline siap |
| M1 — Generate ~300 dialog & validasi manusia | ⬜ **butuh kredensial LLM** |
| M2 — Skrip fine-tune QLoRA + evaluasi (Kaggle) | ✅ skrip siap |
| M2 — Jalankan training & hasilkan adapter | ⬜ butuh sesi Kaggle |
| M3 — Integrasi LLM lokal (MODE=local) | ✅ |
| M4 — Polish frontend | ✅ |
| M5 — Video PoW + video inovasi + proposal | ⬜ |

Jalur kode sudah tersambung ujung ke ujung; yang tersisa adalah menjalankannya —
generate dialog (butuh endpoint LLM), latih adapter (butuh GPU Kaggle), lalu commit
adapter ke `model/checkpoints/`.

## Konvensi commit (Conventional Commits — wajib rulebook)
- `feat: <deskripsi>` — fitur baru
- `fix: <deskripsi>` — perbaikan bug
- `refactor: <deskripsi>` — perubahan struktur tanpa ubah fungsionalitas
- `docs: <deskripsi>` — dokumentasi

Panduan: https://www.conventionalcommits.org
