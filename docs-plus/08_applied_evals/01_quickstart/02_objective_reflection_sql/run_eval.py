import json
from pathlib import Path
from typing import Dict, List

import typer

from shared.config import load_env, create_gemini_chat_model
from agents import Agent, Runner


app = typer.Typer(add_completion=False)


def load_dataset(path: Path) -> List[Dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def answer_with_query(agent: Agent, item: Dict[str, str], reflect: bool) -> str:
    base_prompt = (
        "You are given a natural language question about a tiny retail dataset. "
        "First, propose an SQL query over tables (sales, products)."
        " Then answer ONLY with the final numeric/text answer."
    )
    question = item["question"].strip()
    first = await Runner.run(agent, f"{base_prompt}\nQuestion: {question}")
    if not reflect:
        return first.final_output

    reflection_prompt = (
        "Review and refine the previous SQL to be correct and efficient."
        " Then answer ONLY with the final answer."
    )
    second = await Runner.run(agent, f"Prev output: {first.final_output}\n{reflection_prompt}")
    return second.final_output


def normalize(s: str) -> str:
    return s.strip().lower()


@app.command()
def main(
    dataset: Path = typer.Option(..., exists=True, dir_okay=False, help="jsonl with question,answer"),
    reflect: bool = typer.Option(False, help="Enable second-pass reflection"),
    model: str = typer.Option("gemini-2.5-flash"),
):
    load_env()
    llm = create_gemini_chat_model(model)
    agent = Agent(
        name="SQLReflectionAgent",
        instructions=(
            "You write SQL over small tables and compute the final answer."
        ),
        model=llm,
    )

    data = load_dataset(dataset)
    import asyncio

    correct = 0
    total = 0
    for item in data:
        total += 1
        out = asyncio.run(answer_with_query(agent, item, reflect))
        if normalize(out).startswith(normalize(item["answer"])):
            correct += 1
        print(f"Q: {item['question']}\nA: {out}\nGT: {item['answer']}\n---")

    acc = correct / total if total else 0.0
    label = "with_reflection" if reflect else "no_reflection"
    print(f"Accuracy ({label}): {acc:.2%} ({correct}/{total})")


if __name__ == "__main__":
    main()


