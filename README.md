# CityPark Assistant

A parking space reservation chatbot built with LangChain, LangGraph, and RAG. Users interact with an AI assistant to find parking, check availability, and submit reservation requests for admin approval.

## Presentation

[CityPark_Stage1.pptx](scrn_Presentation/CityPark_Stage1.pptx)

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — handles Python version and dependencies
- An Anthropic API key (or OpenAI if you prefer)

## Setup

```bash
git clone <repo-url>
cd AI_FastTrack

# Create .env from the example
cp .env.example .env
# Fill in your API key in .env

uv sync
```

**.env contents:**
```
ANTHROPIC_API_KEY=your-key-here
# LLM_PROVIDER=openai        # uncomment to use OpenAI instead
# OPENAI_API_KEY=your-key-here
```

## Run

```bash
uv run python main.py
```

On first run this will:
1. Download the HuggingFace embedding model (~90 MB, one-time)
2. Build the FAISS vector index from `app/rag/seed_parking_info.md`
3. Create and seed the SQLite database
4. Start the server at `http://localhost:8000`

Open `http://localhost:8000` for the chat UI, and `http://localhost:8000/admin` for the admin panel — where pending reservation requests are reviewed and approved or rejected (the user's chat is notified of the decision automatically).

## Test

```bash
uv run pytest                                           # all tests
uv run pytest tests/test_nodes.py                      # single file
uv run pytest tests/test_nodes.py::test_init_node_resets_llm_calls  # single test
```

## Evaluate (requires OpenAI key)

```bash
uv run python -m eval.eval_rag    # run RAGAS evaluation, saves to eval/results.csv
uv run python -m eval.report      # generate HTML report from results
```

## Architecture

```
User → guard_route → llm_call ⇄ tool_node → pre_end_guard → response
              ↓
           reject
```

- **guard_route** — classifies input; blocks off-topic or adversarial messages
- **llm_call** — main LLM node with tool binding (RAG, availability, price, reservation)
- **tool_node** — executes tool calls; stores reservation details in graph state
- **pre_end_guard** — masks phone numbers before the response reaches the user

Static parking info is retrieved via FAISS (LlamaIndex). Live availability comes from a SQLite database. Reservation proposals are stored in graph state and require admin approval.

## Admin sub-agent (human-in-the-loop)

When a reservation proposal is confirmed, the main agent routes into the **admin sub-agent** — a separate LangGraph subgraph that puts a human in the loop:

```
init → approval (interrupt) → llm_call_admin ⇄ tool_node_adm → END
```

- **approval_node** calls `interrupt()`, pausing the graph and surfacing the proposed reservation. The request now shows up at `http://localhost:8000/admin`.
- The admin **approves or rejects** in the panel. The decision (`{"decision": ..., "reason": ...}`) resumes the paused graph via `Command(resume=...)`.
- **llm_call_admin** is an LLM bound with the MCP save tool. On approval it calls the tool to persist the booking; it then writes a short summary back to the user.
- The user's chat is **notified of the outcome automatically** (polled), so they see the approval/rejection without re-sending a message.

The sub-agent keeps its own conversation channel (`message_admin`) separate from the user-facing `messages`, so admin/tool chatter never leaks into the chat. Pausing/resuming relies on the `InMemorySaver` checkpointer.

## MCP server (reservation persistence)

Confirmed reservations are written to storage by a standalone **MCP server** (`app/mcp/mcp_server.py`, built with FastMCP):

- It exposes a single tool, **`Dictionary_saver`**, which validates the reservation and **inserts it into the `BOOKINGS` table** (SQLite) as an `approved` booking. Because the availability query filters on `status = "approved"`, a saved booking immediately makes that spot **unavailable to other users**.
- The agent connects to it through **`langchain-mcp-adapters`** (`MultiServerMCPClient`) over **stdio** — the client launches the server as a subprocess; no separate process or port to manage. Tools are loaded **lazily** on first use so importing the graph stays fast.
- Field names are mapped to the DB columns at insert time (e.g. `clients_name → name`, `phone_number → phone`); `booking_type`, `status`, `created_at` are set server-side and `id` is auto-assigned.

In normal use you never start the server by hand — the agent's MCP client launches it over stdio on demand. To sanity-check the save tool directly, the `__main__` block inserts a sample reservation:
```bash
uv run python -m app.mcp.mcp_server     # runs the sample insert in __main__
```
> Note: under `langgraph dev`, launch with `uv run langgraph dev --allow-blocking` — the MCP client does a brief synchronous `shutil.which` lookup that the dev server's strict blocking-call detector otherwise flags.

## Switching LLM providers

Set `LLM_PROVIDER=openai` in `.env` and provide `OPENAI_API_KEY`. Defaults to Anthropic (`claude-haiku-4-5-20251001`).
