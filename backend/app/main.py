from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import coach, roleplay
from .config import settings
from .scenarios import get_scenario, list_scenarios
from .schemas import (
    ChatRequest,
    ChatResponse,
    EvaluateRequest,
    EvaluateResponse,
    Scenario,
    ScenarioSummary,
)

app = FastAPI(title="JagoJual API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": settings.mode}


@app.get("/api/scenarios", response_model=list[ScenarioSummary])
def scenarios() -> list[ScenarioSummary]:
    return list_scenarios()


@app.get("/api/scenarios/{scenario_id}", response_model=Scenario)
def scenario_detail(scenario_id: str) -> Scenario:
    s = get_scenario(scenario_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")
    return s


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    s = get_scenario(req.scenario_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")
    reply = roleplay.customer_reply(s, req.history, req.message)
    return ChatResponse(reply=reply)


@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    s = get_scenario(req.scenario_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Skenario tidak ditemukan")
    return coach.evaluate(s, req.history)
