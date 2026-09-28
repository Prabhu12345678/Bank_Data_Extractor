import logging
import json
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from src.config.settings import settings

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Highly configurable Strategy/Factory pattern to return the configured LLM engine.
    Supports Proprietary LLMs, Localized (Ollama/vLLM), and Aggregators.
    """

    @staticmethod
    def get_llm(temperature: float = 0.0):
        provider = settings.llm_provider.lower()

        if provider == "mock":
            # A dummy executable that acts like a LangChain chat model to support testing without an API Key
            logger.info("Using MOCK LLM Provider for local UI testing.")
            def mock_llm_response(prompt):
                prompt_str = str(prompt).lower()
                if "password-protected" in prompt_str or "unsupported" in prompt_str:
                    return AIMessage(content=json.dumps({
                        "confidence_score": 0.20,
                        "data": {
                            "document_type": "Unknown",
                            "entity_name": "UNKNOWN",
                            "document_id": "UNKNOWN",
                            "date": "UNKNOWN",
                            "total_amount": 0.0,
                            "line_items": []
                        }
                    }))
                return AIMessage(content=json.dumps({
                    "confidence_score": 0.99,
                    "data": {
                        "document_type": "Invoice",
                        "entity_name": "ACME CORP (MOCK DEMO)",
                        "document_id": "PO-1001",
                        "date": "09/26/2026",
                        "total_amount": 450.00,
                        "line_items": [
                            {"description": "SOFTWARE LICENSING (MOCK)", "quantity": 1, "unit_price": 200.0, "total": 200.0},
                            {"description": "MAINTENANCE (MOCK)", "quantity": 1, "unit_price": 250.0, "total": 250.0}
                        ]
                    }
                }))
            return RunnableLambda(mock_llm_response)

        elif provider == "claude":
            if not settings.anthropic_api_key:
                logger.warning("Anthropic API key missing! Switch to 'mock' provider in .env to test without keys.")
            return ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                temperature=temperature,
                anthropic_api_key=settings.anthropic_api_key
            )

        elif provider == "openai":
            return ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                openai_api_key=settings.openai_api_key
            )

        elif provider == "ollama" or provider == "local":
            return ChatOpenAI(
                model=settings.local_llm_model,
                temperature=temperature,
                openai_api_base=settings.local_llm_url,
                openai_api_key="ollama"
            )

        elif provider == "aggregator":
            return ChatOpenAI(
                model=settings.aggregator_model,
                temperature=temperature,
                openai_api_base=settings.aggregator_url,
                openai_api_key=settings.aggregator_api_key
            )

        else:
            raise ValueError(f"Unsupported LLM Provider configured: {provider}")
