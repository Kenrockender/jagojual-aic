# Model — Fine-tuning (dikerjakan di Kaggle)

> **Offline & sekali jalan.** Skrip di folder ini TIDAK dipanggil backend saat
> demo (sesuai batasan MVP rulebook: inferensi berparameter statis). Output-nya
> berupa **adapter LoRA** yang di-commit ke `../checkpoints/` lalu di-load backend
> di MODE=local.

## Ringkasan
- **Base:** `Qwen/Qwen2.5-7B-Instruct` (Apache-2.0) · cadangan `Qwen2.5-3B-Instruct`
- **Metode:** QLoRA (4-bit) via `peft` + `trl`
- **Platform:** Kaggle (P100 16GB / T4×2, ~30 jam/minggu gratis)
- **Fokus fine-tune:** mode **Pelatih** (penilaian teknik). Role-play andalkan base.

## Status skrip

| File | Fungsi | Status |
|---|---|---|
| `build_scenario_matrix.py` | Rencanakan sel dialog seimbang → `data/scenario_matrix.json` | ✅ siap |
| `prompts.py` | Template prompt generate + prompt inferensi (roleplay/coach) | ✅ siap |
| `1_generate_data.py` | Generate + validasi dialog berlabel → `data/dialogs/*.json` | ✅ siap |
| `2_prepare_sft.py` | Flatten dialog → contoh SFT (mode Pelanggan & Pelatih), split 80/10/10 | ⬜ berikutnya |
| `3_finetune_qlora.py` | QLoRA Qwen2.5, fokus mode Pelatih | ⬜ |
| `4_evaluate.py` | Turn-level F1 teknik + kualitas saran, vs base non-fine-tune | ⬜ |

## Langkah data (sudah bisa dijalankan)

```bash
cd model/training

# 1) matriks skenario (300 sel: 150 otomotif + 150 elektronik, seimbang & deterministik)
python build_scenario_matrix.py --per-bidang 150

# 2) generate dialog — client OpenAI-compatible (provider mana pun / server lokal vLLM/Ollama)
export JAGO_LLM_BASE_URL=https://.../v1
export JAGO_LLM_API_KEY=sk-...
export JAGO_LLM_MODEL=qwen2.5-72b-instruct
python 1_generate_data.py --dry-run     # cek prompt tanpa panggil API
python 1_generate_data.py --limit 5     # smoke test
python 1_generate_data.py               # semua (resume otomatis: skip yang sudah ada)

# MULTI-LLM: jalankan lagi dengan --model / JAGO_LLM_MODEL berbeda untuk diversity.
# File yang sudah ada di-skip; hapus file target dulu bila ingin menimpa dengan model lain.

# 3) validasi seluruh dialog (schema Draft-07 + aturan bisnis per-speaker)
python 1_generate_data.py --validate-only
```

Dependensi: stdlib untuk dry-run & validasi ringan. Validasi schema penuh: `pip install jsonschema`.
Semua label bersumber dari `data/taxonomy.json` (single source of truth, selaras `backend/app/schemas.py`).

## Fine-tune (akan dirinci di M2)
1. Buka notebook Kaggle, aktifkan GPU + Internet.
2. `2_prepare_sft.py` → `3_finetune_qlora.py`.
3. Simpan adapter → push HF Hub / download → commit ke `../checkpoints/`.
