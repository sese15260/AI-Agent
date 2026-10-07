import csv
from pathlib import Path

from fastapi.testclient import TestClient
from app import main
from app.summary import summarize


def test_dataset_is_real_sized_and_ordered():
    path = Path(__file__).parents[1] / "data" / "samsung_005930_daily.csv"
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) >= 100
    assert len({row["date"] for row in rows}) == len(rows)
    assert rows == sorted(rows, key=lambda row: row["date"])
    assert all(float(row["value"]) > 0 for row in rows)
    assert summarize(rows)["metrics"]["latest"] == float(rows[-1]["value"])


def test_endpoints_and_validation(monkeypatch):
    state = {"data": []}
    monkeypatch.setattr(main.store, "data_list", lambda: state["data"])
    monkeypatch.setattr(main.store, "data_create", lambda item: state["data"].append({**item.model_dump(mode="json"), "id": item.date.isoformat()}) or state["data"][-1])
    monkeypatch.setattr(main.store, "conversation_save", lambda title, messages, id=None: {"id": id or "c1", "title": title, "messages": messages})
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.post("/api/data", json={"date": "2026-01-01", "value": -1}).status_code == 422
    assert client.post("/api/data", json={"date": "2026-01-01", "value": 100, "memo": "test"}).status_code == 201
    assert client.get("/api/data/summary").json()["count"] == 1
    assert client.post("/api/conversations", json={"title": "기록", "messages": [{"role": "user", "content": "안녕"}]}).status_code == 201


def test_chat_injects_summary_and_saves(monkeypatch):
    rows = [{"id": "2026-01-01", "date": "2026-01-01", "value": 100.0, "memo": ""}, {"id": "2026-01-02", "date": "2026-01-02", "value": 105.0, "memo": ""}]
    saved = {}
    prompts = []
    monkeypatch.setattr(main.store, "data_list", lambda: rows)
    monkeypatch.setattr(main.store, "conversation_get", lambda id: None)
    def save(title, messages, id=None):
        saved.update({"title": title, "messages": messages})
        return {"id": "c1"}
    monkeypatch.setattr(main.store, "conversation_save", save)
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    class FakeResponses:
        def create(self, **kwargs):
            prompts.append(kwargs)
            return type("Response", (), {"output_text": "최근 종가는 105원입니다."})()
    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()
    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = TestClient(main.app).post("/api/chat", json={"message": "최근 종가는?"})
    assert response.status_code == 200
    assert response.json()["conversation_id"] == "c1"
    assert '"latest": 105.0' in prompts[0]["instructions"]
    assert prompts[0]["input"][-1]["role"] == "user"
    assert prompts[0]["store"] is False
    assert [m["role"] for m in saved["messages"]] == ["user", "assistant"]
