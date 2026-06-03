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

Static parking info is retrieved via FAISS (LlamaIndex). Live availability comes from a SQLite database. Reservation proposals are stored in graph state and require admin approval (Stage 2).

## Switching LLM providers

Set `LLM_PROVIDER=openai` in `.env` and provide `OPENAI_API_KEY`. Defaults to Anthropic (`claude-haiku-4-5-20251001`).
