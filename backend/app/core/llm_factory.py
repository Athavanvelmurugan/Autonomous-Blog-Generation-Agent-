import logging
from functools import lru_cache
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from backend.app.config import get_settings
from backend.app.core.llm_config import get_node_config, NodeLLMConfig

logger = logging.getLogger(__name__)

# Known reasoning models that reject or ignore temperature parameters
REASONING_MODEL_PREFIXES = ("o1", "o1-", "o1-mini", "o1-preview", "o3", "o3-mini")


def model_supports_temperature(model_name: str) -> bool:
    """
    Determines whether a model architecture supports explicit temperature tuning.
    OpenAI reasoning models (o1, o1-mini, o3-mini) reject temperature != 1 with 400 errors.
    """
    clean_name = model_name.lower().split("/")[-1].strip()
    for prefix in REASONING_MODEL_PREFIXES:
        if clean_name == prefix or clean_name.startswith(f"{prefix}-"):
            return False
    return True


@lru_cache(maxsize=128)
def _create_cached_llm(
    provider: str,
    model: str,
    temperature: Optional[float],
    max_tokens: int,
    top_p: Optional[float],
    timeout: float,
    max_retries: int,
    api_key: Optional[str],
) -> BaseChatModel:
    """
    Internal cached factory constructor.
    Memoizes LLM client instances by their exact hyperparameter tuple.
    """
    kwargs = {"max_tokens": max_tokens}

    if temperature is not None:
        kwargs["temperature"] = temperature

    # Only pass top_p if explicitly configured (prefer temperature only)
    if top_p is not None:
        kwargs["top_p"] = top_p

    if api_key:
        kwargs["api_key"] = api_key

    # Attempt LangChain init_chat_model first
    try:
        from langchain.chat_models import init_chat_model
        return init_chat_model(
            model=model,
            model_provider=provider,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
    except Exception as e:
        logger.warning(f"init_chat_model fallback triggered for {provider}/{model}: {e}")

    # Fallback to direct provider classes
    if provider == "groq":
        from langchain_groq import ChatGroq
        groq_kwargs = {
            "model_name": model,
            "groq_api_key": api_key,
            "max_tokens": max_tokens,
            "request_timeout": timeout,
            "max_retries": max_retries,
        }
        if temperature is not None:
            groq_kwargs["temperature"] = temperature
        if top_p is not None:
            groq_kwargs["model_kwargs"] = {"top_p": top_p}
        return ChatGroq(**groq_kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        openai_kwargs = {
            "model_name": model,
            "openai_api_key": api_key,
            "max_tokens": max_tokens,
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if temperature is not None:
            openai_kwargs["temperature"] = temperature
        if top_p is not None:
            openai_kwargs["top_p"] = top_p
        return ChatOpenAI(**openai_kwargs)

    raise ValueError(f"Unsupported or unconfigured LLM provider: {provider}")


def get_node_llm(
    node_name: str,
    temperature_override: Optional[float] = None,
    creativity_level: Optional[str] = None,
    max_tokens_override: Optional[int] = None,
) -> BaseChatModel:
    """
    Unified Per-Node LLM Factory.
    Retrieves the configured model, temperature, and tokens for the specified node.
    
    Args:
        node_name: Canonical name or alias of the LangGraph node (e.g. 'writer', 'verifier')
        temperature_override: Optional explicit temperature (used during dynamic revision step-downs)
        creativity_level: Optional API creativity preset ('low', 'balanced', 'high')
        max_tokens_override: Optional max tokens override (e.g. scaled for target word count)
        
    Returns:
        Configured, cached BaseChatModel instance with observability metadata.
    """
    settings = get_settings()
    config = get_node_config(node_name)
    provider = settings.MODEL_PROVIDER.lower().strip()
    model = config.model

    # 1. Calculate effective temperature
    if temperature_override is not None:
        effective_temp = float(temperature_override)
    else:
        effective_temp = config.temperature

        # Apply creativity offset ONLY to writing/title nodes
        if creativity_level and config.node_name in ["content_generator", "title_generator"]:
            if creativity_level == "low":
                effective_temp = max(0.1, round(effective_temp - 0.1, 2))
            elif creativity_level == "high":
                effective_temp = min(1.0, round(effective_temp + 0.1, 2))

    # 2. Check reasoning model temperature support
    if not model_supports_temperature(model):
        logger.warning(
            f"Model '{model}' is a reasoning model that does not support temperature tuning. "
            f"Skipping temperature parameter for node '{config.node_name}'."
        )
        passed_temp = None
    else:
        passed_temp = effective_temp

    # 3. Resolve API key and effective max tokens
    api_key = settings.GROQ_API_KEY if provider == "groq" else settings.OPENAI_API_KEY
    effective_max_tokens = max_tokens_override if max_tokens_override is not None else config.max_tokens

    # 4. Observability: Log hyperparameter telemetry
    logger.info(
        f"[LLM Call] Node: '{config.node_name}' | Model: '{model}' ({provider}) | "
        f"Temperature: {passed_temp if passed_temp is not None else 'N/A (Reasoning)'} "
        f"(Source: {config.source}) | MaxTokens: {effective_max_tokens}"
    )

    # 5. Fetch or instantiate cached client
    llm = _create_cached_llm(
        provider=provider,
        model=model,
        temperature=passed_temp,
        max_tokens=effective_max_tokens,
        top_p=config.top_p,
        timeout=config.timeout,
        max_retries=config.max_retries,
        api_key=api_key,
    )

    # 6. Attach LangSmith tracing tags/metadata if enabled
    if settings.LANGSMITH_TRACING:
        llm = llm.with_config(
            tags=[config.node_name, f"temp_{passed_temp}", provider],
            metadata={
                "node_name": config.node_name,
                "model": model,
                "temperature": passed_temp,
                "max_tokens": effective_max_tokens,
                "provider": provider,
                "source": config.source,
            },
        )

    return llm


# Main public alias for backward compatibility and clean ergonomics
get_llm = get_node_llm
