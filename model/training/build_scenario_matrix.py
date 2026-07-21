"""Bangun matriks skenario terkontrol dari data/taxonomy.json.

Tujuan: menentukan SEL yang akan digenerate (bidang x produk x topik_keberatan x
persona x varian-kualitas) secara SEIMBANG & deterministik, sebelum memanggil LLM.
Ini menjaga distribusi kelas (mitigasi risiko "kelas tak seimbang", PLAN.md §11).

Output: data/scenario_matrix.json — daftar sel, dipakai oleh 1_generate_data.py.

Pakai:
    python build_scenario_matrix.py --per-bidang 150
    python build_scenario_matrix.py --per-bidang 150 --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TAXONOMY = DATA_DIR / "taxonomy.json"
OUT = DATA_DIR / "scenario_matrix.json"

# Porsi dialog yang menyisipkan turn sales "lemah" (agar model belajar beda mutu).
RASIO_VARIAN_CAMPUR = 0.30


def load_taxonomy() -> dict:
    return json.loads(TAXONOMY.read_text(encoding="utf-8"))


def build_bidang(bidang_id: str, spec: dict, target: int, rng: random.Random) -> list[dict]:
    produk = spec["produk_contoh"]
    topik = spec["topik_keberatan"]
    persona_ids = [p["id"] for p in load_taxonomy()["persona"]["label"]]

    sel: list[dict] = []
    # Stratifikasi: bagi rata target ke setiap topik_keberatan, lalu rotasi
    # produk & persona agar tiap kombinasi tersebar merata.
    per_topik = _bagi_rata(target, len(topik))
    counter = 0
    for topik_spec, n in zip(topik, per_topik):
        for i in range(n):
            varian = "campur" if rng.random() < RASIO_VARIAN_CAMPUR else "kuat"
            sel.append(
                {
                    "scenario_id": f"{bidang_id}_{topik_spec['id']}_{i + 1:02d}",
                    "bidang": bidang_id,
                    "produk": produk[counter % len(produk)],
                    "topik_keberatan": topik_spec["id"],
                    "keberatan_global": topik_spec["map"],
                    "contoh_ucapan": topik_spec["contoh_ucapan"],
                    "persona": persona_ids[counter % len(persona_ids)],
                    "varian_kualitas": varian,
                }
            )
            counter += 1
    rng.shuffle(sel)
    return sel


def _bagi_rata(total: int, n: int) -> list[int]:
    """Bagi `total` ke `n` ember sesetara mungkin."""
    dasar, sisa = divmod(total, n)
    return [dasar + (1 if i < sisa else 0) for i in range(n)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-bidang", type=int, default=150, help="Target dialog per bidang.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    tax = load_taxonomy()

    matrix: list[dict] = []
    for bidang_id, spec in tax["bidang"].items():
        matrix.extend(build_bidang(bidang_id, spec, args.per_bidang, rng))

    payload = {
        "meta": {
            "versi_taksonomi": tax["versi"],
            "seed": args.seed,
            "per_bidang": args.per_bidang,
            "total": len(matrix),
            "rasio_varian_campur": RASIO_VARIAN_CAMPUR,
        },
        "sel": matrix,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Ringkasan distribusi ke stdout untuk sanity-check.
    print(f"OK: {len(matrix)} sel -> {OUT}")
    for dim in ("bidang", "topik_keberatan", "persona", "varian_kualitas"):
        c = Counter(s[dim] for s in matrix)
        print(f"  {dim}: {dict(sorted(c.items()))}")


if __name__ == "__main__":
    main()
