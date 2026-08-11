"""
LLM provider factory.
Change LLM_PROVIDER in .env without touching any other code.
"""
from app.core.config import settings
from app.core.logging import logger


def get_llm():
    """Return a LangChain-compatible LLM based on LLM_PROVIDER env var."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")
        logger.info(f"Using Groq LLM: {settings.LLM_MODEL}")
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Supported: groq")
