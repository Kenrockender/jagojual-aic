from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_scenarios_listed():
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    assert {s["bidang"] for s in data} == {"otomotif", "elektronik"}


def test_chat_mock_reply():
    r = client.post("/api/chat", json={"scenario_id": "otomotif_boros", "message": "Halo Pak, mobil ini justru irit kok.", "history": [{"role": "pelanggan", "text": "boros?"}]})
    assert r.status_code == 200
    assert isinstance(r.json()["reply"], str) and r.json()["reply"]


def test_evaluate_mock():
    r = client.post("/api/evaluate", json={"scenario_id": "otomotif_boros", "history": [{"role": "sales", "text": "Selamat datang Pak, boleh saya bantu carikan sesuai kebutuhan?"}]})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["skor_total"] <= 100
    assert len(body["per_teknik"]) == 6
