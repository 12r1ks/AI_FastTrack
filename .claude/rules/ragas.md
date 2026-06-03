# Ragas Rules

Current API (v0.4, 2026). Do not use deprecated patterns.

## Deprecated — never use

| Deprecated | Replacement |
|---|---|
| `instructor_llm_factory()` | `llm_factory()` (unified, auto-detects provider) |
| `LangchainLLMWrapper` | `llm_factory()` with native clients |
| `LlamaIndexLLMWrapper` | `llm_factory()` with native clients |
| `LangchainEmbeddingsWrapper` | `OpenAIEmbeddings` or provider-native class |
| `AspectCritic` metric | `@discrete_metric()` decorator |
| `SimpleCriteriaScore` metric | `@discrete_metric()` decorator |
| `AnswerSimilarity` metric | `SemanticSimilarity` |
| `evaluate()` function | `@experiment()` decorator |
| `single_turn_ascore(sample)` | `ascore(**kwargs)` — kwargs, not a Sample object |
| `PydanticPrompt` dataclass | `BasePrompt` property-based class |
| `PromptMixin.adapt_prompts()` | `prompt.adapt()` on individual prompt objects |
| `ground_truths=["..."]` (list) | `reference="..."` (single string) |
| `from ragas.metrics import Faithfulness` | `from ragas.metrics.collections import Faithfulness` |
| `from ragas import evaluate` | `from ragas import experiment` |
| `embeddings.embed_query()` | `await embeddings.embed_text()` |
| `embeddings.embed_documents()` | `await embeddings.embed_texts()` |

## Import paths (v0.4)

```python
from ragas.metrics.collections import (
    Faithfulness, AnswerRelevancy, AnswerCorrectness,
    ContextPrecision, ContextRecall, SemanticSimilarity,
)
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings
from ragas import experiment
from ragas.metrics import discrete_metric, numeric_metric
```

## LLM initialisation

```python
from ragas.llms import llm_factory
from openai import AsyncOpenAI

llm = llm_factory("gpt-4o", client=AsyncOpenAI(api_key="..."))
# Provider is inferred from the model name — no separate instructor_llm_factory needed
```

## Embeddings

```python
from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    client=AsyncOpenAI(api_key="..."),
    model="text-embedding-3-small",
)
embedding = await embeddings.embed_text("text")
embeddings_list = await embeddings.embed_texts(["text1", "text2"])
```

## Scoring metrics

```python
from ragas.metrics.collections import Faithfulness, AnswerRelevancy

metric = Faithfulness(llm=llm)

# Returns MetricResult, not float
result = await metric.ascore(
    user_input="What is the parking fee?",
    response="The fee is $10/day.",
    retrieved_contexts=["Parking costs $10 per day."],
)
score: float = result.value      # the numeric score
reason: str | None = result.reason  # optional LLM explanation
```

## Sample schema (SingleTurnSample)

```python
from ragas import SingleTurnSample

sample = SingleTurnSample(
    user_input="What is AI?",
    response="AI is ...",
    retrieved_contexts=["context1"],
    reference="correct answer",   # NOT ground_truths=[...]
)
```

## Evaluation with @experiment

```python
from ragas import experiment
from pydantic import BaseModel
from ragas.metrics.collections import Faithfulness, AnswerRelevancy

class EvalResult(BaseModel):
    faithfulness: float
    answer_relevancy: float

@experiment(EvalResult)
async def run_eval(row):
    faith = await Faithfulness(llm=llm).ascore(
        response=row.response,
        retrieved_contexts=row.contexts,
    )
    relevancy = await AnswerRelevancy(llm=llm).ascore(
        user_input=row.user_input,
        response=row.response,
    )
    return EvalResult(
        faithfulness=faith.value,
        answer_relevancy=relevancy.value,
    )

results = await run_eval(dataset)
```

## Custom metrics

```python
from ragas.metrics import discrete_metric, numeric_metric

# Replace AspectCritic / SimpleCriteriaScore with decorators
@discrete_metric(name="clarity", allowed_values=["clear", "unclear"])
def clarity(response: str) -> str:
    return "clear" if len(response) > 50 else "unclear"

@numeric_metric(name="quality", allowed_values=(0.0, 10.0))
def quality_score(response: str) -> float:
    return min(len(response) / 500 * 10, 10.0)

result = await clarity().ascore(response="...")
```

## Available metrics (v0.4 collections)

Faithfulness, AnswerRelevancy, AnswerCorrectness, AnswerAccuracy,
ContextPrecision, ContextRecall, ContextRelevance, ContextEntityRecall,
NoiseSensitivity, ResponseGroundedness, SemanticSimilarity, FactualCorrectness,
BleuScore, RougeScore, ExactMatch, StringPresence, LevenshteinDistance,
NonLLMStringSimilarity, SummaryScore, ToolCallAccuracy, ToolCallF1,
TopicAdherence, AgentGoalAccuracy, DomainSpecificRubrics, InstanceSpecificRubrics.

**Not yet migrated to collections:** Multi-Modal Faithfulness, Multi-Modal Relevance.
