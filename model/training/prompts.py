"""Template prompt untuk pipeline data JagoJual.

Berisi:
  * build_generation_messages() -> prompt untuk GENERATE dialog berlabel (dipakai
    1_generate_data.py). Ber-grounding ke framework sales nyata dan meminta output
    JSON sesuai data/dialogs/schema.json.
  * ROLEPLAY_SYSTEM / COACH_SYSTEM / COACH_TURN_SYSTEM + helper render_* -> template
    prompt inferensi yang dipakai backend (mode Pelanggan & mode Pelatih) DAN saat
    flatten ke contoh SFT (2_prepare_sft.py).

Semua label diambil dari taxonomy (single source of truth) agar tidak drift.

PENTING: format prompt di bagian 2 adalah KONTRAK antara data latih dan inferensi.
Backend (`backend/app/llm.py`) me-mirror fungsi-fungsi ini; kalau diubah di sini,
ubah juga di sana — kalau tidak, model dilatih pada format yang berbeda dari yang
dilihatnya saat demo.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_taxonomy() -> dict:
    return json.loads((DATA_DIR / "taxonomy.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. PROMPT GENERATE DATA (LLM -> dialog berlabel)
# --------------------------------------------------------------------------- #

_FRAMEWORK_BRIEF = """\
Framework penjualan yang WAJIB kamu jadikan acuan saat menyusun & melabeli dialog:
- SPIN Selling: gali kebutuhan bertingkat (Situasi -> Masalah -> Implikasi -> Kebutuhan) SEBELUM menawarkan.
- AIDA: Attention (sapa) -> Interest/Desire (manfaat relevan) -> Action (closing).
- FAB: ubah Fitur menjadi Manfaat yang nyambung ke kebutuhan pelanggan.
- Objection handling: akui keberatan -> klarifikasi -> jawab dengan NILAI/BUKTI -> cek ulang. JANGAN langsung diskon, JANGAN memaksa, JANGAN defensif."""

_VARIAN_BRIEF = {
    "kuat": (
        "Semua turn 'sales' berkualitas 'baik': teknik tepat waktu, empatik, berbasis nilai. "
        "Alur mendekati ideal (sapa -> gali -> manfaat -> atasi keberatan -> closing, upsell bila wajar)."
    ),
    "campur": (
        "Sisipkan 2-3 turn 'sales' berkualitas 'lemah' (mis. langsung diskon saat dibilang mahal, "
        "monolog fitur tanpa gali kebutuhan, defensif, atau memaksa closing), lalu turn berikutnya "
        "PERBAIKI menjadi 'baik'. Tujuannya kontras mutu agar model belajar bedanya."
    ),
}


def _teknik_ringkas(tax: dict) -> str:
    return "\n".join(
        f"  - {t['id']}: {t['definisi']}" for t in tax["teknik"]["label"]
    )


def _keberatan_ringkas(tax: dict) -> str:
    return "\n".join(
        f"  - {k['id']}: {k['definisi']}" for k in tax["keberatan"]["global"]
    )


def build_generation_messages(cell: dict, tax: dict | None = None) -> list[dict]:
    """Susun messages (system+user) untuk generate satu dialog dari satu sel matriks."""
    tax = tax or load_taxonomy()
    persona = next(p for p in tax["persona"]["label"] if p["id"] == cell["persona"])
    bidang = tax["bidang"][cell["bidang"]]

    system = f"""Kamu adalah pakar pelatihan sales Indonesia yang membuat DATA LATIH dialog jualan \
di {bidang['konteks']}. Bahasa: Indonesia sehari-hari yang natural (boleh campur sedikit gaya \
percakapan toko), sopan, tidak kaku.

{_FRAMEWORK_BRIEF}

TEKNIK sales (label turn 'sales', pilih tepat satu per turn):
{_teknik_ringkas(tax)}

KEBERATAN pelanggan (label turn 'pelanggan' yang mengandung keberatan; null jika tidak ada):
{_keberatan_ringkas(tax)}

Kamu HANYA membalas JSON valid sesuai skema. Tanpa teks lain, tanpa markdown fence."""

    user = f"""Buat SATU dialog jualan lengkap untuk sel berikut:

- bidang: {cell['bidang']} ({bidang['nama']})
- produk: {cell['produk']}
- persona pelanggan: {persona['id']} — {persona['deskripsi']} (emosi awal: {persona['emosi_awal']})
- keberatan utama yang HARUS muncul: topik "{cell['topik_keberatan']}" \
(kategori global: {cell['keberatan_global']}). Contoh ucapan pemicu: "{cell['contoh_ucapan']}"
- varian mutu: {cell['varian_kualitas']} -> {_VARIAN_BRIEF[cell['varian_kualitas']]}

Ketentuan:
- 8-14 turn, umumnya bergantian mulai dari 'sales' (sapaan) lalu 'pelanggan'.
- SATU giliran sales = SATU teknik. Kalau satu ucapan sebenarnya melakukan dua teknik
  (mis. mengajak closing SEKALIGUS menawarkan aksesori), PECAH jadi dua giliran 'sales'
  berurutan dengan label masing-masing. Label yang menggabung dua teknik membuat penilaian
  sesi salah menyimpulkan ada teknik yang "tidak dipakai".
