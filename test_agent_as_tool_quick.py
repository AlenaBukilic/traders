"""
Quick test for Phase 3 - just tool creation without invocation
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_quick():
    print("=" * 60)
    print("Phase 3 Quick Test - Tool Creation Only")
    print("=" * 60)
    
    print("\nTest 1: Create Researcher Tool")
    try:
        from strands_researcher import get_strands_researcher_tool
        
        researcher_tool = await get_strands_researcher_tool("TestTrader", "gpt-4o-mini")
        
        print(f"✓ Created researcher tool")
        print(f"  Type: {type(researcher_tool)}")
        print(f"  Name: {getattr(researcher_tool, 'name', 'N/A')}")
        print(f"  Description: {getattr(researcher_tool, 'description', 'N/A')[:100]}...")
        
        # Check it's callable
        if callable(researcher_tool):
            print(f"  ✓ Tool is callable")
        
        print("\nTest 2: Use Tool in Agent")
        from strands import Agent
        from model_providers import ModelProvider
        
        model = ModelProvider.get_strands_model("gpt-4o-mini")
        agent = Agent(
            name="TestAgent",
            system_prompt="You are a test agent with access to a researcher tool.",
            model=model,
            tools=[researcher_tool]
        )
        
        print(f"✓ Created agent with researcher tool")
        print(f"  Agent name: {agent.name}")
        
        print("\n✅ Phase 3 Quick Test PASSED!")
        print("Tool creation and agent integration work correctly.")
        print("\nNote: Full invocation test would take 1-2 minutes.")
        print("Run test_agent_as_tool.py for complete validation.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_quick())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
