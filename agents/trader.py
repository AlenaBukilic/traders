"""
Trader Agent Implementation

This module provides the Trader agent using the Strands Agents SDK.
The Trader agent orchestrates trading decisions by:
- Using the Researcher agent (as a tool) for market research
- Accessing account management via MCP
- Accessing market data via MCP
- Sending notifications via MCP
- Making buy/sell decisions based on strategy

Key Features:
- Nested agent architecture (Trader uses Researcher)
- Multiple MCP server integration
- Strategy-based trading
- Alternates between trading and rebalancing modes
"""

import asyncio
import json
from contextlib import AsyncExitStack
from typing import Optional
from mcp.client.stdio import StdioServerParameters, stdio_client

from strands import Agent
from strands.tools.mcp import MCPClient
from core.model_providers import ModelProvider
from core.templates import trader_instructions, trade_message, rebalance_message
from infrastructure.mcp_params import trader_mcp_server_params
from agents.researcher import get_researcher_tool
from infrastructure.accounts_client import read_accounts_resource, read_strategy_resource
from infrastructure.database import write_log
from core.observability import create_log_hook


MAX_TURNS = 30


class Trader:
    """
    Trader agent implementation using Strands SDK.
    
    This is the main trader implementation for the system.
    For the legacy OpenAI Agents version, see legacy/traders.py
    """
    
    def __init__(self, name: str, lastname: str = "Trader", model_name: str = "gpt-4o-mini"):
        """
        Initialize a Trader agent.
        
        Args:
            name: Trader's name (e.g., "Warren", "George")
            lastname: Trader's strategy identifier (e.g., "Patience", "Bold")
            model_name: Model to use for trading decisions
        """
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.agent = None
        self.do_trade = True
    
    async def create_agent(self, trader_mcp_servers, researcher_tool) -> Agent:
        """
        Create the Trader agent with all necessary tools.
        
        Args:
            trader_mcp_servers: List of MCPClient instances for trader tools
            researcher_tool: The researcher agent wrapped as a tool
            
        Returns:
            Configured Strands Agent instance
        """
        model = ModelProvider.get_strands_model(self.model_name)
        
        log_hook = create_log_hook(self.name)
        
        all_tools = [researcher_tool] + (trader_mcp_servers if trader_mcp_servers else [])
        
        self.agent = Agent(
            name=self.name,
            system_prompt=trader_instructions(self.name),
            model=model,
            tools=all_tools,
            hooks=[log_hook]
        )
        
        return self.agent
    
    async def get_account_report(self) -> str:
        """
        Get account information for this trader.
        
        Returns:
            JSON string with account details (without time series data)
        """
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)
    
    async def run_agent(self, trader_mcp_servers, researcher_tool):
        """
        Run the trader agent with a specific task (trade or rebalance).
        
        Args:
            trader_mcp_servers: MCP servers for trader tools
            researcher_tool: Researcher agent as tool
        """
        self.agent = await self.create_agent(trader_mcp_servers, researcher_tool)
        
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        
        result = await self.agent.invoke_async(message)
        
        mode = "trading" if self.do_trade else "rebalancing"
        write_log(self.name, "agent", f"Completed {mode} - stop reason: {result.stop_reason}")
        
        return result
    
    async def run_with_mcp_servers(self):
        """
        Set up MCP servers and run the agent.
        
        This method manages the lifecycle of:
        - Trader MCP servers (accounts, market, push)
        - Researcher tool (which has its own MCP servers)
        """
        trader_mcp_tools = []
        for params in trader_mcp_server_params:
            server_params = StdioServerParameters(
                command=params["command"],
                args=params["args"],
                env=params.get("env")
            )
            
            def make_transport(sp=server_params):
                return stdio_client(sp)
            
            mcp_client = MCPClient(
                transport_callable=make_transport,
                startup_timeout=120
            )
            trader_mcp_tools.append(mcp_client)
        
        researcher_tool = await get_researcher_tool(
            self.name,
            self.model_name
        )
        
        await self.run_agent(trader_mcp_tools, researcher_tool)
    
    async def run_with_trace(self):
        """
        Run the agent with tracing/logging.
        
        Logs trading activity to the database for UI display.
        """
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        write_log(self.name, "trace", f"Started: {trace_name}")
        
        try:
            await self.run_with_mcp_servers()
            write_log(self.name, "trace", f"Ended: {trace_name}")
        except Exception as e:
            write_log(self.name, "trace", f"Error: {e}")
            raise
    
    async def run(self):
        """
        Main entry point for running the trader.
        
        This is the public interface that maintains compatibility
        with the original Trader class.
        """
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
            write_log(self.name, "trace", f"Error in run: {e}")
        
        # Toggle mode for next run
        self.do_trade = not self.do_trade


async def test_single_trader(
    name: str = "Warren",
    lastname: str = "Patience",
    model_name: str = "gpt-4o-mini"
):
    """
    Test a single trader execution.
    
    This function demonstrates how to use the Trader class
    and can be used for validation during migration.
    
    Args:
        name: Trader name
        lastname: Trader strategy identifier
        model_name: Model to use
    """
    print(f"\n=== Testing Trader: {name} ({lastname}) ===")
    print(f"Model: {model_name}\n")
    
    trader = Trader(name, lastname, model_name)
    
    print("Running trader... (this may take 2-3 minutes)")
    await trader.run()
    
    print(f"\n✓ Trader {name} completed execution")
    print(f"  Mode for next run: {'Trade' if trader.do_trade else 'Rebalance'}")


if __name__ == "__main__":
    import sys
    
    async def main():
        """Run standalone test of Trader agent"""
        try:
            await test_single_trader()
            print("\n✅ Trader test completed successfully!")
            sys.exit(0)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Trader test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())
