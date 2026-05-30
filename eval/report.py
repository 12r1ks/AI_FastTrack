# Run: uv run python -m eval.report
import pandas as pd

NUMERIC_COLS = [
    "context_precision",
    "context_recall",
    "answer_relevancy",
    "faithfulness",
    "noise_sensitivity",
]

CSS = """
<style>
  body { font-family: sans-serif; padding: 2rem; background: #f8f9fa; }
  h1 { color: #333; }
  table { border-collapse: collapse; width: 100%; background: white;
          box-shadow: 0 1px 4px rgba(0,0,0,.1); border-radius: 8px; overflow: hidden; }
  th { background: #2c3e50; color: white; padding: 10px 14px; text-align: left; }
  td { padding: 9px 14px; border-bottom: 1px solid #eee; }
  tr:last-child td { border-bottom: none; }
  .summary { margin-top: 2rem; background: white; padding: 1rem 1.5rem;
             border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
  .summary h2 { margin-top: 0; color: #333; }
  .summary table { box-shadow: none; }
  .summary th { background: #34495e; }
</style>
"""


def build_report(csv_path: str = "eval/results.csv", output_path: str = "eval/results.html"):
    df = pd.read_csv(csv_path)

    higher_is_better = [c for c in NUMERIC_COLS if c in df.columns and c != "noise_sensitivity"]
    lower_is_better  = [c for c in ["noise_sensitivity"] if c in df.columns]

    styled = (
        df.style
        .format({col: "{:.3f}" for col in NUMERIC_COLS if col in df.columns})
        .background_gradient(subset=higher_is_better, cmap="RdYlGn", vmin=0, vmax=1)
        .background_gradient(subset=lower_is_better,  cmap="RdYlGn_r", vmin=0, vmax=1)
        .set_properties(**{"text-align": "left"})
    )

    summary = df[NUMERIC_COLS].mean().rename("mean").to_frame().T
    summary_html = (
        summary.style
        .format("{:.3f}")
        .background_gradient(cmap="RdYlGn", vmin=0, vmax=1)
        .set_properties(**{"text-align": "left"})
        .to_html()
    )

    main_table = styled.to_html()

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>RAG Evaluation Report</title>{CSS}</head>
<body>
  <h1>RAG Evaluation Report</h1>
  <p>{len(df)} questions evaluated &nbsp;|&nbsp; green = high score, red = low score</p>
  {main_table}
  <div class="summary">
    <h2>Mean scores</h2>
    {summary_html}
  </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    build_report()
