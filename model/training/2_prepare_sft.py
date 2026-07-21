"""Flatten dialog berlabel -> contoh SFT siap latih (OFFLINE, mis. di Kaggle).

Alur: data/dialogs/*.json -> tiga jenis contoh -> data/sft/{train,val,test}.jsonl

Jenis contoh yang dihasilkan (lihat PLAN.md §6):

  1. coach_sesi   — 1 per dialog. Input: seluruh percakapan. Output: JSON penilaian
                    sesi (skor_total / per_teknik / saran) hasil rubrik deterministik
                    dari label emas (rubric.py). INI TUGAS UTAMA yang di-fine-tune,
                    dan bentuknya persis `EvaluateResponse` di backend.
  2. coach_turn   — 1 per giliran sales. Output: {"teknik", "kualitas"}. Tugas
                    pelabelan murni; jadi dasar metrik F1 di 4_evaluate.py.
  3. roleplay     — beberapa per dialog (default 2). Output: balasan pelanggan.
                    Porsinya sengaja kecil: mode Pelanggan mengandalkan kemampuan
                    base model, fine-tune difokuskan ke mode Pelatih.

Split 80/10/10 dikelompokkan per `scenario_id` dan distratifikasi per `bidang`,
jadi tidak ada giliran dari satu dialog yang bocor ke dua split sekaligus.

Format keluaran: JSONL chat (`{"messages": [...], "meta": {...}}`) — langsung bisa
dibaca `trl.SFTTrainer` dengan chat template Qwen.

Pakai:
    python 2_prepare_sft.py                    # semua dialog -> data/sft/
    python 2_prepare_sft.py --stats-only       # lihat distribusi tanpa menulis file
    python 2_prepare_sft.py --roleplay-per-dialog 0   # murni mode Pelatih
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import prompts
import rubric

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DIALOGS_DIR = DATA_DIR / "dialogs"
OUT_DIR = DATA_DIR / "sft"

# Di bawah jumlah ini, memotong val/test hanya menyisakan segelintir contoh yang
# tidak berarti secara statistik — lebih jujur menaruh semuanya di train + peringatan.
MIN_DIALOG_UNTUK_SPLIT = 10


# --------------------------------------------------------------------------- #
# Muat dialog
# --------------------------------------------------------------------------- #

def muat_dialog() -> list[dict]:
    dialogs = []
    for f in sorted(DIALOGS_DIR.glob("*.json")):
        if f.name == "schema.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("turns"):
            print(f"[LEWAT] {f.name}: tidak ada turns", file=sys.stderr)
            continue
        d["_file"] = f.name
        dialogs.append(d)
    return dialogs


# --------------------------------------------------------------------------- #
# Pembentuk contoh
# --------------------------------------------------------------------------- #

def _contoh(messages: list[dict], dialog: dict, tipe: str) -> dict:
    return {
        "messages": messages,
        "meta": {
            "scenario_id": dialog["scenario_id"],
            "bidang": dialog["bidang"],
            "tipe": tipe,
            "generator": dialog.get("grounding", {}).get("generator", "?"),
            "divalidasi_manusia": dialog.get("grounding", {}).get("divalidasi_manusia", False),
        },
    }


def contoh_coach_sesi(dialog: dict, tax: dict, teknik_ids: list[str]) -> dict:
    target = rubric.nilai_sesi(dialog["turns"], teknik_ids)
    return _contoh(
        [
            {"role": "system", "content": prompts.COACH_SYSTEM},
            {"role": "user", "content": prompts.coach_session_user(dialog, dialog["turns"], tax)},
            {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
        ],
        dialog,
        "coach_sesi",
    )


def contoh_coach_turn(dialog: dict, tax: dict) -> list[dict]:
    hasil = []
    for i, t in enumerate(dialog["turns"]):
        if t.get("speaker") != "sales" or not t.get("teknik") or not t.get("kualitas"):
            continue
        target = {"teknik": t["teknik"], "kualitas": t["kualitas"]}
        hasil.append(
            _contoh(
                [
                    {"role": "system", "content": prompts.COACH_TURN_SYSTEM},
                    {
                        "role": "user",
                        "content": prompts.coach_turn_user(dialog, dialog["turns"][:i], t["text"], tax),
                    },
                    {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
                ],
                dialog,
                "coach_turn",
            )
        )
    return hasil


def contoh_roleplay(dialog: dict, tax: dict, n: int, rng: random.Random) -> list[dict]:
    """Ambil `n` giliran pelanggan sebagai target balasan role-play."""
    if n <= 0:
        return []
    # Butuh minimal satu giliran sebelumnya supaya ada konteks yang dibalas.
    kandidat = [i for i, t in enumerate(dialog["turns"]) if t.get("speaker") == "pelanggan" and i > 0]
    if not kandidat:
        return []
    dipilih = sorted(rng.sample(kandidat, min(n, len(kandidat))))
    sistem = prompts.roleplay_system(dialog, tax)
    return [
        _contoh(
            [
                {"role": "system", "content": sistem},
                {"role": "user", "content": prompts.render_transcript(dialog["turns"][:i])},
                {"role": "assistant", "content": dialog["turns"][i]["text"].strip()},
            ],
            dialog,
            "roleplay",
        )
        for i in dipilih
    ]


# --------------------------------------------------------------------------- #
# Split
# --------------------------------------------------------------------------- #

def bagi_split(dialogs: list[dict], seed: int) -> dict[str, set[str]]:
    """Group split per scenario_id, distratifikasi per bidang. Return {split: {id}}."""
    rng = random.Random(seed)
    hasil: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}

    per_bidang: dict[str, list[str]] = {}
    for d in dialogs:
        per_bidang.setdefault(d["bidang"], []).append(d["scenario_id"])

    for bidang, ids in sorted(per_bidang.items()):
        ids = sorted(ids)  # urutkan dulu supaya shuffle-nya reprodusibel
        rng.shuffle(ids)
        n = len(ids)
        if n < MIN_DIALOG_UNTUK_SPLIT:
            print(
                f"[PERINGATAN] bidang '{bidang}' cuma {n} dialog (< {MIN_DIALOG_UNTUK_SPLIT}); "
                "semuanya masuk train, val/test dikosongkan.",
                file=sys.stderr,
            )
            hasil["train"].update(ids)
            continue
        n_test = max(1, round(n * 0.10))
        n_val = max(1, round(n * 0.10))
        hasil["test"].update(ids[:n_test])
        hasil["val"].update(ids[n_test : n_test + n_val])
        hasil["train"].update(ids[n_test + n_val :])
    return hasil


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def ringkas(contoh: list[dict]) -> dict:
    return {
        "jumlah": len(contoh),
        "per_tipe": dict(sorted(Counter(c["meta"]["tipe"] for c in contoh).items())),
        "per_bidang": dict(sorted(Counter(c["meta"]["bidang"] for c in contoh).items())),
        "dialog_unik": len({c["meta"]["scenario_id"] for c in contoh}),
    }


def distribusi_label(dialogs: list[dict]) -> dict:
    teknik = Counter()
    kualitas = Counter()
    keberatan = Counter()
    for d in dialogs:
        for t in d["turns"]:
            if t.get("speaker") == "sales":
                teknik[t.get("teknik")] += 1
                kualitas[t.get("kualitas")] += 1
            elif t.get("keberatan"):
                keberatan[t["keberatan"]] += 1
    return {
        "teknik": dict(sorted(teknik.items(), key=lambda x: -x[1])),
        "kualitas": dict(sorted(kualitas.items())),
        "keberatan": dict(sorted(keberatan.items(), key=lambda x: -x[1])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--roleplay-per-dialog", type=int, default=2, help="0 = murni mode Pelatih.")
    ap.add_argument("--no-turn-level", action="store_true", help="Lewati contoh pelabelan per giliran.")
    ap.add_argument("--stats-only", action="store_true", help="Cetak ringkasan, jangan tulis file.")
    args = ap.parse_args()

    dialogs = muat_dialog()
    if not dialogs:
        print(f"ERROR: tidak ada dialog di {DIALOGS_DIR}. Jalankan 1_generate_data.py dulu.", file=sys.stderr)
        return 2

    tax = prompts.load_taxonomy()
    teknik_ids = [t["id"] for t in tax["teknik"]["label"]]
    rng = random.Random(args.seed)
    split_of = {sid: s for s, ids in bagi_split(dialogs, args.seed).items() for sid in ids}

    buckets: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for d in dialogs:
        contoh = [contoh_coach_sesi(d, tax, teknik_ids)]
        if not args.no_turn_level:
            contoh += contoh_coach_turn(d, tax)
        contoh += contoh_roleplay(d, tax, args.roleplay_per_dialog, rng)
        buckets[split_of[d["scenario_id"]]].extend(contoh)

    stats = {
        "sumber": {"dialog": len(dialogs), "label": distribusi_label(dialogs)},
        "seed": args.seed,
        "roleplay_per_dialog": args.roleplay_per_dialog,
        "split": {k: ringkas(v) for k, v in buckets.items()},
    }

    print(f"{len(dialogs)} dialog -> {sum(len(v) for v in buckets.values())} contoh SFT")
    for nama, isi in buckets.items():
        r = stats["split"][nama]
        print(f"  {nama:5} {r['jumlah']:5} contoh dari {r['dialog_unik']:4} dialog  {r['per_tipe']}")
    print(f"  distribusi teknik: {stats['sumber']['label']['teknik']}")
    print(f"  distribusi kualitas: {stats['sumber']['label']['kualitas']}")

    if args.stats_only:
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for nama, isi in buckets.items():
        path = args.out_dir / f"{nama}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for c in isi:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"  tulis {path} ({len(isi)} baris)")
    (args.out_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  tulis {args.out_dir / 'stats.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
