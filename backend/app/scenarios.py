"""Skenario latihan (hardcoded untuk MVP). 2 bidang: otomotif + elektronik.

`lanjutan` = balasan pelanggan bertahap yang dipakai MODE=mock. Di MODE=local
(M3), balasan dihasilkan LLM sehingga `lanjutan` tidak lagi dibutuhkan.
"""

from .schemas import Persona, Scenario, ScenarioSummary

_SCENARIOS: list[Scenario] = [
    # ---------------- Otomotif ----------------
    Scenario(
        id="otomotif_boros",
        bidang="otomotif",
        judul="Pelanggan khawatir boros BBM",
        produk="SUV 1.5L Turbo",
        persona=Persona(tipe="skeptis-hemat", deskripsi="Bapak berkeluarga, sangat memperhitungkan biaya bensin bulanan."),
        pembuka="Mobil segini boros nggak sih? Sebulan bisa habis berapa buat bensin?",
        keberatan=["boros_bbm", "dp_cicilan", "bandingkan_merk"],
        lanjutan=[
            "Tapi kan tetap lebih boros dari LCGC ya? Selisihnya lumayan buat sebulan.",
            "Hmm, kalau DP-nya berat nggak? Cicilan per bulan berapa kira-kira?",
            "Saya masih mau bandingkan sama merk sebelah dulu deh.",
        ],
    ),
    Scenario(
        id="otomotif_harga_jual",
        bidang="otomotif",
        judul="Ragu harga jual kembali",
        produk="Sedan kompak",
        persona=Persona(tipe="rasional", deskripsi="Pekerja kantoran, mikir nilai jual kembali dalam 5 tahun."),
        pembuka="Sedan ini kalau dijual lagi 5 tahun lagi jatuh harganya banyak nggak?",
        keberatan=["harga_jual_kembali", "bandingkan_merk", "harga"],
        lanjutan=[
            "Katanya sedan susah dijual lagi dibanding SUV, bener nggak?",
            "Kalau soal servis rutin mahal nggak per tahunnya?",
            "Oke, coba jelaskan kenapa saya harus ambil ini bukan yang lain.",
        ],
    ),
    Scenario(
        id="otomotif_lihat_lihat",
        bidang="otomotif",
        judul="Pelanggan cuma lihat-lihat",
        produk="MPV keluarga",
        persona=Persona(tipe="pasif", deskripsi="Datang ke showroom tanpa niat beli hari ini, sekadar survei."),
        pembuka="Saya cuma lihat-lihat aja dulu ya, belum tentu beli.",
        keberatan=["cuma_lihat_lihat", "mau_pikir_pikir", "harga"],
        lanjutan=[
            "Iya nanti aja deh, saya diskusi dulu sama istri.",
            "Kira-kira ada promo nggak bulan ini?",
            "Boleh minta brosur? Saya pikir-pikir dulu di rumah.",
        ],
    ),
    # ---------------- Elektronik ----------------
    Scenario(
        id="elektronik_harga_sebelah",
        bidang="elektronik",
        judul="Bandingkan harga toko sebelah",
        produk="TV LED 43 inch",
        persona=Persona(tipe="skeptis", deskripsi="Ibu rumah tangga, teliti soal harga dan garansi."),
        pembuka="Ini kok lebih mahal dari toko sebelah ya? Di sana lebih murah lho.",
        keberatan=["harga_toko_sebelah", "harga", "ragu_kualitas"],
        lanjutan=[
            "Tapi selisihnya lumayan lho, hampir 300 ribu.",
            "Garansinya berapa lama? Kalau rusak gimana?",
            "Oke deh, tapi bonusnya apa nih kalau ambil di sini?",
        ],
    ),
    Scenario(
        id="elektronik_spek",
        bidang="elektronik",
        judul="Bingung soal spesifikasi",
        produk="Laptop tipis",
        persona=Persona(tipe="awam", deskripsi="Mahasiswa, tidak paham spek teknis, butuh dipandu."),
        pembuka="Saya nggak ngerti spek-spek gini. Ini bagus buat kuliah nggak sih?",
        keberatan=["ragu_kualitas", "harga", "mau_pikir_pikir"],
        lanjutan=[
            "RAM 8GB itu cukup nggak buat tugas-tugas berat?",
            "Kalau dibanding yang lebih murah bedanya kerasa nggak?",
            "Hmm, budget saya pas-pasan sih sebenarnya.",
        ],
    ),
    Scenario(
        id="elektronik_garansi",
        bidang="elektronik",
        judul="Khawatir cepat rusak",
        produk="Mesin cuci front loading",
        persona=Persona(tipe="hati-hati", deskripsi="Bapak yang pernah kecewa produk cepat rusak."),
        pembuka="Mesin cuci gini biasanya cepet rusak nggak? Saya pernah kapok soalnya.",
        keberatan=["ragu_kualitas", "harga", "bandingkan_kompetitor"],
        lanjutan=[
            "Kalau rusak di luar garansi, servisnya mahal nggak?",
            "Merk ini beneran awet? Ada buktinya?",
            "Oke, tapi kenapa harus ambil yang ini bukan yang lebih murah?",
        ],
    ),
]


def list_scenarios() -> list[ScenarioSummary]:
    return [ScenarioSummary(id=s.id, bidang=s.bidang, judul=s.judul, produk=s.produk) for s in _SCENARIOS]


def get_scenario(scenario_id: str) -> Scenario | None:
    return next((s for s in _SCENARIOS if s.id == scenario_id), None)
