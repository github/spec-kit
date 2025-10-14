import asyncio
import os

import logfire
from agents import Agent, Runner
from langfuse import get_client

from shared.config import load_env, create_gemini_chat_model, maybe_configure_langfuse_otlp


def setup_instrumentation() -> None:
    logfire.configure(service_name="applied_evals_step01", send_to_logfire=False)
    logfire.instrument_openai_agents()


async def run_once() -> None:
    model = create_gemini_chat_model("gemini-2.5-flash")
    agent = Agent(
        name="BaselineAgent",
        instructions=(
            "You are a concise assistant. Answer clearly in 1-2 sentences."
        ),
        model=model,
    )
    question = "In one sentence, why do evals matter for agentic workflows?"
    result = await Runner.run(agent, question)
    print("Response:\n" + result.final_output)


async def main() -> None:
    load_env()
    maybe_configure_langfuse_otlp()
    setup_instrumentation()

    lf = None
    try:
        lf = get_client()
        if lf and not lf.auth_check():
            lf = None
    except Exception:
        lf = None

    await run_once()

    if lf:
        lf.flush()
        print(f"Traces sent to: {os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')}/traces")


if __name__ == "__main__":
    asyncio.run(main())


