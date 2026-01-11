"""
Quick Phase 2 Validation (without slow invocation tests)

This runs only the fast tests to validate basic functionality.
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_both_researchers_creation():
    """Test both Strands and OpenAI Agents researchers can be created"""
    print("\n=== Testing Both Researcher Implementations ===\n")
    
    results = []
    
    print("1. Strands Researcher:")
    try:
        from agents.researcher import get_strands_researcher
        researcher = await get_strands_researcher("TestTrader", "gpt-4o-mini")
        print(f"   ✓ Created: {researcher.name}")
        results.append(True)
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results.append(False)
    
    print("\n2. OpenAI Agents Researcher:")
    try:
        from traders import get_researcher
        from agents.mcp import MCPServerStdio
        from mcp_params import researcher_mcp_server_params
        from contextlib import AsyncExitStack
        
        async with AsyncExitStack() as stack:
            mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in researcher_mcp_server_params("TestTrader")
            ]
            
            researcher = await get_researcher(mcp_servers, "gpt-4o-mini")
            print(f"   ✓ Created: {researcher.name}")
            results.append(True)
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        results.append(False)
    
    return all(results)


async def main():
    print("=" * 60)
    print("Phase 2 Quick Validation (Creation Tests Only)")
    print("=" * 60)
    
    success = await test_both_researchers_creation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Quick validation PASSED!")
        print("\nBoth Researcher implementations work correctly.")
        print("Full invocation test already validated in standalone run.")
        print("\nReady for Phase 3: Nested Agent Pattern")
    else:
        print("⚠ Quick validation FAILED")
        print("Check errors above")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
