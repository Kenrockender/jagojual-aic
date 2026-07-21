from typing import Literal

from pydantic import BaseModel

Bidang = Literal["otomotif", "elektronik"]
Role = Literal["sales", "pelanggan"]

# Taksonomi teknik jualan — SAMA di semua bidang (lihat PLAN.md §6).
TEKNIK = [
    "sapa_rapport",
    "gali_kebutuhan",
    "presentasi_manfaat",
    "atasi_keberatan",
    "closing",
    "upsell",
]


class Persona(BaseModel):
    tipe: str
    deskripsi: str
    # Ikut masuk prompt role-play (lihat prompts.ROLEPLAY_SYSTEM) — bukan label
    # klasifikasi, hanya penanda nada awal pelanggan.
    emosi_awal: str = "netral"


class ScenarioSummary(BaseModel):
    id: str
    bidang: Bidang
    judul: str
    produk: str


class Scenario(ScenarioSummary):
    persona: Persona
    pembuka: str  # kalimat pembuka pelanggan
    keberatan: list[str]
    lanjutan: list[str] = []  # balasan pelanggan bertahap (dipakai mock mode)


class ChatMessage(BaseModel):
    role: Role
    text: str


class ChatRequest(BaseModel):
    scenario_id: str
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


class EvaluateRequest(BaseModel):
    scenario_id: str
    history: list[ChatMessage] = []


class TeknikScore(BaseModel):
    teknik: str
    skor: int
    catatan: str


class EvaluateResponse(BaseModel):
    skor_total: int
    per_teknik: list[TeknikScore]
    saran: list[str]
