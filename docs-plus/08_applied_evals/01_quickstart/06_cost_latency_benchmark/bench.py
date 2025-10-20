import time
from dataclasses import dataclass

import typer

from shared.config import load_env, create_gemini_chat_model
from agents import Agent, Runner


app = typer.Typer(add_completion=False)


@dataclass
class StepTiming:
    name: str
    ms: float


@app.command()
def main(prompt: str = typer.Option("Summarize why evals matter in 2 sentences.")):
    load_env()
    model = create_gemini_chat_model("gemini-2.5-flash")
    agent = Agent(name="BenchAgent", instructions="Be concise.", model=model)

    t0 = time.perf_counter()
    import asyncio
    result = asyncio.run(Runner.run(agent, prompt))
    t1 = time.perf_counter()

    total_ms = (t1 - t0) * 1000
    print("Output:\n" + result.final_output)
    print(f"\nTiming: {total_ms:.1f} ms (single step)")
    print("Cost: token-based estimate not implemented (provider-specific)")


if __name__ == "__main__":
    main()


