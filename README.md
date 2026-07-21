# JagoJual — AI Sales Trainer untuk Toko Offline

Simulator latihan percakapan penjualan berbasis AI untuk tenaga sales lintas
industri di Indonesia (MVP: **otomotif** & **elektronik**). Trainee berlatih
melawan **pelanggan AI**, lalu mendapat **skor + feedback** per teknik jualan.

Pilar AIC COMPFEST 18: **Smart Commerce** (sales operasional).

| Dokumen | Isi |
|---|---|
| [`PLAN.md`](PLAN.md) | Desain & rasional lengkap: kenapa LoRA, kenapa data sintetik, pemetaan ke kriteria penilaian |
| [`model/training/TRAINING.md`](model/training/TRAINING.md) | **Runbook training di Kaggle**, langkah demi langkah sampai adapter jalan di backend |
| [`data/README.md`](data/README.md) | Taksonomi label, cara dataset dibuat, catatan lisensi & etika |
| [Status & serah terima](#status) | Posisi pengerjaan sekarang dan apa yang perlu dibereskan berikutnya |

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
├── backend/
│   ├── app/
│   │   ├── main.py        FastAPI: /api/scenarios, /api/chat, /api/evaluate
│   │   ├── prompts.py     prompt inferensi — KEMBAR dengan model/training/prompts.py
│   │   ├── llm.py         MODE=local: Qwen2.5 4-bit + adapter LoRA
│   │   ├── mock.py        MODE=mock: heuristik kata kunci (bukan AI)
│   │   └── scenarios.py   6 skenario latihan (hardcoded)
│   └── tests/             22 tes, jalan tanpa GPU
├── frontend/              Next.js 14 (2 layar: pilih skenario → role-play + rapor)
├── model/
│   ├── training/          OFFLINE (Kaggle) — tidak pernah dipanggil backend
│   │   ├── TRAINING.md    ← runbook
│   │   ├── build_scenario_matrix.py → data/scenario_matrix.json
│   │   ├── 1_generate_data.py       → data/dialogs/*.json
│   │   ├── rubric.py      rubrik deterministik label emas → target skor sesi
│   │   ├── 2_prepare_sft.py         → data/sft/*.jsonl  (tidak di-commit, turunan)
│   │   ├── 3_finetune_qlora.py      → model/checkpoints/
│   │   └── 4_evaluate.py            adapter vs base
│   └── checkpoints/       adapter LoRA (masih kosong — training belum dijalankan)
└── data/                  taksonomi, matriks skenario, dialog berlabel
```

> **`backend/app/prompts.py` dan `model/training/prompts.py` adalah kontrak berpasangan.**
> Adapter dilatih pada format prompt di sana. Kalau salah satu diubah tanpa yang lain,
> model melihat format berbeda dari yang dilatihkan dan mutunya turun **tanpa error
> yang kelihatan**. Ubah keduanya bersamaan.

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

**Tenggat penyisihan: 25 Agustus 2026, 23.55 WIB** — itu batas commit/push terakhir
*sekaligus* batas submisi berkas. Deliverable: link repo (public, README + docker compose),
video Proof of Work ≤7 menit (YouTube unlisted, **dilarang di-cut**, hanya boleh
fast-forward + voice over), video inovasi ≤5 menit (public), proposal PDF ≤20 halaman.

Jalur kode sudah tersambung ujung ke ujung; yang tersisa adalah menjalankannya —
generate dialog (butuh endpoint LLM), latih adapter (butuh GPU Kaggle), lalu commit
adapter ke `model/checkpoints/`.

### Kalau kamu baru bergabung, mulai dari sini

```bash
git clone https://github.com/Kenrockender/jagojual-aic.git && cd jagojual-aic
docker compose up --build        # UI di :3000 — jalan dalam mock mode
```

Yang perlu kamu tahu sebelum menyentuh apa pun:

1. **Yang jalan sekarang belum AI.** Badge "Mode contoh · tanpa AI" di UI itu jujur.
   `mock.py` menilai dengan mencocokkan kata kunci, dan balasan pelanggannya kalimat
   kaleng dari `scenarios.py`. Jalur AI-nya (`llm.py`) sudah lengkap tapi menunggu adapter.
2. **`data/dialogs/` baru berisi 2 seed.** Dataset ~300 dialog sudah digenerate di luar
   repo tapi **belum di-push**. Tanpa itu, `2_prepare_sft.py` tidak menghasilkan
   split val/test yang berarti.
3. **`data/sft/` sengaja tidak di-commit** — turunan deterministik dari `data/dialogs/`.
   Regenerate dengan `python 2_prepare_sft.py`.

### Utang teknis yang sudah diketahui

Bukan bug yang bikin error, tapi hal yang akan ditanyakan juri atau menurunkan mutu diam-diam:

| Hal | Kenapa penting |
|---|---|
| **Persona backend ≠ persona taksonomi.** `scenarios.py` memakai `skeptis-hemat`, `rasional`, `pasif`, `awam`, `hati-hati`; `data/taxonomy.json` memakai `skeptis`, `buru_buru`, `sensitif_harga`, `banyak_tanya`, `loyal_merk_lain`, `cuma_lihat`. | Model dilatih melihat label taksonomi, saat demo disodori label lain. Dampaknya ringan (role-play mengandalkan base model) tapi mudah diluruskan. |
| **6 skenario hardcoded, sementara `scenario_matrix.json` punya 300 sel.** | Timpang: dataset besar tapi aplikasi menawarkan skenario tulisan tangan. Sebaiknya skenario dibangkitkan dari matriks. |
| **Angka evaluasi belum punya tempat tampil.** `4_evaluate.py` menghasilkan `eval.json`, tapi belum dikutip di README maupun proposal. | Itu satu-satunya bukti fine-tuning berguna. |
| **`npm audit` masih menyisakan temuan severity high pada Next.js.** Hanya tertutup dengan naik ke Next 16 (major, butuh React 19). | Sengaja ditunda: aplikasi jalan di localhost, tanpa middleware, `next/image`, atau server actions. Putuskan sebelum submisi. |

## Konvensi commit (Conventional Commits — wajib rulebook)
- `feat: <deskripsi>` — fitur baru
- `fix: <deskripsi>` — perbaikan bug
- `refactor: <deskripsi>` — perubahan struktur tanpa ubah fungsionalitas
- `docs: <deskripsi>` — dokumentasi

Panduan: https://www.conventionalcommits.org
