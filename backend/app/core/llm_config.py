import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict
from backend.app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeLLMConfig:
    """
    Configuration specification for a specific LangGraph agent node.
    Enables granular per-node temperature, token limits, and model routing.
    """
    node_name: str
    model: str
    temperature: float
    max_tokens: int
    top_p: Optional[float] = None
    timeout: float = 60.0
    max_retries: int = 2
    source: str = "default"  # 'default' or 'env'


# Canonical Node Name Mapping
NODE_ALIASES = {
    "plan_queries": "plan_queries",
    "plan": "plan_queries",
    "extract_facts": "extract_facts",
    "extract": "extract_facts",
    "research": "research_agent",
    "research_agent": "research_agent",
    "title": "title_generator",
    "title_generator": "title_generator",
    "write": "content_generator",
    "writer": "content_generator",
    "content_generator": "content_generator",
    "reviewer": "verifier_agent",
    "verifier": "verifier_agent",
    "verify": "verifier_agent",
    "verifier_agent": "verifier_agent",
    "translator": "translator",
    "translate": "translator",
}

# Approved Default Baselines (requirement 12: research/extract/verify = 0, write = 0.35, title = 0.5)
DEFAULT_NODE_SPECS = {
    "plan_queries": {
        "temperature": 0.0,
        "max_tokens": 512,
        "env_temp_keys": ["PLAN_TEMPERATURE", "RESEARCH_TEMPERATURE"],
        "env_tokens_keys": ["PLAN_MAX_TOKENS"],
        "env_model_keys": ["PLAN_MODEL", "RESEARCH_MODEL"],
    },
    "extract_facts": {
        "temperature": 0.0,
        "max_tokens": 2048,
        "env_temp_keys": ["EXTRACT_TEMPERATURE", "RESEARCH_TEMPERATURE"],
        "env_tokens_keys": ["EXTRACT_MAX_TOKENS"],
        "env_model_keys": ["EXTRACT_MODEL", "RESEARCH_MODEL"],
    },
    "research_agent": {
        "temperature": 0.0,
        "max_tokens": 512,
        "env_temp_keys": ["RESEARCH_TEMPERATURE"],
        "env_tokens_keys": ["RESEARCH_MAX_TOKENS"],
        "env_model_keys": ["RESEARCH_MODEL"],
    },
    "title_generator": {
        "temperature": 0.5,
        "max_tokens": 150,
        "env_temp_keys": ["TITLE_TEMPERATURE"],
        "env_tokens_keys": ["TITLE_MAX_TOKENS"],
        "env_model_keys": ["TITLE_MODEL"],
    },
    "content_generator": {
        "temperature": 0.35,
        "max_tokens": 4096,
        "env_temp_keys": ["WRITER_TEMPERATURE", "CONTENT_TEMPERATURE"],
        "env_tokens_keys": ["WRITER_MAX_TOKENS", "CONTENT_MAX_TOKENS"],
        "env_model_keys": ["WRITER_MODEL", "CONTENT_MODEL"],
    },
    "verifier_agent": {
        "temperature": 0.0,
        "max_tokens": 1500,
        "env_temp_keys": ["VERIFIER_TEMPERATURE", "REVIEWER_TEMPERATURE"],
        "env_tokens_keys": ["VERIFIER_MAX_TOKENS", "REVIEWER_MAX_TOKENS"],
        "env_model_keys": ["VERIFIER_MODEL", "REVIEWER_MODEL"],
    },
    "translator": {
        "temperature": 0.2,
        "max_tokens": 4096,
        "env_temp_keys": ["TRANSLATOR_TEMPERATURE"],
        "env_tokens_keys": ["TRANSLATOR_MAX_TOKENS"],
        "env_model_keys": ["TRANSLATOR_MODEL"],
    },
}


def _get_env_val(keys: list) -> Optional[str]:
    """Helper to retrieve first matching environment variable value."""
    for key in keys:
        val = os.getenv(key)
        if val is not None and val.strip() != "":
            return val.strip()
    return None


def validate_node_temperature(node: str, temp: float, provider: str = "groq") -> None:
    """
    Validates that a node's temperature falls within the provider's valid mathematical range.
    Raises ValueError with a clear actionable message if invalid.
    """
    provider_lower = provider.lower().strip()
    if provider_lower == "anthropic":
        min_temp, max_temp = 0.0, 1.0
    else:
        # OpenAI, Groq, Google, Ollama support 0.0 to 2.0
        min_temp, max_temp = 0.0, 2.0

    if not (min_temp <= temp <= max_temp):
        raise ValueError(
            f"Invalid temperature {temp} configured for node '{node}' with provider '{provider}'. "
            f"Temperature must be between {min_temp} and {max_temp}."
        )


def build_node_configs() -> Dict[str, NodeLLMConfig]:
    """
    Builds the active configuration dictionary across all nodes,
    applying environment variable overrides and validating ranges at startup.
    """
    settings = get_settings()
    global_model = settings.MODEL_NAME
    provider = settings.MODEL_PROVIDER

    configs = {}

    for node_name, spec in DEFAULT_NODE_SPECS.items():
        source = "default"
        
        # 1. Model resolution
        model_env = _get_env_val(spec["env_model_keys"])
        if not model_env and node_name == "verifier_agent" and getattr(settings, "VERIFIER_MODEL", None):
            model_env = settings.VERIFIER_MODEL
        model = model_env if model_env else global_model
        if model_env:
            source = "env"

        # 2. Temperature resolution
        temp_env = _get_env_val(spec["env_temp_keys"])
        if temp_env is not None:
            try:
                temperature = float(temp_env)
                source = "env"
            except ValueError:
                raise ValueError(
                    f"Invalid non-numeric value '{temp_env}' for {spec['env_temp_keys'][0]}."
                )
        else:
            temperature = float(spec["temperature"])

        # 3. Max tokens resolution
        tokens_env = _get_env_val(spec["env_tokens_keys"])
        if tokens_env is not None:
            try:
                max_tokens = int(tokens_env)
                source = "env"
            except ValueError:
                raise ValueError(
                    f"Invalid non-integer value '{tokens_env}' for {spec['env_tokens_keys'][0]}."
                )
        else:
            max_tokens = int(spec["max_tokens"])

        if max_tokens <= 0:
            raise ValueError(f"max_tokens for node '{node_name}' must be positive, got {max_tokens}.")

        # 4. Strict Startup Range Validation
        validate_node_temperature(node_name, temperature, provider)

        configs[node_name] = NodeLLMConfig(
            node_name=node_name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            source=source,
        )

    return configs


# Singleton dictionary initialized and validated at module import time
NODE_CONFIGS: Dict[str, NodeLLMConfig] = build_node_configs()


def get_node_config(node_name: str) -> NodeLLMConfig:
    """
    Retrieves the immutable configuration for a given LangGraph node.
    Accepts canonical node names or common aliases (e.g., 'writer', 'reviewer').
    """
    canonical_name = NODE_ALIASES.get(node_name.lower().strip(), node_name)
    if canonical_name not in NODE_CONFIGS:
        # Fallback to default writer specs if an unknown custom node is queried
        logger.warning(
            f"Node '{node_name}' not explicitly configured in llm_config. Falling back to content_generator defaults."
        )
        return NODE_CONFIGS["content_generator"]
    return NODE_CONFIGS[canonical_name]


def refresh_node_configs() -> Dict[str, NodeLLMConfig]:
    """Rebuilds and revalidates node configs (useful for testing runtime env changes)."""
    global NODE_CONFIGS
    NODE_CONFIGS = build_node_configs()
    return NODE_CONFIGS
