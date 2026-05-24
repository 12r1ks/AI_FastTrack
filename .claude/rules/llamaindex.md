# LlamaIndex Rules

Current API (2025–2026). Do not use deprecated patterns.

## Deprecated — never use

| Deprecated | Replacement |
|---|---|
| `ServiceContext` | `Settings` global object or per-call kwargs |
| `ServiceContext.from_defaults(llm=..., embed_model=...)` | `Settings.llm = ...; Settings.embed_model = ...` |
| `from llama_index.llms import OpenAI` | `from llama_index.llms.openai import OpenAI` |
| `from llama_index.vector_stores import PineconeVectorStore` | `from llama_index.vector_stores.pinecone import PineconeVectorStore` |
| `from llama_hub.slack.base import SlackReader` | `from llama_index.readers.slack import SlackReader` |
| `QueryPipeline` (removed) | LCEL-style chains or LangGraph |
| `FunctionCallingAgent`, `AgentRunner`, `OpenAIAgent` (removed) | `FunctionAgent` / `ReActAgent` + `AgentWorkflow` |
| `AgentExecutor`-style classes | `AgentWorkflow` |
| Python 3.9 | Python 3.10+ (3.9 deprecated March 2026) |
| `asyncio_module` | `get_asyncio_module` |

## Installation

Install the core package plus provider-specific integrations — do **not** import integrations from the monolithic `llama_index` namespace:

```bash
# Minimal custom install
pip install llama-index-core llama-index-llms-openai llama-index-embeddings-openai

# Anthropic LLM
pip install llama-index-llms-anthropic

# Local embeddings
pip install llama-index-embeddings-huggingface

# Quick start bundle (includes OpenAI LLM + embeddings + file reader)
pip install llama-index
```

## Global configuration — Settings

`Settings` is the singleton that replaces `ServiceContext`. Set it once; all downstream components pick it up automatically.

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.text_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=64)
# Optional: token budget
Settings.context_window = 128_000
Settings.num_output = 512
```

Local overrides (supersede global):

```python
index = VectorStoreIndex.from_documents(docs, embed_model=custom_embed)
engine = index.as_query_engine(llm=custom_llm)
```

## RAG — VectorStoreIndex

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Build and persist
documents = SimpleDirectoryReader("data/").load_data()
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist(persist_dir="data/index")

# Load from disk
from llama_index.core import StorageContext, load_index_from_storage
storage_context = StorageContext.from_defaults(persist_dir="data/index")
index = load_index_from_storage(storage_context)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What are the parking hours?")
```

## Agents — FunctionAgent and AgentWorkflow

Use `FunctionAgent` (function-calling LLM) or `ReActAgent` (any LLM). Wrap in `AgentWorkflow` for multi-agent orchestration.

```python
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent, AgentWorkflow

llm = OpenAI(model="gpt-4o-mini")

async def my_tool(query: str) -> str:
    """Describe what this tool does."""
    return "result"

agent = FunctionAgent(
    tools=[my_tool],
    llm=llm,
    system_prompt="You are a helpful assistant.",
)

# Single agent — run directly
response = await agent.run(user_msg="Hello")

# Multi-agent — wrap in AgentWorkflow
workflow = AgentWorkflow(agents=[agent_a, agent_b])
response = await workflow.run(user_msg="Hello")
```

## Agents — stateful / multi-turn

```python
from llama_index.core.workflow import Context, JsonSerializer

ctx = Context(agent)
r1 = await agent.run(user_msg="My name is Alex.", ctx=ctx)
r2 = await agent.run(user_msg="What is my name?", ctx=ctx)

# Serialize and restore conversation state
ctx_dict = ctx.to_dict(serializer=JsonSerializer())
ctx = Context.from_dict(agent, ctx_dict, serializer=JsonSerializer())
```

## Agents — streaming

```python
from llama_index.core.agent.workflow import AgentStream

handler = agent.run(user_msg="Tell me a story.")
async for event in handler.stream_events():
    if isinstance(event, AgentStream):
        print(event.delta, end="", flush=True)
```

## Human-in-the-loop

```python
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent

async def requires_approval(ctx: Context) -> str:
    """Task requiring human confirmation."""
    response = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="approval",
        waiter_event=InputRequiredEvent(prefix="Approve? (yes/no)", user_name="admin"),
        requirements={"user_name": "admin"},
    )
    return "Approved" if response.response == "yes" else "Rejected"
```

## LLM provider switching

```python
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic

def get_llm(provider: str = "openai"):
    if provider == "anthropic":
        return Anthropic(model="claude-sonnet-4-6")
    return OpenAI(model="gpt-4o-mini")
```

## Key import paths (v0.10+)

```python
# Core
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter

# Agents
from llama_index.core.agent.workflow import FunctionAgent, ReActAgent, AgentWorkflow, AgentStream
from llama_index.core.workflow import Context, JsonSerializer, InputRequiredEvent, HumanResponseEvent

# LLMs (install separately)
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic

# Embeddings (install separately)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
```
