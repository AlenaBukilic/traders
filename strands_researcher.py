"""
Strands Researcher Agent Implementation

This module provides the Researcher agent using the Strands Agents SDK.
The Researcher agent is responsible for searching the web for financial news,
identifying trading opportunities, and maintaining a knowledge graph of information.

Key Features:
- Web search via Brave Search MCP server
- Web page fetching via mcp-server-fetch
- Knowledge graph via mcp-memory-libsql
- Comprehensive financial research capabilities
"""

import asyncio
from contextlib import AsyncExitStack
from typing import Optional
from mcp.client.stdio import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient
from model_providers import ModelProvider
from templates import researcher_instructions, research_tool
from mcp_params import researcher_mcp_server_params
from strands_observability import create_log_hook


async def get_strands_researcher(trader_name: str, model_name: str = "gpt-4o-mini") -> Agent:
    """
    Create a Researcher agent using Strands SDK.
    
    This function creates a financial research agent with access to:
    - Web search (Brave Search)
    - Web page fetching
    - Knowledge graph memory (per-trader)
    
    Args:
        trader_name: Name of the trader (used for memory isolation)
        model_name: Model to use (default: gpt-4o-mini)
    
    Returns:
        Strands Agent configured as a Researcher
        
    Note:
        The MCP servers must be configured in mcp_params.py
        The agent uses system_prompt (not instructions) in Strands API
    """
    
    # Get MCP server parameters for this trader
    mcp_server_params = researcher_mcp_server_params(trader_name)
    
    # Create MCP clients using stdio transport
    # We'll need to handle the connection lifecycle carefully
    mcp_tools = []
    
    # For Strands, we need to create MCPClient instances
    # The Strands MCPClient takes a transport_callable
    for params in mcp_server_params:
        # Create stdio server parameters
        server_params = StdioServerParameters(
            command=params["command"],
            args=params["args"],
            env=params.get("env")
        )
        
        # Create a transport callable that returns the stdio connection
        def make_transport(sp=server_params):
            return stdio_client(sp)
        
        # Create MCPClient with the transport
        mcp_client = MCPClient(
            transport_callable=make_transport,
            startup_timeout=120
        )
        mcp_tools.append(mcp_client)
    
    # Get model from provider
    model = ModelProvider.get_strands_model(model_name)
    
    # Create log hook for observability
    log_hook = create_log_hook(trader_name)
    
    # Create Strands Agent
    # Note: Strands uses system_prompt instead of instructions
    researcher = Agent(
        name="Researcher",
        system_prompt=researcher_instructions(),
        model=model,
        tools=mcp_tools,  # MCP clients are passed as tools
        hooks=[log_hook]  # Add logging hook
    )
    
    return researcher


async def get_strands_researcher_tool(trader_name: str, model_name: str = "gpt-4o-mini"):
    """
    Create a Researcher agent and convert it to a tool for use by Trader.
    
    This implements the agent-as-tool pattern for Strands, equivalent to
    OpenAI Agents' agent.as_tool() method.
    
    The pattern:
    1. Create the researcher agent
    2. Wrap its invoke_async method in a @tool decorated function
    3. Return the tool for use by other agents
    
    Args:
        trader_name: Name of the trader (for memory isolation)
        model_name: Model to use
    
    Returns:
        Tool-wrapped Researcher agent that can be called by other agents
        
    Example:
        researcher_tool = await get_strands_researcher_tool("Warren")
        trader = Agent(tools=[researcher_tool], ...)
        # Trader can now call the researcher tool
    """
    from strands import tool
    
    # Create the researcher agent
    researcher = await get_strands_researcher(trader_name, model_name)
    
    # Wrap the researcher invocation in a tool
    # We'll use a closure to capture the researcher instance
    @tool(
        name="Researcher",
        description=research_tool()
    )
    async def researcher_tool(query: str) -> str:
        """
        Research tool that delegates to the Researcher agent.
        
        Use this tool to research online for news and opportunities,
        either based on your specific request to look into a certain stock,
        or generally for notable financial news and opportunities.
        
        Args:
            query: What kind of research you're looking for. Describe the research request clearly.
        
        Returns:
            Research findings and analysis
        """
        # Invoke the researcher agent
        result = await researcher.invoke_async(query)
        
        # Extract the response text from the result
        # The response structure is: result.message (dict) with 'content' (list)
        try:
            if hasattr(result, 'message'):
                msg = result.message
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    if isinstance(content, list) and len(content) > 0:
                        # Extract text from first content block
                        first_content = content[0]
                        if isinstance(first_content, dict) and 'text' in first_content:
                            return first_content['text']
                        elif hasattr(first_content, 'text'):
                            return first_content.text
            
            # Fallback: return string representation
            return str(result.message)
        except Exception as e:
            return f"Error extracting response: {e}\nRaw result: {result.message}"
    
    return researcher_tool


async def test_researcher_standalone(trader_name: str = "Warren", model_name: str = "gpt-4o-mini"):
    """
    Test the Researcher agent in standalone mode.
    
    This function demonstrates how to use the Researcher agent
    and can be used for validation during migration.
    
    Args:
        trader_name: Name of trader (for memory isolation)
        model_name: Model to use
    """
    print(f"\n=== Testing Strands Researcher ===")
    print(f"Trader: {trader_name}")
    print(f"Model: {model_name}\n")
    
    # Create researcher
    print("Creating researcher agent...")
    researcher = await get_strands_researcher(trader_name, model_name)
    print(f"✓ Created researcher: {researcher.name}")
    
    # Test with a simple query
    print("\nTesting researcher with query...")
    query = "Research recent news about Tesla stock performance"
    
    try:
        result = await researcher.invoke_async(query)
        print(f"✓ Researcher responded successfully")
        print(f"\nStop reason: {result.stop_reason}")
        
        # Try to extract response
        # Note: Response structure may be complex, handle gracefully
        if hasattr(result, 'message'):
            print(f"\nResponse preview: {str(result.message)[:500]}...")
        
        return True
    except Exception as e:
        print(f"✗ Researcher invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up agent resources if cleanup method exists
        if hasattr(researcher, 'cleanup') and callable(researcher.cleanup):
            await researcher.cleanup()


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    async def main():
        """Run standalone test of Researcher agent"""
        try:
            success = await test_researcher_standalone()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(main())
