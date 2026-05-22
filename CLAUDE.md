# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A parking space reservation chatbot built in Python using LangChain, LangGraph, and RAG. Users interact with a chatbot to get parking info and make reservations; requests are escalated to a human admin for approval; confirmed reservations are persisted via an MCP server.

## Tech Stack

- **Language**: Python
- **Frameworks**: LangChain, LangGraph, FastAPI
- **Architecture**: RAG (Retrieval-Augmented Generation) orchestrated by LangGraph from stage 1
- **Vector DB**: FAISS (local, via `langchain-community`)
- **Relational DB**: SQLite (dynamic data + LangGraph checkpointer)
- **LLM**: Anthropic / OpenAI — switchable via LangChain configurable fields
- **Frontend**: Vanilla HTML/JS served by FastAPI (two pages: user chat + admin panel)
- **MCP Server**: Python + FastAPI (stage 3)
- **Testing**: pytest (minimum 2 tests per module)

## Architecture

The system is a 4-stage pipeline orchestrated by LangGraph:

```
User → [Agent 1: RAG Chatbot] → [Agent 2: Admin Agent] → [MCP Server] → reservations.txt
```

### Stage 1 — RAG Chatbot (Agent 1)
- Answers queries about parking info (hours, prices, availability, location) using a vector DB.
- Collects reservation details interactively: name, surname, car number, reservation period.
- Guard rails: filter output to prevent sensitive data leaking from the vector store (e.g., using a pre-trained NLP classifier on responses before returning them to the user).
- Static data (general info, location, rules) → FAISS. Dynamic data (availability, prices, hours) → SQLite.

### Stage 2 — Human-in-the-Loop (Agent 2)
- Receives escalated reservation requests from Agent 1.
- Sends the request to a human admin (email, messenger, or REST API) and awaits confirm/refuse.
- Passes the admin's response back to Agent 1 to inform the user.

### Stage 3 — MCP Server
- Triggered after admin approval.
- Writes confirmed reservation to a text file.
- File entry format: `Name | Car Number | Reservation Period | Approval Time`
- Must be secure against unauthorized access.

### Stage 4 — LangGraph Orchestration
- Wires all components into a single graph:
  - Node: user interaction (RAG + chatbot context)
  - Node: admin approval (human-in-the-loop)
  - Node: data recording (MCP server call)
- Manages state transitions and handles approval/refusal branching.

## Specification Files

- General requirements: [`Documents/general.md`](Documents/general.md)
- Stage 1 — RAG Chatbot: [`Documents/stage1.md`](Documents/stage1.md)
- Stage 2 — Human-in-the-Loop: [`Documents/stage2.md`](Documents/stage2.md)
- Stage 3 — MCP Server: [`Documents/stage3.md`](Documents/stage3.md)
- Stage 4 — LangGraph Orchestration: [`Documents/stage4.md`](Documents/stage4.md)

## Framework Rules

@.claude/rules/langchain-langgraph.md
@.claude/rules/fastapi.md

## Commands

_No code exists yet. Add commands here once the project is scaffolded._

```bash
uv sync                          # install / sync dependencies
uv add <package>                 # add a dependency

uv run uvicorn main:app --reload # run the app
uv run pytest                    # run all tests
uv run pytest tests/test_rag.py  # run a single test file
```
