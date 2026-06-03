import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage


@pytest.fixture
def client():
    with patch("app.agent.agent.agent_builder") as mock_builder:
        mock_agent = MagicMock()
        mock_builder.compile.return_value = mock_agent

        from app.app import app
        return TestClient(app)


# ── GET / ─────────────────────────────────────────────────────────────────────

def test_root_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# ── POST /chat ────────────────────────────────────────────────────────────────

def test_chat_returns_reply():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [AIMessage(content="We have spots available.")]
    }

    with patch("app.app.agent", mock_agent):
        from app.app import app
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "sess1", "message": "Any spots?"})

    assert response.status_code == 200
    assert response.json()["reply"] == "We have spots available."

def test_chat_passes_session_id_as_thread_id():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [AIMessage(content="Hello!")]
    }

    with patch("app.app.agent", mock_agent):
        from app.app import app
        client = TestClient(app)
        client.post("/chat", json={"session_id": "my-session", "message": "Hi"})

    call_kwargs = mock_agent.ainvoke.call_args
    config = call_kwargs[1]["config"] if "config" in call_kwargs[1] else call_kwargs[0][1]
    assert config["configurable"]["thread_id"] == "my-session"

def test_chat_missing_fields_returns_422():
    with patch("app.app.agent", AsyncMock()):
        from app.app import app
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hi"})

    assert response.status_code == 422

def test_chat_agent_error_returns_500():
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = Exception("LLM unavailable")

    with patch("app.app.agent", mock_agent):
        from app.app import app
        client = TestClient(app)
        response = client.post("/chat", json={"session_id": "s1", "message": "Hi"})

    assert response.status_code == 500
