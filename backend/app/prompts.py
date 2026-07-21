"""Prompt inferensi — sisi backend.

⚠️ KONTRAK: file ini me-mirror bagian inferensi `model/training/prompts.py`. Adapter
LoRA dilatih pada format PERSIS ini; kalau salah satu diubah tanpa yang lain, model
melihat format yang berbeda dari yang dilatihkan dan mutu penilaian turun tanpa error
yang kelihatan. Ubah keduanya bersamaan.

Sengaja dipisah dari `llm.py` supaya bisa diuji tanpa torch/GPU terpasang.
"""

from .schemas import ChatMessage, Scenario

# Konteks per bidang — selaras `data/taxonomy.json` -> bidang[*].nama / .konteks.
BIDANG = {
    "otomotif": {"nama": "Otomotif (mobil)", "konteks": "Showroom / dealer mobil."},
    "elektronik": {"nama": "Elektronik & gadget", "konteks": "Toko elektronik / pramuniaga."},
}

ROLEPLAY_SYSTEM = """Kamu memerankan PELANGGAN di {konteks}. Persona: {persona_tipe} \
({persona_desk}), emosi awal {emosi}. Produk yang sedang dilihat: {produk}. \
Balas SATU giliran saja sebagai pelanggan, natural dan konsisten dengan persona. \
Jangan memberi nasihat menjual; kamu pembeli, bukan pelatih."""

COACH_SYSTEM = """Kamu PELATIH sales. Nilai teknik jualan pada percakapan berikut. \
Untuk tiap giliran 'sales', tentukan teknik (sapa_rapport|gali_kebutuhan|presentasi_manfaat|\
atasi_keberatan|closing|upsell) dan kualitas (baik|lemah), lalu beri skor total 0-100 dan \
2-3 saran konkret. Balas HANYA JSON: \
{"skor_total": int, "per_teknik": [{"teknik": str, "skor": int, "catatan": str}], "saran": [str]}"""

_SPEAKER_LABEL = {"sales": "Sales", "pelanggan": "Pelanggan"}


def render_transcript(history: list[ChatMessage]) -> str:
    return "\n".join(f"{_SPEAKER_LABEL.get(m.role, m.role)}: {m.text.strip()}" for m in history)


def roleplay_system(scenario: Scenario) -> str:
    b = BIDANG.get(scenario.bidang, {"konteks": scenario.bidang})
    return ROLEPLAY_SYSTEM.format(
        konteks=b["konteks"],
        persona_tipe=scenario.persona.tipe,
        persona_desk=scenario.persona.deskripsi,
        emosi=scenario.persona.emosi_awal,
        produk=scenario.produk,
    )


def _konteks_baris(scenario: Scenario) -> str:
    b = BIDANG.get(scenario.bidang, {"nama": scenario.bidang, "konteks": ""})
    return (
        f"Konteks: {b['nama']} — {b['konteks']} "
        f"Produk: {scenario.produk}. Persona pelanggan: {scenario.persona.tipe}."
    )


def coach_session_user(scenario: Scenario, history: list[ChatMessage]) -> str:
    return (
        f"{_konteks_baris(scenario)}\n\n"
        f"Percakapan:\n{render_transcript(history)}\n\n"
        "Nilai percakapan di atas."
    )


def roleplay_messages(scenario: Scenario, history: list[ChatMessage]) -> list[dict]:
    """Mode Pelanggan: seluruh percakapan jadi satu user turn, sama seperti saat latih."""
    return [
        {"role": "system", "content": roleplay_system(scenario)},
        {"role": "user", "content": render_transcript(history)},
    ]


def coach_messages(scenario: Scenario, history: list[ChatMessage]) -> list[dict]:
    return [
        {"role": "system", "content": COACH_SYSTEM},
        {"role": "user", "content": coach_session_user(scenario, history)},
    ]
