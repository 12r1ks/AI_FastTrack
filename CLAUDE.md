## Personal Guidelines

@~/.claude/CLAUDE.md

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A parking space reservation chatbot built in Python using LangChain, LangGraph, and RAG. Users interact with a chatbot to get parking info and make reservations; requests are escalated to a human admin for approval; confirmed reservations are persisted via an MCP server.

## Tech Stack

- **Language**: Python 3.13
- **Frameworks**: LangChain, LangGraph, FastAPI
- **Architecture**: RAG (Retrieval-Augmented Generation) orchestrated by LangGraph
- **Vector DB**: FAISS via LlamaIndex (`llama-index-vector-stores-faiss`) — **not** `langchain-community`
- **Embeddings**: HuggingFace `BAAI/bge-small-en-v1.5` (local, no API key needed)
- **Relational DB**: SQLite (async via SQLAlchemy + aiosqlite)
- **LLM**: Anthropic (`claude-haiku-4-5-20251001`) / OpenAI (`gpt-4o`) — switchable via `LLM_PROVIDER` env var
- **Frontend**: Vanilla HTML/JS served by FastAPI (`app/frontend/chat.html`, `app/frontend/admin.html`)
- **Testing**: pytest + pytest-asyncio (`asyncio_mode = "auto"`)
- **Eval**: RAGAS (`eval/` directory, requires `OPENAI_API_KEY`)

## Commands

```bash
uv sync                                         # install / sync dependencies
uv add <package>                                # add a dependency

uv run uvicorn app.app:app --reload             # run the app (entry point is app/app.py)
uv run pytest                                   # run all tests
uv run pytest tests/test_nodes.py              # run a single test file
uv run pytest tests/test_nodes.py::test_init_node_resets_llm_calls  # run one test

uv run python -m app.rag.indexing               # rebuild the FAISS vector index from seed_parking_info.md
uv run python -m app.SQLite.db                  # create database tables
uv run python -m app.SQLite.seed_db             # reset and seed the database with spots/bookings

uv run python -m eval.eval_rag                  # run RAGAS evaluation (requires OPENAI_API_KEY)
uv run python -m eval.report                    # generate HTML report from eval/results.csv
```

## Architecture (Current: Stage 1)

The system is a 4-stage pipeline orchestrated by LangGraph. **Stage 1 (RAG Chatbot) is implemented.**

```
User → [Agent 1: RAG Chatbot] → [Agent 2: Admin Agent] → [MCP Server] → reservations.txt
                ↑
            (Stage 1 only)
```

### LangGraph Graph (Stage 1)

```
START → init → guard_route → llm_call → should_continue → tool_node → llm_call (loop)
                    ↓                          ↓
                 reject                   pre_end_guard → END
```

- **init**: resets `llm_calls` counter to 0 on each request
- **guard_route**: structured-output classifier — routes to `reject` for off-topic/adversarial input
- **llm_call**: main LLM node with tool-binding; injects system prompt with current time and reservation state
- **tool_node**: dispatches tool calls; updates `proposed_reservation` in state when reservation tool fires
- **pre_end_guard**: output filter that masks phone numbers via regex before returning to user
- **reject**: returns a canned parking-only message

The graph is compiled **twice**:
- `agent.py` exports `agent` (no checkpointer) — used by the eval script
- `app.py` imports `agent_builder` and recompiles it with `InMemorySaver` — this is what handles HTTP requests

`InMemorySaver` is intentional throughout — this is a mentor-review project, not production. It fully supports `interrupt()`/resume within the same process. `SqliteSaver` would only matter if the server restarted between admin notification and response.

### Tools

| Tool | Description |
|---|---|
| `Price_Calculator` | Calculates cost from hours/days at fixed rates |
| `Retrieve_data_from_company_database` | LlamaIndex FAISS retrieval of static parking info |
| `query_available_spots` | Async SQLAlchemy query for available spots by location/time/type |
| `store_or_update_info_for_parking_proposal` | Validates and stores reservation details into graph state |

### Data Stores

- **FAISS index** (`app/db/faiss_vector_store/`) — static parking info seeded from `app/rag/seed_parking_info.md`; rebuilt with `python -m app.rag.indexing`
- **SQLite** (`app/db/Dynamic_SQLite_DB.db`) — two tables: `spots` (A/B/T types, east/central locations) and `BOOKINGS` (reservations + blocks)

### State Schema (`MessagesState`)

Key fields beyond `messages`: `llm_calls` (loop guard), `proposed_reservation` (dict from reservation tool), `reservation_status`, `is_admin`.

## Specification Files

- General requirements: [`Documents/general.md`](Documents/general.md)
- Stage 1 — RAG Chatbot: [`Documents/stage1.md`](Documents/stage1.md)
- Stage 2 — Human-in-the-Loop: [`Documents/stage2.md`](Documents/stage2.md)
- Stage 3 — MCP Server: [`Documents/stage3.md`](Documents/stage3.md)
- Stage 4 — LangGraph Orchestration: [`Documents/stage4.md`](Documents/stage4.md)


## Framework Rules

@.claude/rules/langchain-langgraph.md
@.claude/rules/fastapi.md
@.claude/rules/llamaindex.md
@.claude/rules/ragas.md

## Skills

- `/check-stage-ready [N]` — verify stage N is complete before mentor submission (runs tests, checks all files)
- `/sync-framework-rules [framework]` — fetch current docs and update `.claude/rules/<framework>.md`

## Subagents

- `test-writer` — writes pytest tests for a given module (invoke: "write tests for app/db/models.py")
