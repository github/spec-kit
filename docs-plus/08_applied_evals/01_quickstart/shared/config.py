import os
import base64
from dotenv import load_dotenv, find_dotenv

from agents import AsyncOpenAI, OpenAIChatCompletionsModel


def load_env() -> None:
    load_dotenv(find_dotenv())


def create_gemini_chat_model(model: str = "gemini-2.5-flash") -> OpenAIChatCompletionsModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment")
    external_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    return OpenAIChatCompletionsModel(model=model, openai_client=external_client)


def maybe_configure_langfuse_otlp() -> None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    if not (public_key and secret_key):
        return
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ.setdefault("LANGFUSE_HOST", host)
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = host + "/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"