- Keberatan utama di atas WAJIB muncul minimal sekali dengan label keberatan yang sesuai.
- Setiap turn 'sales' WAJIB punya "teknik" dan "kualitas". Setiap turn 'pelanggan' WAJIB punya
  "keberatan" (isi label atau null) dan boleh "emosi".
- Realistis untuk konteks Indonesia: sebut harga/DP/cicilan/garansi/BBM secara wajar, jangan
  mengumbar janji palsu. Bingkai jualan ETIS (jujur, tidak manipulatif).
- Output PERSIS bentuk ini (isi turns sesuai dialog):

{{"scenario_id": "{cell['scenario_id']}", "bidang": "{cell['bidang']}", "produk": "{cell['produk']}", \
"persona": {{"tipe": "{persona['id']}", "emosi_awal": "{persona['emosi_awal']}"}}, \
"grounding": {{"framework": ["SPIN", "AIDA"], "generator": "<isi-nama-model>", "divalidasi_manusia": false}}, \
"turns": [{{"speaker": "sales", "text": "...", "teknik": "sapa_rapport", "kualitas": "baik"}}, \
{{"speaker": "pelanggan", "text": "...", "keberatan": null, "emosi": "netral"}}]}}"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# --------------------------------------------------------------------------- #
# 2. PROMPT INFERENSI (dipakai backend & saat flatten ke SFT)
# --------------------------------------------------------------------------- #

ROLEPLAY_SYSTEM = """Kamu memerankan PELANGGAN di {konteks}. Persona: {persona_tipe} \
({persona_desk}), emosi awal {emosi}. Produk yang sedang dilihat: {produk}. \
Balas SATU giliran saja sebagai pelanggan, natural dan konsisten dengan persona. \
Jangan memberi nasihat menjual; kamu pembeli, bukan pelatih."""

COACH_SYSTEM = """Kamu PELATIH sales. Nilai teknik jualan pada percakapan berikut. \
Untuk tiap giliran 'sales', tentukan teknik (sapa_rapport|gali_kebutuhan|presentasi_manfaat|\
atasi_keberatan|closing|upsell) dan kualitas (baik|lemah), lalu beri skor total 0-100 dan \
2-3 saran konkret. Balas HANYA JSON: \
{{"skor_total": int, "per_teknik": [{{"teknik": str, "skor": int, "catatan": str}}], "saran": [str]}}"""

COACH_TURN_SYSTEM = """Kamu PELATIH sales. Untuk SATU giliran sales, tentukan teknik \
(sapa_rapport|gali_kebutuhan|presentasi_manfaat|atasi_keberatan|closing|upsell) dan kualitas \
(baik|lemah). Balas HANYA JSON: {{"teknik": str, "kualitas": str}}"""

_SPEAKER_LABEL = {"sales": "Sales", "pelanggan": "Pelanggan"}


def _persona_id(persona) -> str:
    """Terima persona sebagai id string (sel matriks) atau dict (file dialog)."""
    return persona["tipe"] if isinstance(persona, dict) else persona


def roleplay_system(cell_or_scenario: dict, tax: dict | None = None) -> str:
    tax = tax or load_taxonomy()
    pid = _persona_id(cell_or_scenario["persona"])
    p = next(x for x in tax["persona"]["label"] if x["id"] == pid)
    konteks = tax["bidang"][cell_or_scenario["bidang"]]["konteks"]
    return ROLEPLAY_SYSTEM.format(
        konteks=konteks,
        persona_tipe=p["id"],
        persona_desk=p["deskripsi"],
        emosi=p["emosi_awal"],
        produk=cell_or_scenario["produk"],
    )


def render_transcript(turns: list[dict]) -> str:
    """Ubah daftar turn jadi transkrip datar. Terima key 'speaker' (dialog) atau 'role' (API)."""
    baris = []
    for t in turns:
        spk = t.get("speaker") or t.get("role")
        baris.append(f"{_SPEAKER_LABEL.get(spk, spk)}: {t['text'].strip()}")
    return "\n".join(baris)


def _konteks_baris(scenario: dict, tax: dict) -> str:
    bidang = tax["bidang"][scenario["bidang"]]
    return (
        f"Konteks: {bidang['nama']} — {bidang['konteks']} "
        f"Produk: {scenario['produk']}. Persona pelanggan: {_persona_id(scenario['persona'])}."
    )


def coach_session_user(scenario: dict, turns: list[dict], tax: dict | None = None) -> str:
    """User message mode Pelatih (penilaian SELURUH sesi) — dipakai backend /api/evaluate."""
    tax = tax or load_taxonomy()
    return (
        f"{_konteks_baris(scenario, tax)}\n\n"
        f"Percakapan:\n{render_transcript(turns)}\n\n"
        "Nilai percakapan di atas."
    )


def coach_turn_user(scenario: dict, konteks_turns: list[dict], sales_text: str, tax: dict | None = None) -> str:
    """User message mode Pelatih (label SATU giliran sales) — untuk eval F1 teknik."""
    tax = tax or load_taxonomy()
    sebelum = render_transcript(konteks_turns) if konteks_turns else "(awal percakapan)"
    return (
        f"{_konteks_baris(scenario, tax)}\n\n"
        f"Percakapan sebelumnya:\n{sebelum}\n\n"
        f"Giliran sales yang dinilai:\n{sales_text.strip()}"
    )
