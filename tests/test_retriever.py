import pytest
from unittest.mock import patch, MagicMock
from app.rag.retriever import retrieve


# ── retrieve ──────────────────────────────────────────────────────────────────

def _make_mock_nodes(*texts):
    nodes = []
    for text in texts:
        node = MagicMock()
        node.node.get_content.return_value = text
        nodes.append(node)
    return nodes


def test_retrieve_returns_list():
    with patch("app.rag.retriever._index") as mock_index:
        mock_index.as_retriever.return_value.retrieve.return_value = _make_mock_nodes("info1")
        result = retrieve("parking hours")
    assert isinstance(result, list)


def test_retrieve_returns_correct_count():
    with patch("app.rag.retriever._index") as mock_index:
        mock_index.as_retriever.return_value.retrieve.return_value = _make_mock_nodes("a", "b", "c")
        result = retrieve("test", top_k=3)
    assert len(result) == 3


def test_retrieve_result_contains_content():
    with patch("app.rag.retriever._index") as mock_index:
        mock_index.as_retriever.return_value.retrieve.return_value = _make_mock_nodes("open 24 hours")
        result = retrieve("parking hours")
    assert "open 24 hours" in result[0]


def test_retrieve_passes_top_k():
    with patch("app.rag.retriever._index") as mock_index:
        mock_retriever = mock_index.as_retriever.return_value
        mock_retriever.retrieve.return_value = []
        retrieve("query", top_k=2)
    mock_index.as_retriever.assert_called_once_with(similarity_top_k=2)


def test_retrieve_empty_results():
    with patch("app.rag.retriever._index") as mock_index:
        mock_index.as_retriever.return_value.retrieve.return_value = []
        result = retrieve("unknown query")
    assert result == []
