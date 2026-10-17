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
    summary = summarize(rows)
    assert summary["metrics"]["latest"] == float(rows[-1]["value"])
    assert len(summary["recent"]) == 20
    assert len(summary["monthly"]) >= 12


def test_endpoints_and_validation(monkeypatch):
    monkeypatch.setenv("SITE_ACCESS_TOKEN", "test-access-key")
    state = {"data": []}
    monkeypatch.setattr(main.store, "data_list", lambda: state["data"])
    monkeypatch.setattr(main.store, "data_create", lambda item: state["data"].append({**item.model_dump(mode="json"), "id": item.date.isoformat()}) or state["data"][-1])
    monkeypatch.setattr(main.store, "conversation_save", lambda title, messages, id=None: {"id": id or "c1", "title": title, "messages": messages})
    client = TestClient(main.app, headers={"X-Access-Key": "test-access-key"})
    assert client.get("/health").status_code == 200
    assert TestClient(main.app).get("/api/data").status_code == 200
    assert TestClient(main.app).get("/api/data/summary").status_code == 200
    assert TestClient(main.app).post("/api/data", json={"date": "2026-01-01", "value": 100}).status_code == 401
    assert TestClient(main.app, headers={"X-Access-Key": "wrong"}).get("/api/conversations").status_code == 401
    assert TestClient(main.app).get("/docs").status_code == 200
    schema = TestClient(main.app).get("/openapi.json")
    assert schema.status_code == 200
    assert schema.json()["components"]["securitySchemes"]["AccessKey"]["name"] == "X-Access-Key"
    assert "security" not in schema.json()["paths"]["/api/data"]["get"]
    assert "security" not in schema.json()["paths"]["/api/chat"]["post"]
    assert schema.json()["paths"]["/api/data"]["post"]["security"] == [{"AccessKey": []}]
    assert client.get("/docs").status_code == 200
    assert client.post("/api/data", json={"date": "2026-01-01", "value": -1}).status_code == 422
    assert client.post("/api/data", json={"date": "2026-01-01", "value": 100, "memo": "test"}).status_code == 201
    assert client.get("/api/data/summary").json()["count"] == 1
    assert client.post("/api/conversations", json={"title": "기록", "messages": [{"role": "user", "content": "안녕"}]}).status_code == 201


def test_chat_injects_summary_and_saves(monkeypatch):
    monkeypatch.setenv("SITE_ACCESS_TOKEN", "test-access-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://copa.codyssey.kr/v1")
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
    client_options = {}
    class FakeCompletions:
        def create(self, **kwargs):
            prompts.append(kwargs)
            return type("Completion", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "최근 종가는 105원입니다."})()})()]})()
    class FakeClient:
        def __init__(self, **kwargs):
            client_options.update(kwargs)
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()
    monkeypatch.setattr(main, "OpenAI", FakeClient)
    response = TestClient(main.app).post("/api/chat", json={"message": "최근 종가는?"})
    assert response.status_code == 200
    assert response.json()["conversation_id"] == "c1"
    assert client_options["base_url"] == "https://copa.codyssey.kr/v1"
    assert '"latest": 105.0' in prompts[0]["messages"][0]["content"]
    assert prompts[0]["messages"][-1]["role"] == "user"
    assert prompts[0]["model"] == "gpt-5-mini"
    assert prompts[0]["max_completion_tokens"] == 500
    assert [m["role"] for m in saved["messages"]] == ["user", "assistant"]
