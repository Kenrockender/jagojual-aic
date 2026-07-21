"""Generator dialog LOKAL (tanpa API) — grounded ke taksonomi & framework sales.

Alternatif dari 1_generate_data.py (yang butuh endpoint LLM). Skrip ini membangun
dialog berlabel secara deterministik (seed tetap) dari bank kalimat sales nyata yang
di-grounding ke SPIN / AIDA / FAB / objection-handling (feel-felt-found). Dipakai
sebagai BOOTSTRAP supaya training bisa jalan tanpa kredensial LLM.

Setiap dialog:
  * mengikuti alur konsultatif: sapa -> gali -> presentasi -> (keberatan) -> atasi -> closing -> upsell
  * label per-turn (teknik, kualitas, keberatan) benar by construction
  * varian 'kuat'  -> semua turn sales `baik`
    varian 'campur'-> sebagian turn sales `lemah` (kontras mutu untuk rubrik)
  * keberatan utama sel (keberatan_global) dijamin muncul.

Pool kalimat sengaja dibuat kaya (banyak varian per slot) supaya diversitas bahasa
tinggi dan model tidak sekadar menghafal template.

Jalankan:
    python 1_generate_local.py            # tulis semua sel -> data/dialogs/
    python 1_generate_local.py --limit 5  # smoke test
Lalu validasi dgn pipeline resmi:
    python 1_generate_data.py --validate-only
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DIALOGS_DIR = DATA_DIR / "dialogs"
MATRIX = DATA_DIR / "scenario_matrix.json"

EMOSI_AWAL = {
    "skeptis": "ragu", "buru_buru": "tidak_sabar", "sensitif_harga": "hati_hati",
    "banyak_tanya": "penasaran", "loyal_merk_lain": "defensif", "cuma_lihat": "santai",
}
HORMAT = ["Pak", "Bu", "Kak", "Mas", "Mbak"]
NAMA_SALES = ["Adit", "Rina", "Bima", "Sari", "Deni", "Fitri", "Yoga", "Nadia", "Rizky", "Wulan"]

# --------------------------------------------------------------------------- #
# Profil produk: kebutuhan khas, manfaat (fitur->manfaat+angka), item upsell
# --------------------------------------------------------------------------- #
PRODUK = {
    "LCGC 1.000cc": {
        "pakai": ["harian ke kantor", "antar-jemput anak sekolah", "mobil pertama keluarga muda", "usaha online kecil-kecilan"],
        "manfaat": [
            "mesin 1.000cc-nya irit, rata-rata pemilik kami dapat 18-20 km/liter dalam kota",
            "pajak tahunannya rendah dan sparepart-nya murah serta gampang dicari di mana-mana",
            "bodinya ringkas jadi lincah dan gampang parkir di gang sempit atau mal penuh",
            "harga on the road-nya paling terjangkau di kelasnya, cocok untuk mobil pertama",
            "meski kecil, kabinnya sudah muat 5 orang dengan AC yang dingin merata",
        ],
        "upsell": ["paket kaca film + karpet dasar", "cicilan asuransi all-risk tahun pertama", "aksesori pelindung bodi"],
    },
    "MPV keluarga 7-seater": {
        "pakai": ["mudik dan jalan-jalan keluarga besar", "usaha travel/antar-jemput", "keluarga dengan tiga anak", "operasional kantor"],
        "manfaat": [
            "kabin 3 baris benar-benar muat 7 orang dan bagasinya masih lega untuk koper",
            "ground clearance-nya tinggi, aman lewat jalan rusak dan genangan saat hujan",
            "kursi baris kedua dan ketiga bisa dilipat rata untuk mengangkut barang besar",
            "fitur hiburannya lengkap, perjalanan jauh anak-anak jadi anteng",
            "konsumsi BBM-nya masih wajar untuk ukuran mobil sebesar ini, sekitar 11-12 km/liter",
        ],
        "upsell": ["paket peredam kabin + kamera mundur", "extended warranty mesin 5 tahun", "cover jok kulit sintetis"],
    },
    "SUV compact": {
        "pakai": ["gaya harian tapi sesekali luar kota", "keluarga muda yang suka touring", "jalan campur kota dan tol", "kerja lapangan"],
        "manfaat": [
            "posisi duduknya tinggi jadi pandangan luas dan lebih santai saat macet panjang",
            "mesin injeksi dengan mode Eco, rata-rata 13-14 km/liter untuk pemakaian dalam kota",
            "fitur keselamatannya lengkap: 6 airbag, rem ABS, dan kontrol stabilitas",
            "desainnya gagah dan ground clearance-nya cukup untuk jalan menantang",
            "bagasinya luas dan bisa diperluas, praktis untuk barang touring atau belanja bulanan",
        ],
        "upsell": ["paket pelindung cat + servis gratis 1 tahun", "roof rack untuk barang touring", "ban serep berkualitas + tools"],
    },
    "city car hatchback": {
        "pakai": ["mobilitas dalam kota yang padat", "anak muda yang baru kerja", "mobil kedua di rumah", "hilir mudik jarak pendek"],
        "manfaat": [
            "radius putarnya kecil, gampang muter dan nyelip parkir di area sempit",
            "konsumsi BBM-nya efisien 16-18 km/liter, ringan untuk pemakaian harian",
            "desainnya modern lengkap head unit layar sentuh dan koneksi ke HP",
            "bobotnya ringan jadi tarikannya responsif dan asyik di jalanan kota",
            "biaya perawatannya murah dan nilai jualnya tetap diminati anak muda",
        ],
        "upsell": ["paket audio + peredam pintu", "kaca film anti-panas merek ternama", "spoiler + velg ringan"],
    },
    "mobil bekas sertifikasi": {
        "pakai": ["budget terbatas tapi mau mobil layak", "kebutuhan cepat pakai", "pembeli pertama yang hati-hati", "tambahan armada usaha"],
        "manfaat": [
            "unit sudah lolos inspeksi 150 titik dan bergaransi mesin 1 tahun dari kami",
            "riwayat servisnya tercatat rapi dan kilometernya asli, bukan hasil putar-balik",
            "harganya jauh di bawah unit baru tapi kondisinya masih prima dan siap pakai",
            "surat-suratnya lengkap dan sudah kami bantu cek keasliannya, jadi aman",
            "kalau ada yang kurang sreg dalam 7 hari, ada kebijakan tukar unit dari kami",
        ],
        "upsell": ["paket detailing + ganti oli menyeluruh", "perpanjangan garansi mesin jadi 2 tahun", "asuransi TLO setahun"],
    },
    "TV LED 43 inch": {
        "pakai": ["ruang keluarga ukuran sedang", "nonton bola dan film akhir pekan", "upgrade dari TV tabung lama", "kamar utama yang luas"],
        "manfaat": [
            "panelnya sudah 4K dan Smart TV, langsung bisa YouTube dan Netflix tanpa alat tambahan",
            "sudah bergaransi resmi panel 2 tahun, bukan sekadar garansi toko",
            "warnanya tajam dan konsumsi listriknya hemat karena LED generasi baru",
            "suaranya sudah jernih dan ada mode film, nonton jadi lebih berasa bioskop",
            "bezel-nya tipis jadi layar terasa lebih luas untuk ukuran 43 inch",
        ],
        "upsell": ["bracket dinding + pemasangan rapi", "soundbar biar suara film lebih menggelegar", "stabilizer pelindung tegangan"],
    },
    "mesin cuci front-loading": {
        "pakai": ["keluarga dengan cucian menumpuk", "yang mau hemat air dan listrik", "apartemen dengan ruang terbatas", "usaha laundry kecil"],
        "manfaat": [
            "front-loading lebih hemat air dan deterjen, hasil cuciannya bersih dan lebih awet",
            "ada mode cepat 15 menit dan fitur pengering, praktis banget saat musim hujan",
            "motornya inverter, jadi lebih senyap dan bergaransi sampai 10 tahun",
            "putaran pengeringnya kencang, jemuran jadi cepat kering meski mendung",
            "programnya banyak, ada khusus untuk baju bayi dan bahan halus",
        ],
        "upsell": ["stacking kit + tutup pelindung", "layanan antar-pasang dan uji coba gratis", "voucher deterjen khusus front-loading"],
    },
    "AC 1 PK inverter": {
        "pakai": ["kamar tidur ukuran 3x4 meter", "yang tagihan listriknya sering bengkak", "ruang kerja di rumah", "kamar kos yang pengap"],
        "manfaat": [
            "teknologi inverter membuat listrik lebih hemat sampai 30% dibanding AC biasa",
            "dinginnya cepat terasa dan stabil, kompresornya bergaransi 5 tahun",
            "ada filter anti-bakteri, bagus untuk yang punya alergi atau anak kecil",
            "suaranya senyap jadi tidur tidak terganggu suara kompresor",
            "sudah dilengkapi mode hemat malam yang otomatis menyesuaikan suhu",
        ],
        "upsell": ["paket pasang + bracket + pipa berkualitas", "voucher servis cuci AC 2x setahun", "remote pintar kendali dari HP"],
    },
    "smartphone mid-range": {
        "pakai": ["yang butuh baterai awet untuk kerja seharian", "hobi foto dan sosmed", "ganti HP lama yang mulai lemot", "anak sekolah untuk belajar online"],
        "manfaat": [
            "baterainya 5000mAh plus fast charging, sekali cas tahan seharian penuh",
            "kameranya sudah ada OIS jadi hasil foto malam tetap tajam tidak gampang blur",
            "RAM-nya besar dan chipset-nya kencang, dijamin lancar 3-4 tahun ke depan",
            "layarnya sudah 90Hz jadi scroll dan game terasa mulus",
            "memorinya lega dan bisa ditambah kartu, tidak gampang penuh",
        ],
        "upsell": ["paket anti-gores + case original", "tukar tambah HP lama biar lebih hemat", "earbuds nirkabel dengan harga bundling"],
    },
    "kulkas 2 pintu": {
        "pakai": ["keluarga yang belanja stok mingguan", "yang sering menyimpan daging dan sayur", "upgrade dari kulkas 1 pintu", "usaha katering rumahan"],
        "manfaat": [
            "freezer-nya terpisah dan tidak menumpuk bunga es karena sudah no-frost",
            "hemat listrik dengan kompresor inverter yang bergaransi sampai 10 tahun",
            "rak kacanya kuat menahan beban dan ada laci sayur khusus biar sayur tetap segar",
            "kapasitasnya besar, stok belanjaan sebulan pun tertata rapi",
            "pintunya rapat dan ada mode hemat, dinginnya awet meski sering dibuka-tutup",
        ],
        "upsell": ["stabilizer biar aman dari tegangan naik-turun", "layanan antar plus buang kulkas lama gratis", "wadah penyimpan makanan set"],
    },
}

# --------------------------------------------------------------------------- #
# Profil topik keberatan: ucapan pelanggan + poin nilai untuk 'atasi' (baik)
# --------------------------------------------------------------------------- #
TOPIK = {
    "boros_bbm": {
        "ucapan": ["Mobil segini boros nggak sih bensinnya?", "Wah CC segini pasti minum bensin ya?",
                    "Takutnya boros nih buat harian, sebulan bisa habis berapa?",
                    "Kalau macet-macetan gini borosnya parah nggak?", "Jujur, saya paling takut soal konsumsi bensinnya."],
        "nilai": ["itu bukan angka brosur, melainkan catatan konsumsi pelanggan kami yang rutenya mirip Bapak/Ibu",
                   "nanti pas test drive kita nyalakan indikator konsumsi real-time, jadi Bapak/Ibu lihat sendiri angkanya",
                   "kuncinya di mode berkendara Eco yang otomatis mengatur bahan bakar saat macet",
                   "kalau dihitung per bulan, selisihnya dengan mobil lain sebenarnya tidak sebesar yang dibayangkan"],
    },
    "dp_cicilan": {
        "ucapan": ["DP-nya berat ya, cicilan per bulan berapa?", "Wah DP-nya kayaknya kemahalan buat saya.",
                    "Cicilannya kira-kira sanggup nggak ya sama gaji saya?", "Ada skema DP yang lebih ringan nggak?",
                    "Bunga cicilannya gede nggak nih totalnya?"],
        "nilai": ["kita ada skema DP ringan 20% atau DP 30% biar cicilannya lebih enteng, saya hitungkan simulasinya",
                   "ada promo bunga rendah bulan ini yang membuat total cicilannya jauh lebih ramah",
                   "tenornya bisa disesuaikan dengan kemampuan bulanan Bapak/Ibu, tidak harus dipaksakan",
                   "kalau berkenan, saya bantu simulasikan beberapa pilihan biar kelihatan mana yang paling pas di kantong"],
    },
    "bandingkan_merk": {
        "ucapan": ["Kalau dibanding merk sebelah kok lebih mahal?", "Merk sebelah lebih murah lho, kenapa harus ini?",
                    "Apa sih bedanya sama merk yang itu?", "Yang sebelah spesifikasinya kelihatan mirip tapi lebih murah.",
                    "Saya lagi timbang-timbang sama merk lain juga nih."],
        "nilai": ["selisihnya ada di nilai jual kembali dan jaringan bengkel resmi yang jauh lebih luas",
                   "kalau dibandingkan berdampingan, fitur keselamatan dan garansinya beda kelas",
                   "biaya kepemilikan jangka panjangnya justru lebih murah karena perawatannya terjangkau",
                   "yang sering tidak kelihatan di harga adalah after-sales-nya, dan di sini itu yang kami jaga"],
    },
    "harga_jual_kembali": {
        "ucapan": ["Nanti kalau dijual lagi harganya jatuh nggak?", "Depresiasinya gede nggak ya mobil ini?",
                    "Takut rugi banyak pas mau jual lagi nanti.", "Ini termasuk yang cepat turun harganya nggak?",
                    "Lima tahun lagi kira-kira sisa berapa persen harganya?"],
        "nilai": ["tipe ini termasuk yang harga bekasnya paling stabil karena peminatnya selalu banyak",
                   "asal servis rutin di bengkel resmi, nilai jualnya terjaga dan gampang laku lagi",
                   "kami juga punya program buyback yang bisa jadi acuan harga wajarnya nanti",
                   "riwayat servis yang tercatat rapi itu yang bikin harga jualnya tidak anjlok"],
    },
    "ruang_kabin": {
        "ucapan": ["Buat keluarga saya kayaknya kekecilan deh.", "Muat nggak ya buat kami sekeluarga plus barang?",
                    "Kabinnya sempit kelihatannya dari luar.", "Anak saya tiga, cukup nggak ruang belakangnya?",
                    "Kalau bawa barang banyak, bagasinya mepet nggak?"],
        "nilai": ["coba Bapak/Ibu duduk sendiri di baris belakang, ternyata ruang kakinya masih lega",
                   "kursinya bisa dikonfigurasi, jadi fleksibel antara muat orang atau muat barang",
                   "dimensinya memang ringkas di luar, tapi ruang dalamnya dirancang efisien",
                   "kalau kebutuhannya angkut barang besar sesekali, baris ketiga tinggal dilipat rata"],
    },
    "konsultasi_pasangan": {
        "ucapan": ["Saya diskusi dulu sama istri ya.", "Nanti saya tanya suami saya dulu deh.",
                    "Mau mikir-mikir dan omongin dulu di rumah.", "Ini keputusan besar, saya nggak bisa mutusin sendiri.",
                    "Saya pulang dulu, bahas sama keluarga."],
        "nilai": ["boleh banget, biar mantap saya siapkan ringkasan spesifikasi dan simulasi biaya untuk dibawa pulang",
                   "kalau berkenan saya bantu jadwalkan test drive bareng pasangan supaya bisa dicoba berdua",
                   "wajar kok, keputusan begini memang enaknya dibicarakan; saya kirimkan detailnya lewat WhatsApp ya",
                   "supaya diskusinya lebih gampang, saya catatkan poin-poin pentingnya biar tidak lupa"],
    },
    "harga_toko_sebelah": {
        "ucapan": ["Di toko sebelah kok lebih murah ya?", "Sebelah lebih murah lho, bisa turun harga nggak?",
                    "Kenapa di sini lebih mahal dari toko depan?", "Selisihnya lumayan lho sama yang di ujung.",
                    "Saya barusan dari sebelah, di sana lebih miring."],
        "nilai": ["unit kami garansi resmi pabrik 2 tahun plus antar-pasang gratis, itu yang membuat selisihnya",
                   "boleh dicek, yang di sebelah itu garansi toko atau garansi resmi? seringnya beda di situ",
                   "kami sertakan pemasangan oleh teknisi resmi, jadi tidak ada biaya tersembunyi belakangan",
                   "harga kami sudah termasuk layanan purna jual yang bisa Bapak/Ibu klaim kapan saja"],
    },
    "garansi": {
        "ucapan": ["Garansinya resmi apa toko? Berapa lama?", "Kalau rusak nanti garansinya gimana?",
                    "Takut cepat rusak terus susah klaim garansi.", "Klaim garansinya ribet nggak prosedurnya?",
                    "Sparepart-nya dijamin ada nggak kalau perlu ganti?"],
        "nilai": ["ini garansi resmi pabrik, klaimnya di service center resmi bukan di toko yang bisa tutup sewaktu-waktu",
                   "kartu garansinya kami aktifkan langsung atas nama Bapak/Ibu, jadi aman kalau ada apa-apa",
                   "prosedur klaimnya cukup bawa unit dan kartu, sisanya kami yang bantu urus",
                   "ketersediaan sparepart-nya terjamin karena merek ini punya jaringan resmi di seluruh Indonesia"],
    },
    "spek_bingung": {
        "ucapan": ["Saya bingung bedanya sama yang tipe satunya.", "Ini beda apa sih sama yang sebelahnya?",
                    "Speknya banyak, saya nggak ngerti mana yang cocok.", "Istilah-istilahnya asing buat saya.",
                    "Yang mana sih yang paling pas buat kebutuhan saya?"],
        "nilai": ["intinya bedanya cuma di dua hal yang berpengaruh ke pemakaian Bapak/Ibu, sisanya sama saja",
                   "biar gampang, saya cocokkan langsung dengan kebutuhan yang tadi Bapak/Ibu sebutkan",
                   "tidak usah pusing dengan angka-angkanya, saya terjemahkan ke manfaat sehari-hari saja",
                   "kalau tujuannya seperti yang tadi, tipe ini yang paling masuk akal, yang lain justru mubazir"],
    },
    "awet": {
        "ucapan": ["Merk ini awet nggak? Takut cepat rusak.", "Tahan berapa tahun biasanya?",
                    "Jangan-jangan setahun sudah rewel.", "Saya pernah kapok beli yang cepat rusak.",
                    "Komponennya bandel nggak buat pemakaian harian?"],
        "nilai": ["komponen utamanya bergaransi panjang, itu bentuk keyakinan pabrik terhadap keawetannya",
                   "asal pemakaian normal, rata-rata pelanggan kami memakainya bertahun-tahun tanpa keluhan",
                   "materialnya kelas atas dan ada perlindungan dari lonjakan listrik yang bikin lebih awet",
                   "kalau dirawat sesuai anjuran, usianya bisa jauh lebih panjang dari garansinya"],
    },
    "kemahalan": {
        "ucapan": ["Wah over budget saya nih.", "Kemahalan buat saya yang ini.",
                    "Ada yang lebih murah nggak? Ini di luar budget.", "Duh, selisihnya jauh dari yang saya siapkan.",
                    "Kalau segini mah saya mikir dua kali."],
        "nilai": ["kalau budgetnya pas, ada tipe satu level di bawah yang fungsinya mirip dan garansinya sama",
                   "bisa juga dicicil 0% beberapa bulan, jadi tidak berat di awal",
                   "kalau dihitung per hari selama pemakaian bertahun-tahun, sebenarnya nilainya sepadan",
                   "saya carikan yang sesuai kantong dulu, yang penting kebutuhan utamanya tetap terpenuhi"],
    },
    "lihat_lihat": {
        "ucapan": ["Lihat-lihat dulu aja mas.", "Belum mau beli sih, cuma lihat-lihat.",
                    "Santai aja dulu, lagi survei harga.", "Saya cuma mampir sebentar kok.",
                    "Belum ada rencana beli sekarang, sekadar lihat model."],
        "nilai": ["silakan, tidak apa-apa; biar tidak bingung, boleh saya tunjukkan dua pilihan terlaris saja?",
                   "sambil lihat-lihat, kalau ada yang mau ditanya soal spesifikasi atau promo saya siap bantu",
                   "nggak harus beli hari ini kok; saya kasih gambaran singkat biar nanti Bapak/Ibu mudah membandingkan",
                   "santai saja, saya temani sebentar biar kalau nanti butuh, Bapak/Ibu sudah punya bayangan"],
    },
}

# --------------------------------------------------------------------------- #
# Bank kalimat teknik (baik & lemah)
# --------------------------------------------------------------------------- #
def sapa_baik(hormat, produk, pakai, nama):
    return random.choice([
        f"Selamat siang, {hormat}. Silakan, ada yang bisa saya bantu? Lagi cari yang seperti apa nih?",
        f"Selamat datang, {hormat}. Lagi cari {produk} untuk keperluan apa? Biar saya bantu carikan yang pas.",
        f"Halo, {hormat}, silakan dilihat-lihat dulu. Kalau boleh tahu, ini untuk {pakai} atau ada kebutuhan lain?",
        f"Selamat datang, {hormat}. Saya {nama}, siap bantu. Lagi cari-cari {produk} ya?",
        f"Mari, {hormat}, silakan masuk. Kebetulan pas banget, boleh saya temani lihat-lihat {produk}-nya?",
        f"Selamat siang, {hormat}. Perkenalkan saya {nama}. Boleh tahu ini untuk dipakai sendiri atau untuk keluarga?",
        f"Halo {hormat}, apa kabar? Silakan, kalau ada yang menarik nanti saya jelaskan detailnya ya.",
        f"Selamat datang. Lagi cari {produk} nih, {hormat}? Biar tidak salah pilih, saya bantu sesuaikan dengan kebutuhannya ya.",
        f"Selamat siang, {hormat}, terima kasih sudah mampir. Ada model tertentu yang sudah diincar atau mau saya bantu carikan?",
    ])

def sapa_lemah(hormat, produk, nama):
    return random.choice([
        f"Mau beli apa? Ini {produk}-nya lagi promo, ambil aja mumpung murah.",
        f"Cari {produk} ya? Yang ini aja langsung, bagus kok, nggak usah mikir lama.",
        f"Iya {hormat} mau yang mana? Langsung saya buatkan nota ya biar cepat.",
        f"{produk}? Ada tuh di sana, lihat sendiri aja dulu ya.",
        "Mau yang mana? Semua bagus kok, tinggal pilih aja.",
        f"Beli sekarang {hormat}? Lagi diskon nih, sayang kalau kelewat.",
    ])

def gali_baik(produk, pakai):
    return random.choice([
        f"Boleh tahu biasanya dipakai untuk apa? Dan kira-kira sehari seberapa sering?",
        f"Sebelum saya sarankan, boleh saya tanya kebutuhannya dulu? Ini lebih ke {pakai}, atau ada prioritas lain?",
        "Kira-kira budget yang nyaman di kisaran berapa ya? Biar saya tunjukkan yang benar-benar pas, tidak kejauhan.",
        "Sekarang lagi pakai yang seperti apa? Ada yang kurang sreg dari yang sekarang, biar saya carikan solusinya?",
        f"Yang paling penting buat Bapak/Ibu apa nih, {pakai}, hemat biaya, atau kenyamanan? Biar saya prioritaskan.",
        "Rencananya dipakai berapa orang biasanya? Dan lebih sering dalam kota atau jarak jauh?",
        "Boleh cerita sedikit kebiasaan pemakaiannya? Dari situ saya bisa bantu pilihkan yang tidak mubazir.",
        f"Supaya rekomendasinya tepat, boleh saya tahu apa yang bikin Bapak/Ibu tertarik ke {produk} ini?",
        "Ada pengalaman kurang enak dengan produk sebelumnya? Biar yang ini benar-benar menjawab kebutuhannya.",
    ])

def gali_lemah(produk):
    return random.choice([
        f"Pokoknya {produk} ini paling laku, langsung ambil aja deh.",
        "Mau yang murah atau yang mahal? Sudah itu saja.",
        f"Nggak usah banyak mikir, {produk} ini semua orang cocok kok.",
        "Yang penting beli dulu, nanti juga terbiasa sendiri.",
        f"Ngapain ditanya-tanya, {produk} ini yang paling bagus, percaya saya.",
    ])

def presentasi_baik(produk, manfaat):
    return random.choice([
        f"Nah untuk kebutuhan tadi, {produk} ini pas: {manfaat}. Jadi langsung menjawab yang Bapak/Ibu butuhkan.",
        f"Kalau begitu ini cocok. {manfaat.capitalize()}. Artinya sehari-hari pemakaiannya lebih tenang.",
        f"Keunggulan utamanya yang relevan buat Bapak/Ibu begini: {manfaat}.",
        f"Yang bikin {produk} ini menonjol, {manfaat}, dan itu yang paling terasa manfaatnya di pemakaian harian.",
        f"Coba saya jelaskan yang paling nyambung dengan kebutuhan tadi: {manfaat}.",
        f"Dibanding pilihan lain, nilai lebih {produk} ada di sini: {manfaat}.",
    ])

def presentasi_lemah(produk):
    return random.choice([
        f"{produk} ini speknya tinggi, prosesornya kencang, layarnya bagus, fiturnya lengkap semua pokoknya.",
        f"Ini {produk} paling canggih, fiturnya dari A sampai Z ada, semua orang suka, bagus deh pokoknya.",
        "Ya bagus lah, kan mahal. Ada garansi, ada bonus, komplit.",
        f"Fiturnya banyak banget, ada ini itu, semua ada di {produk} ini. Percaya deh.",
        "Ini teknologinya terbaru, canggih, pokoknya nomor satu di kelasnya.",
    ])

def atasi_baik(hormat, nilai):
    return random.choice([
        f"Betul, {hormat}, wajar kalau ragu. Tapi begini: {nilai}. Gimana, sudah lebih jelas?",
        f"Saya paham kekhawatiran Bapak/Ibu. Banyak pelanggan awalnya berpikir sama, sampai tahu bahwa {nilai}.",
        f"Boleh saya jelaskan sedikit, {hormat}? {nilai.capitalize()}. Jadi ini bukan sekadar klaim.",
        f"Pertanyaan yang bagus, {hormat}. Justru di situ bedanya: {nilai}.",
        f"Saya mengerti maksud Bapak/Ibu. Izinkan saya luruskan: {nilai}.",
        f"Terima kasih sudah jujur, {hormat}. Nah, {nilai}, jadi bisa lebih tenang mempertimbangkannya.",
        f"Wajar banget dipikirkan. Kenyataannya, {nilai}, dan itu bisa Bapak/Ibu buktikan sendiri.",
    ])

def atasi_lemah(hormat):
    return random.choice([
        f"Yaudah {hormat} saya kasih diskon deh biar sama kayak yang lain.",
        "Ah itu mah tidak usah dipikirin, semua produk juga begitu kok.",
        "Percaya saja sama saya, dijamin tidak nyesel, sudah banyak yang beli.",
        f"Jangan ragu {hormat}, pokoknya bagus. Ambil aja dulu deh.",
        "Kalau soal itu sih relatif ya, tergantung orangnya. Yang penting ambil dulu.",
        "Masa tidak percaya sama saya? Ini barang bagus lho.",
    ])

def closing_baik(hormat, produk):
    aksi = random.choice(["simulasi cicilan", "jadwal antar", "test drive", "cek unit ready", "proses administrasi"])
    return random.choice([
        f"Kalau ini cocok, saya bisa langsung siapkan untuk hari ini juga, {hormat}. Mau saya proseskan?",
        f"Biar pas, Bapak/Ibu lebih nyaman ambil yang ini atau yang tadi satunya? Saya siapkan yang dipilih.",
        f"Gimana kalau kita lanjut ke {aksi} sekarang? Biar Bapak/Ibu makin mantap.",
        f"Kalau tidak ada yang mengganjal lagi, boleh saya bantu lanjutkan ke {aksi}, {hormat}?",
        f"Unitnya kebetulan masih ready. Mau saya amankan dulu untuk Bapak/Ibu?",
        f"Supaya tidak bolak-balik, sekalian saya bantu urus {aksi}-nya ya, {hormat}?",
        f"Menurut saya ini sudah paling sesuai kebutuhan tadi. Lanjut ke langkah berikutnya, {hormat}?",
    ])

def closing_lemah(hormat):
    return random.choice([
        f"Ayo dong {hormat} ambil sekarang, nanti kehabisan lho, buruan.",
        "Jadi beli tidak nih? Saya tunggu dari tadi soalnya.",
        "Sudah ini saja, langsung bayar ya, tidak usah kelamaan mikir.",
        f"Mumpung saya baik nih {hormat}, ambil sekarang ya, jangan ditunda-tunda.",
        "Kapan lagi ada harga segini? Pokoknya harus ambil hari ini.",
    ])

def upsell_baik(hormat, item):
    return random.choice([
        f"Sekalian, mau saya tambahkan {item}? Lumayan buat jaga-jaga dan menambah kenyamanan, cuma sedikit tambahan.",
        f"Kalau berkenan, {item} ini pas dengan kebutuhan Bapak/Ibu tadi, bikin lebih worth it. Saya masukkan ya?",
        f"Biar makin lengkap, banyak pelanggan menambahkan {item}. Mau saya siapkan sekalian?",
        f"Satu lagi yang biasanya berguna: {item}. Sifatnya opsional, tapi sayang kalau nanti nyari terpisah.",
        f"Supaya lebih tenang pemakaiannya, {item} bisa saya bundling dengan harga lebih baik. Mau?",
    ])

def upsell_lemah(item):
    return random.choice([
        f"Tambahin {item} juga ya, biar tokonya untung sedikit.",
        f"Beli {item} juga dong, mumpung di sini, nambah sedikit doang kok.",
        f"Ambil {item} sekalian lah, masa cuma beli itu doang.",
    ])

# --------------------------------------------------------------------------- #
# Kalimat pelanggan
# --------------------------------------------------------------------------- #
def cust_open(produk, pakai, persona):
    base = [
        f"Iya saya lagi cari {produk} buat {pakai}.",
        f"Ini lagi lihat-lihat {produk} yang cocok untuk {pakai}.",
        f"Lagi butuh {produk} nih, buat {pakai}.",
        f"Saya tertarik sama {produk} ini, kebetulan lagi perlu untuk {pakai}.",
    ]
    if persona == "buru_buru":
        base += [f"Langsung aja ya, saya cari {produk} buat {pakai}, yang bagus yang mana?"]
    if persona == "cuma_lihat":
        base += [f"Sebenarnya cuma lihat-lihat sih, tapi mungkin butuh {produk} buat {pakai}."]
    return random.choice(base)

def cust_neutral(persona):
    base = ["Iya, betul.", "Hmm, oke.", "Ya kira-kira begitu.", "Boleh, lanjut.",
            "Oh begitu.", "Iya sih.", "Paham-paham.", "Oke saya dengerin.",
            "Nah itu yang saya mau tahu.", "Iya, terus?"]
    if persona == "banyak_tanya":
        base += ["Oh iya? Terus kalau soal itu gimana?", "Boleh dijelaskan lebih detail?",
                 "Kalau yang tipe satunya beda jauh nggak?"]
    if persona == "buru_buru":
        base += ["Iya iya, terus?", "Oke cepetan, saya buru-buru.", "Langsung intinya aja deh."]
    if persona == "skeptis":
        base += ["Yakin nih?", "Hmm, masa sih?"]
    if persona == "loyal_merk_lain":
        base += ["Biasanya saya pakai merk lain sih.", "Merk sebelah katanya juga bagus."]
    return random.choice(base)

def cust_after_handle(persona):
    base = ["Oh begitu ya, oke masuk akal.", "Hmm boleh juga.", "Ya sudah kalau begitu.",
            "Oke, saya jadi lebih ngerti.", "Lumayan meyakinkan sih penjelasannya.",
            "Oke deh, itu poin yang bagus."]
    if persona == "skeptis":
        base = ["Hmm, tapi beneran ya?", "Oke... tapi saya masih agak ragu sih.",
                "Yaudah coba lihat dulu deh buktinya.", "Kedengarannya bagus, tapi harus saya cek."]
    if persona == "loyal_merk_lain":
        base = ["Biasanya saya pakai merk sebelah sih, tapi oke boleh dijelaskan.",
                "Hmm, beda juga ya ternyata.", "Oke, mulai kepikiran juga sih."]
    if persona == "buru_buru":
        base = ["Oke oke, paham. Lanjut.", "Ya udah, intinya oke lah."]
    return random.choice(base)

def cust_agree(persona):
    base = ["Oke deh, saya ambil.", "Yaudah kalau begitu saya jadi.", "Boleh, kita lanjut.",
            "Oke, saya mau yang ini.", "Sip, proses saja.", "Baik, saya sepakat."]
    if persona == "cuma_lihat":
        base = ["Yaudah deh, boleh lihat lebih lanjut.", "Oke deh, saya pikirkan serius nih jadinya.",
                "Menarik juga, boleh saya pertimbangkan dengan serius."]
    if persona == "buru_buru":
        base = ["Oke cepetan proses ya.", "Yaudah gas, saya ambil."]
    if persona == "sensitif_harga":
        base = ["Oke, kalau harganya segitu saya ambil.", "Yaudah kalau cicilannya masuk, saya jadi."]
    return random.choice(base)


def build_dialog(cell: dict, rng: random.Random) -> dict:
    # Seed modul random secara deterministik dari rng sel supaya reprodusibel.
    random.seed(rng.getrandbits(64))
    bidang = cell["bidang"]
    produk = cell["produk"]
    topik = cell["topik_keberatan"]
    keb_global = cell["keberatan_global"]
    persona = cell["persona"]
    kuat = cell["varian_kualitas"] == "kuat"
    hormat = random.choice(HORMAT)
    nama = random.choice(NAMA_SALES)
    pinfo = PRODUK[produk]
    tinfo = TOPIK[topik]
    pakai = random.choice(pinfo["pakai"])
    manfaat = random.choice(pinfo["manfaat"])
    item = random.choice(pinfo["upsell"])
    obj_line = random.choice(tinfo["ucapan"])

    obj_di_awal = random.random() < 0.4
    turns: list[dict] = []

    def sales(teknik, teks_baik_fn, teks_lemah_fn, force_baik=False):
        lemah = (not kuat) and (not force_baik) and random.random() < 0.55
        if kuat and random.random() < 0.12:
            lemah = True
        teks = teks_lemah_fn() if lemah else teks_baik_fn()
        turns.append({"speaker": "sales", "text": teks,
                      "teknik": teknik, "kualitas": "lemah" if lemah else "baik"})

    def cust(text, keberatan=None, emosi="netral"):
        turns.append({"speaker": "pelanggan", "text": text, "keberatan": keberatan, "emosi": emosi})

    # 1. sapa
    sales("sapa_rapport", lambda: sapa_baik(hormat, produk, pakai, nama), lambda: sapa_lemah(hormat, produk, nama))
    # 2. pembuka pelanggan
    if obj_di_awal:
        cust(f"{random.choice(['Saya lagi lihat', 'Lagi naksir', 'Kebetulan lagi cari'])} {produk} nih. {obj_line}",
             keberatan=keb_global, emosi=EMOSI_AWAL[persona])
    else:
        cust(cust_open(produk, pakai, persona), keberatan=None, emosi=EMOSI_AWAL[persona])
    # 3. gali
    sales("gali_kebutuhan", lambda: gali_baik(produk, pakai), lambda: gali_lemah(produk))
    cust(cust_neutral(persona))
    if persona == "banyak_tanya" and random.random() < 0.6:
        sales("gali_kebutuhan", lambda: gali_baik(produk, pakai), lambda: gali_lemah(produk))
        cust(cust_neutral(persona))
    # 4. presentasi
    sales("presentasi_manfaat", lambda: presentasi_baik(produk, manfaat), lambda: presentasi_lemah(produk))
    # 5. keberatan utama
    if not obj_di_awal:
        cust(obj_line, keberatan=keb_global, emosi="hati_hati" if persona == "sensitif_harga" else "ragu")
    else:
        cust(cust_after_handle(persona), emosi="netral")
    # 6. atasi
    sales("atasi_keberatan", lambda: atasi_baik(hormat, random.choice(tinfo["nilai"])), lambda: atasi_lemah(hormat))
    cust(cust_after_handle(persona), emosi="tertarik")
    # keberatan sekunder (sebagian dialog)
    if random.random() < 0.3 and keb_global != "harga":
        cust(random.choice(["Tapi tetap agak mahal ya.", "Cuma budget saya agak mepet sih.",
                            "Harganya masih di atas rencana saya nih."]),
             keberatan="harga", emosi="ragu")
        sales("atasi_keberatan",
              lambda: atasi_baik(hormat, "bisa dicicil ringan atau ada tipe yang lebih ramah budget dengan fungsi mirip"),
              lambda: atasi_lemah(hormat))
        cust(cust_after_handle(persona), emosi="netral")
    # 7. closing
    sales("closing", lambda: closing_baik(hormat, produk), lambda: closing_lemah(hormat))
    cust(cust_agree(persona), emosi="tertarik")
    # 8. upsell (kadang absen)
    if random.random() < 0.75:
        sales("upsell", lambda: upsell_baik(hormat, item), lambda: upsell_lemah(item))

    # jaminan keberatan utama muncul
    if keb_global not in {t.get("keberatan") for t in turns}:
        for i, t in enumerate(turns):
            if t["speaker"] == "sales" and t["teknik"] == "atasi_keberatan":
                turns.insert(i, {"speaker": "pelanggan", "text": obj_line,
                                 "keberatan": keb_global, "emosi": "ragu"})
                break

    return {
        "scenario_id": cell["scenario_id"],
        "bidang": bidang,
        "produk": produk,
        "persona": {"tipe": persona, "emosi_awal": EMOSI_AWAL[persona]},
        "grounding": {"framework": ["SPIN", "AIDA", "FAB", "objection-handling"],
                       "generator": "grounded-local-v2", "divalidasi_manusia": False},
        "turns": turns,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cells = json.loads(MATRIX.read_text(encoding="utf-8"))["sel"]
    if args.limit:
        cells = cells[: args.limit]
    DIALOGS_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for cell in cells:
        cell_rng = random.Random(f"{args.seed}:{cell['scenario_id']}")
        d = build_dialog(cell, cell_rng)
        (DIALOGS_DIR / f"{cell['scenario_id']}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"tulis {n} dialog -> {DIALOGS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
