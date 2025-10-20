import json
from pathlib import Path
from typing import List, Dict

import typer

from shared.config import load_env, create_gemini_chat_model
from agents import Agent, Runner


app = typer.Typer(add_completion=False)


PROMPT_TEMPLATE = (
    "You are an evaluator. Given an artifact (text) and a rubric of binary criteria, "
    "return JSON with fields: scores: list[0|1] for each criterion in order; total: int. "
    "Do not include explanations."
)


def load_rubric(path: Path) -> List[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@app.command()
def main(
    artifact_file: Path = typer.Option(..., exists=True, help="Path to text to judge"),
    rubric_file: Path = typer.Option(..., exists=True, help="Path to rubric.txt (one criterion per line)"),
    model: str = typer.Option("gemini-2.5-flash"),
):
    load_env()
    llm = create_gemini_chat_model(model)
    evaluator = Agent(
        name="RubricJudge",
        instructions=PROMPT_TEMPLATE,
        model=llm,
    )

    artifact = artifact_file.read_text(encoding="utf-8")
    rubric = load_rubric(rubric_file)
    criteria_json = json.dumps(rubric)

    import asyncio
    result = asyncio.run(
        Runner.run(
            evaluator,
            f"Rubric: {criteria_json}\nArtifact:\n{artifact}\nReturn compact JSON only.",
        )
    )

    print(result.final_output)


if __name__ == "__main__":
    main()


