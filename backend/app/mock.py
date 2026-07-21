"""Mock mode — balasan & penilaian dari skrip/heuristik sederhana.

Tujuannya: aplikasi tetap bisa dijalankan panitia TANPA GPU/model (syarat
reproducibility). Logika di sini SENGAJA dangkal; penilaian sesungguhnya
dikerjakan LLM fine-tuned di MODE=local.

Karena `catatan` ikut tampil di UI, teksnya harus menyatakan dengan jelas bahwa
angka ini berasal dari heuristik — bukan dari model.
"""

import random

from .schemas import ChatMessage, EvaluateResponse, Scenario, TEKNIK, TeknikScore

_GENERIK = [
    "Hmm, saya masih perlu pikir-pikir dulu.",
    "Oke, terus kelebihannya dibanding yang lain apa?",
    "Kalau soal harga masih bisa nego nggak?",
    "Iya sih, tapi saya belum yakin.",
]

_KATA_KUNCI = {
    "sapa_rapport": ["selamat", "halo", "silakan", "pak", "bu", "terima kasih", "perkenalkan"],
    "gali_kebutuhan": ["butuh", "cari", "untuk", "kebutuhan", "biasanya", "sehari-hari", "berapa"],
    "presentasi_manfaat": ["garansi", "hemat", "fitur", "kualitas", "manfaat", "keunggulan", "awet"],
    "atasi_keberatan": ["memang", "justru", "karena", "sebenarnya", "faktanya", "tenang"],
    "closing": ["ambil", "order", "hari ini", "booking", "dp", "bawa pulang", "deal"],
    "upsell": ["sekalian", "tambah", "paket", "bonus", "aksesori", "cicilan", "asuransi"],
}


def mock_customer_reply(scenario: Scenario, history: list[ChatMessage], message: str) -> str:
    # Berapa kali pelanggan sudah bicara (pembuka dihitung 1)
    prior_pelanggan = [m for m in history if m.role == "pelanggan"]
    idx = max(0, len(prior_pelanggan) - 1)
    if idx < len(scenario.lanjutan):
        return scenario.lanjutan[idx]
    return random.choice(_GENERIK)


def mock_evaluate(scenario: Scenario, history: list[ChatMessage]) -> EvaluateResponse:
    sales_turns = [m for m in history if m.role == "sales"]
    n = len(sales_turns)
    text = " ".join(m.text.lower() for m in sales_turns)

    def skor(teknik: str) -> int:
        hits = sum(1 for k in _KATA_KUNCI[teknik] if k in text)
        return int(min(100, 45 + hits * 18 + min(n, 3) * 5))

    per = [
        TeknikScore(teknik=t, skor=skor(t), catatan="Mode contoh: skor dari pencocokan kata kunci, bukan penilaian model.")
        for t in TEKNIK
    ]
    total = round(sum(p.skor for p in per) / len(per))
    saran = [
        "Gali kebutuhan pelanggan lebih dalam sebelum menawarkan produk.",
        "Saat menjawab keberatan harga, tekankan nilai total (garansi, layanan), bukan sekadar 'lebih murah'.",
        "Tutup percakapan dengan ajakan closing yang konkret (mis. penawaran khusus hari ini).",
    ]
    return EvaluateResponse(skor_total=total, per_teknik=per, saran=saran)
