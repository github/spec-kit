import json
from pathlib import Path
from typing import List, Dict

import typer

from shared.config import load_env, create_gemini_chat_model
from agents import Agent, Runner


app = typer.Typer(add_completion=False)


def load_matrix(path: Path) -> List[Dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


@app.command()
def main(
    matrix_file: Path = typer.Option(..., exists=True, help="JSON list of configs {name,instructions,model}"),
    prompt: str = typer.Option("Why are evals important?"),
):
    load_env()
    results = []
    import asyncio

    for cfg in load_matrix(matrix_file):
        model = create_gemini_chat_model(cfg.get("model", "gemini-2.5-flash"))
        agent = Agent(name=cfg.get("name", "Variant"), instructions=cfg["instructions"], model=model)
        out = asyncio.run(Runner.run(agent, prompt))
        results.append({"name": cfg.get("name", "Variant"), "output": out.final_output})

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()


