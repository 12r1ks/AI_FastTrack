# Run: uv run python -m eval.eval_rag
import asyncio
from openai import AsyncOpenAI
import pandas as pd
from ragas.llms import llm_factory
from ragas.metrics.collections import ContextPrecision, ContextRecall, NoiseSensitivity, AnswerRelevancy, Faithfulness
from ragas.metrics import DiscreteMetric
from eval.dataset import SAMPLES
from app.rag.retriever import retrieve
from app.agent.agent import agent
from ragas.embeddings.base import embedding_factory
from langchain_core.messages import HumanMessage


client = AsyncOpenAI()
llm_ = llm_factory("gpt-4o", client=client)
embeddings = embedding_factory("openai", model="text-embedding-3-small", client=client)

precision_metric = ContextPrecision(llm=llm_)
recall_metric = ContextRecall(llm=llm_)
answerrelevancy_metric = AnswerRelevancy(llm=llm_, embeddings=embeddings)
faithfulness_metrics = Faithfulness(llm=llm_)
noise_sense_metric = NoiseSensitivity(llm=llm_)


async def main():

    print(f"Evaluating {len(SAMPLES)} questions...\n")
    rows = []

    custom_evaluator = DiscreteMetric(
            name="summary_politeness",
            allowed_values=["polite", "impolite"],
            prompt="""Evaluate if the summary is polite and not toxic. Response: {response} Answer with only 'polite' or 'impolite'.""",
        )

    for sample in SAMPLES:
        graphed_sample = await agent.ainvoke({"messages": [HumanMessage(content=sample["user_input"])]})
        reply = graphed_sample["messages"][-1].content
        contexts = retrieve(sample["user_input"], top_k=3)

        precision = await precision_metric.ascore(
            user_input=sample["user_input"],
            reference=sample["reference"],
            retrieved_contexts=contexts,
        )
        recall = await recall_metric.ascore(
            user_input=sample["user_input"],
            reference=sample["reference"],
            retrieved_contexts=contexts,
        )

        answerrelevancy = await answerrelevancy_metric.ascore(
            user_input=sample["user_input"],
            response = reply,
        )

        faithfulness = await faithfulness_metrics.ascore(
            user_input=sample["user_input"],
            response = reply,
            retrieved_contexts=contexts,
        )

        noise_sensitivity = await noise_sense_metric.ascore(
            user_input=sample["user_input"],
            response = reply,
            reference=sample["reference"],
            retrieved_contexts=contexts,
        )

        
        polite_score = await custom_evaluator.ascore(llm=llm_, response=reply)

        rows.append({
            "question": sample["user_input"],
            "context_precision": precision.value,
            "context_recall": recall.value,
            "answer_relevancy": answerrelevancy.value,
            "faithfulness": faithfulness.value,
            "noise_sensitivity": noise_sensitivity.value,
            "is_polite": polite_score.value
        })
        
        print(f"  precision={precision.value:.3f}  "
              f" recall={recall.value:.3f}  "
              f" answer relevancy={answerrelevancy.value:.3f}  "
              f" faithfulness={faithfulness.value:.3f}  "
              f" noise sensitivity={noise_sensitivity.value:.3f}  "
              f" is polite? = {polite_score.value} "
              f" {sample['user_input'][:60]}"
              ) 

    df = pd.DataFrame(rows)
    print(f"\nMean context_precision : {df['context_precision'].mean():.3f}")
    print(f"Mean context_recall    : {df['context_recall'].mean():.3f}")
    print(f"Mean answer_relevancy    : {df['answer_relevancy'].mean():.3f}")

    output_path = "eval/results.csv"
    df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
