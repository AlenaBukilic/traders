"""
Observability and Logging

This module provides logging and observability for Strands agents,
similar to the original LogTracer but adapted for Strands' hooks system.

The adapter uses Strands' hooks to:
- Log agent invocations
- Log tool calls
- Log model calls
- Write to SQLite database for UI display
"""

from strands.hooks import (
    HookProvider,
    BeforeInvocationEvent,
    AfterInvocationEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
    BeforeModelCallEvent,
    AfterModelCallEvent,
)
from infrastructure.database import write_log
from typing import Optional
import secrets
import string


class StrandsLogHook(HookProvider):
    """
    Hook provider that logs Strands agent events to the database.
    
    This adapter provides similar functionality to the original LogTracer
    but uses Strands' hooks system instead of OpenAI Agents TracingProcessor.
    """
    
    def __init__(self, trader_name: str):
        """
        Initialize the log hook for a specific trader.
        
        Args:
            trader_name: Name of the trader (for log correlation)
        """
        self.trader_name = trader_name
    
    async def before_invocation(self, event: BeforeInvocationEvent) -> None:
        """Called before agent invocation starts"""
        write_log(
            self.trader_name,
            "agent",
            f"Started invocation"
        )
    
    async def after_invocation(self, event: AfterInvocationEvent) -> None:
        """Called after agent invocation completes"""
        stop_reason = event.result.stop_reason if hasattr(event.result, 'stop_reason') else 'unknown'
        write_log(
            self.trader_name,
            "agent",
            f"Ended invocation - stop reason: {stop_reason}"
        )
    
    async def before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Called before a tool is invoked"""
        tool_name = event.tool_use.name if hasattr(event.tool_use, 'name') else 'unknown'
        write_log(
            self.trader_name,
            "function",
            f"Started {tool_name}"
        )
    
    async def after_tool_call(self, event: AfterToolCallEvent) -> None:
        """Called after a tool invocation completes"""
        tool_name = event.tool_use.name if hasattr(event.tool_use, 'name') else 'unknown'
        
        if event.exception:
            write_log(
                self.trader_name,
                "function",
                f"Ended {tool_name} - error: {event.exception}"
            )
        else:
            write_log(
                self.trader_name,
                "function",
                f"Ended {tool_name}"
            )
    
    async def before_model_call(self, event: BeforeModelCallEvent) -> None:
        """Called before LLM is invoked"""
        write_log(
            self.trader_name,
            "generation",
            "Started model call"
        )
    
    async def after_model_call(self, event: AfterModelCallEvent) -> None:
        """Called after LLM invocation completes"""
        write_log(
            self.trader_name,
            "response",
            "Ended model call"
        )


def create_log_hook(trader_name: str) -> StrandsLogHook:
    """
    Create a log hook for a trader.
    
    Args:
        trader_name: Name of the trader
        
    Returns:
        Configured StrandsLogHook instance
        
    Example:
        hook = create_log_hook("Warren")
        agent = Agent(..., hooks=[hook])
    """
    return StrandsLogHook(trader_name)


# For backward compatibility with trace_id pattern
ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    """
    Generate a trace ID (for compatibility with original system).
    
    Args:
        tag: Tag to include in trace ID (usually trader name)
        
    Returns:
        Trace ID string
        
    Note:
        This function maintains compatibility with the original system
        but Strands uses its own internal trace IDs.
    """
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"



if __name__ == "__main__":
    import asyncio
    from strands import Agent
    from core.model_providers import ModelProvider
    
    async def test_hook():
        """Test the log hook"""
        print("Testing StrandsLogHook")
        
        hook = create_log_hook("TestTrader")
        print(f"✓ Created hook for TestTrader")
        
        model = ModelProvider.get_strands_model("gpt-4o-mini")
        agent = Agent(
            name="TestAgent",
            system_prompt="You are a test agent.",
            model=model,
            hooks=[hook]
        )
        
        print(f"✓ Created agent with hook")
        
        print("\nInvoking agent (will trigger hooks)...")
        result = await agent.invoke_async("Say 'Hook test successful'")
        
        print(f"\n✓ Agent invoked, hooks triggered")
        print(f"  Stop reason: {result.stop_reason}")
        
        from infrastructure.database import read_log
        logs = list(read_log("TestTrader", last_n=10))
        
        print(f"\nLogs written ({len(logs)} entries):")
        for timestamp, log_type, message in logs:
            print(f"  [{log_type}] {message}")
        
        return True
    
    try:
        asyncio.run(test_hook())
        print("\n✅ Hook test successful!")
    except Exception as e:
        print(f"\n✗ Hook test failed: {e}")
        import traceback
        traceback.print_exc()
