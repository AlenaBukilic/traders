"""
Core Utilities

Shared utilities used across the trading system.
"""

from .model_providers import ModelProvider, create_strands_model, create_openai_agents_model
from .templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool
)
from .observability import (
    StrandsLogHook,
    create_log_hook,
    make_trace_id
)

__all__ = [
    # Model providers
    "ModelProvider",
    "create_strands_model",
    "create_openai_agents_model",
    
    # Templates
    "researcher_instructions",
    "trader_instructions",
    "trade_message",
    "rebalance_message",
    "research_tool",
    
    # Observability
    "StrandsLogHook",
    "create_log_hook",
    "make_trace_id",
]
