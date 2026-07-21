"""Fine-tune QLoRA Qwen2.5 untuk mode Pelatih (OFFLINE, dijalankan di Kaggle).

SEKALI JALAN, DI LUAR REPO SUBMISSION. Skrip ini TIDAK pernah dipanggil backend
saat demo — rulebook membatasi implementasi AI pada inferensi berparameter statis.
Keluarannya adalah adapter LoRA (puluhan MB) yang di-commit ke ../checkpoints/ lalu
di-load backend di MODE=local.

Kenapa QLoRA:
  * Base 7B di-quantize 4-bit muat di satu GPU Kaggle (P100 16GB / T4 15GB), dan
    adapter hasilnya cukup kecil untuk masuk repo — juri bisa memverifikasi sendiri.
  * Yang dilatih hanya adapter; bobot base tetap milik Qwen (Apache-2.0) dan tidak
    ikut di-commit.

Pakai (di sel notebook Kaggle):
    !pip install -q "transformers>=4.44" "trl>=0.12" "peft>=0.13" \
                    "bitsandbytes>=0.43" "accelerate>=0.34" datasets
    !python 3_finetune_qlora.py --train ../../data/sft/train.jsonl \
                               --val   ../../data/sft/val.jsonl \
                               --out   ../checkpoints

    # kalau 7B terlalu berat / lambat, turun ke cadangan:
    !python 3_finetune_qlora.py --base-model Qwen/Qwen2.5-3B-Instruct ...
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_BASE = "Qwen/Qwen2.5-7B-Instruct"

# Semua proyeksi linear blok attention + MLP Qwen2. Melatih keduanya (bukan hanya
# attention) memberi kapasitas lebih untuk tugas keluaran terstruktur, dengan biaya
# parameter yang masih kecil pada r rendah.
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default=DEFAULT_BASE)
    ap.add_argument("--train", type=Path, required=True)
    ap.add_argument("--val", type=Path, default=None)
    ap.add_argument("--out", type=Path, required=True, help="Folder adapter LoRA hasil latih.")

    ap.add_argument("--tipe", nargs="*", default=None,
                    help="Batasi jenis contoh, mis. --tipe coach_sesi coach_turn (default: semua).")

    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--warmup-ratio", type=float, default=0.03)
    ap.add_argument("--save-steps", type=int, default=100, help="Checkpoint berkala (sesi Kaggle bisa mati).")
    ap.add_argument("--resume", action="store_true",
                    help="Lanjutkan dari checkpoint terakhir di --out (sesi Kaggle mati di tengah jalan).")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-steps", type=int, default=-1,
                    help="Batasi jumlah step (mis. 5 untuk smoke test cepat). -1 = pakai --epochs.")

    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.05)

    ap.add_argument("--no-4bit", action="store_true", help="Latih tanpa kuantisasi (butuh GPU besar).")
    return ap.parse_args()


def muat_split(path: Path, tipe: list[str] | None) -> "datasets.Dataset":  # noqa: F821
    from datasets import Dataset

    baris = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if tipe:
        baris = [b for b in baris if b["meta"]["tipe"] in tipe]
    if not baris:
        raise SystemExit(f"ERROR: {path} kosong setelah filter --tipe {tipe}.")
    print(f"  {path.name}: {len(baris)} contoh {dict(Counter(b['meta']['tipe'] for b in baris))}")
    # Buang 'meta' — TRL hanya perlu kolom percakapan, kolom sisa bikin bingung collator.
    return Dataset.from_list([{"messages": b["messages"]} for b in baris])


def main() -> int:
    args = parse_args()

    import torch
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        print("ERROR: butuh GPU. Di Kaggle: Settings -> Accelerator -> GPU.", file=sys.stderr)
        return 2

    # T4 (Kaggle) tidak mendukung bf16; P100/A100 mendukung. Pilih otomatis supaya
    # skrip yang sama jalan di kedua tipe akselerator.
    bf16 = torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float16
    print(f"GPU: {torch.cuda.get_device_name(0)} | dtype: {dtype}")

    print("Memuat data:")
    ds_train = muat_split(args.train, args.tipe)
    ds_val = muat_split(args.val, args.tipe) if args.val and args.val.exists() else None
    if ds_val is None:
        print("  (tanpa val — eval loss dilewati)")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant = None
    if not args.no_4bit:
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        )

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )

    cfg = SFTConfig(
        output_dir=str(args.out),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=args.warmup_ratio,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit" if not args.no_4bit else "adamw_torch",
        max_length=args.max_seq_len,
        packing=False,  # contoh kita pendek & mandiri; packing malah mencampur konteks
        bf16=bf16,
        fp16=not bf16,
        logging_steps=10,
        save_steps=args.save_steps,
        save_total_limit=2,
        eval_strategy="epoch" if ds_val is not None else "no",
        report_to="none",
        seed=args.seed,
    )

    # Muat model secara eksplisit (bukan lewat model_init_kwargs) supaya kompatibel
    # lintas versi TRL — di TRL baru SFTTrainer tidak lagi menerima model_init_kwargs.
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quant,
        torch_dtype=dtype,
        device_map="auto",
    )
    model.config.use_cache = False  # wajib saat gradient checkpointing aktif

    trainer = SFTTrainer(
        model=model,
        args=cfg,
        train_dataset=ds_train,
        eval_dataset=ds_val,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    # Hanya resume kalau memang ada checkpoint; kalau tidak, Trainer melempar error
    # dan sesi Kaggle yang sudah antre lama jadi terbuang percuma.
    ada_checkpoint = args.resume and any(args.out.glob("checkpoint-*"))
    if args.resume and not ada_checkpoint:
        print(f"--resume diminta tapi tidak ada checkpoint-* di {args.out}; mulai dari awal.")
    trainer.train(resume_from_checkpoint=ada_checkpoint or None)

    args.out.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.out))
    tokenizer.save_pretrained(str(args.out))

    # Jejak reproduksi: hyperparameter apa yang menghasilkan adapter ini.
    meta = {
        "base_model": args.base_model,
        "lora": {"r": args.lora_r, "alpha": args.lora_alpha, "dropout": args.lora_dropout,
                 "target_modules": TARGET_MODULES},
        "training": {"epochs": args.epochs, "lr": args.lr, "max_seq_len": args.max_seq_len,
                     "batch_size": args.batch_size, "grad_accum": args.grad_accum,
                     "quantized_4bit": not args.no_4bit, "seed": args.seed},
        "data": {"train": str(args.train), "val": str(args.val) if args.val else None,
                 "n_train": len(ds_train), "n_val": len(ds_val) if ds_val else 0,
                 "tipe": args.tipe or "semua"},
    }
    (args.out / "training_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nAdapter tersimpan di {args.out}")
    print("Langkah berikutnya: 4_evaluate.py --adapter <folder ini> --mode both")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
