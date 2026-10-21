"""
Unified LLM Client Factory (Forwarder & Backward Compatibility Interface).
Provides centralized per-node LLM instance generation and configuration.
"""
from backend.app.core.llm_factory import (
    get_llm,
    get_node_llm,
    model_supports_temperature,
)
from backend.app.core.llm_config import (
    get_node_config,
    NodeLLMConfig,
    NODE_CONFIGS,
    refresh_node_configs,
)

__all__ = [
    "get_llm",
    "get_node_llm",
    "model_supports_temperature",
    "get_node_config",
    "NodeLLMConfig",
    "NODE_CONFIGS",
    "refresh_node_configs",
]
