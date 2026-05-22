# Stage 1 — RAG Chatbot: Implementation Plan

**Goal:** Working parking chatbot — users can ask about parking info and start a reservation via chat. FastAPI serves the UI. LangGraph manages conversation state from message one.

---

## Task 1: Project setup
- Init uv project, install all dependencies
- Create `config.py`: load env vars, `get_llm()` (Anthropic/OpenAI switchable), `get_embeddings()` (OpenAI)
- Verify all imports work

## Task 2: SQLite models
- `app/db/models.py`: `create_tables()` + `get_connection()`
- Tables: `parking_spaces`, `availability_slots`, `reservations`
- Tests: table creation, basic insert/read

## Task 3: Dynamic seed data
- `app/seed/dynamic_seed.py`: populate 10 spaces (Zone A + B), 30 days of availability slots
- Run and verify counts

## Task 4: Static seed + FAISS index
- `app/seed/static_seed.py`: 6 documents (general info, location, hours, pricing, rules, FAQ)
- `app/rag/retriever.py`: `get_retriever()` — load FAISS index, return MMR retriever
- Build index, tests: retriever returns results

## Task 5: LangGraph state schema
- `app/agent/state.py`: `State` TypedDict — messages, intent, reservation, approval_status

## Task 6: Agent nodes
- `app/agent/nodes.py`:
  - `router_node` — classifies last message as `"info"` or `"reservation"` via LLM
  - `rag_node` — retrieves from FAISS + queries SQLite for dynamic context, generates response
  - `collect_details_node` — walks through missing reservation fields (name, surname, car number, datetime from/to), confirms when complete
- Tests: router classification, collect_details field progression

## Task 7: Graph assembly
- `app/agent/graph.py`: wire `router → rag | collect_details`, compile with `SqliteSaver` checkpointer
- Verify graph compiles

## Task 8: FastAPI routes
- `app/api/routes.py`: `POST /chat`, `GET /admin/pending` (stub), `POST /admin/decision` (stub)
- `main.py`: mount frontend static dir, include router, serve `chat.html` at `/` and `admin.html` at `/admin`
- Tests: `/chat` returns reply + status, `/admin/pending` returns empty list

## Task 9: Chat frontend
- `app/frontend/chat.html`: header, scrollable message list, sticky input bar
- Session UUID generated on page load, sent with every request
- Shows system messages for `awaiting_approval`, `confirmed`, `rejected` statuses

## Task 10: Admin frontend (stub) + smoke test
- `app/frontend/admin.html`: header with pending badge, placeholder message ("Stage 2 will populate this")
- Run app, manually verify chat works end-to-end
- Run full test suite, all green
- Update CLAUDE.md commands section with actual uv run commands
