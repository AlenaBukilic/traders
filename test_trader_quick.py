"""
Phase 4 Quick Test - Trader Creation (No Full Execution)

This tests trader creation and setup without running a full trading cycle.
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_trader_creation():
    """Test that we can create a Strands Trader"""
    print("=" * 60)
    print("Phase 4 Quick Test - Trader Creation")
    print("=" * 60)
    
    try:
        from strands_traders import StrandsTrader
        
        print("\n1. Creating StrandsTrader instance...")
        trader = StrandsTrader("Warren", "Patience", "gpt-4o-mini")
        
        print(f"✓ Trader created")
        print(f"  Name: {trader.name}")
        print(f"  Lastname: {trader.lastname}")
        print(f"  Model: {trader.model_name}")
        print(f"  Mode: {'Trade' if trader.do_trade else 'Rebalance'}")
        
        print("\n2. Testing account report fetch...")
        account = await trader.get_account_report()
        print(f"✓ Account report retrieved")
        print(f"  Preview: {account[:100]}...")
        
        print("\n3. Creating researcher tool...")
        from strands_researcher import get_strands_researcher_tool
        researcher_tool = await get_strands_researcher_tool(trader.name, trader.model_name)
        print(f"✓ Researcher tool created")
        
        print("\n4. Creating trader MCP clients...")
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from strands.tools.mcp import MCPClient
        from mcp_params import trader_mcp_server_params
        
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
        
        print(f"✓ Created {len(trader_mcp_tools)} trader MCP clients")
        
        print("\n5. Creating trader agent...")
        agent = await trader.create_agent(trader_mcp_tools, researcher_tool)
        print(f"✓ Trader agent created")
        print(f"  Agent name: {agent.name}")
        
        print("\n✅ All creation tests PASSED!")
        print("\nTrader is ready to run.")
        print("Note: Full execution test would take 2-3 minutes and make actual trades.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_trader_creation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
