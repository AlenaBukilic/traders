"""
Phase 3 - Direct Tool Invocation Test
Tests that the researcher tool can be invoked directly
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def main():
    print("=" * 60)
    print("Phase 3 - Direct Tool Invocation Test")
    print("=" * 60)
    
    try:
        from strands_researcher import get_strands_researcher_tool
        
        print("\n1. Creating researcher tool...")
        researcher_tool = await get_strands_researcher_tool("TestTrader", "gpt-4o-mini")
        print("   ✓ Tool created")
        
        print("\n2. Invoking tool directly...")
        query = "What is happening with Apple stock? Be very brief, 2-3 sentences max."
        print(f"   Query: {query}")
        print("   (This will take 30-60 seconds...)")
        
        result = await researcher_tool(query)
        
        print(f"\n✓ Tool invoked successfully!")
        print(f"\nResponse:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        
        print("\n✅ Direct tool invocation WORKS!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
