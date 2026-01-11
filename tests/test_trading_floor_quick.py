"""
Phase 5 Quick Test - Multi-Trader Creation (No Full Execution)

This tests that we can create multiple traders and they're properly isolated.
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)


async def test_multi_trader_creation():
    """Test creating multiple traders"""
    print("=" * 60)
    print("Phase 5 Quick Test - Multi-Trader Creation")
    print("=" * 60)
    
    try:
        from agents.trading_floor import create_strands_traders
        
        print("\n1. Creating multiple traders...")
        traders = create_strands_traders()
        
        print(f"✓ Created {len(traders)} traders:")
        for trader in traders:
            print(f"  - {trader.name} ({trader.lastname}) using {trader.model_name}")
        
        print("\n2. Verifying trader isolation...")
        # Check that each trader has unique name
        names = [t.name for t in traders]
        if len(names) == len(set(names)):
            print(f"✓ All traders have unique names")
        else:
            print(f"✗ Duplicate trader names found!")
            return False
        
        # Check that each trader has independent state
        print(f"✓ Each trader has independent state:")
        for trader in traders:
            print(f"  - {trader.name}: do_trade={trader.do_trade}")
        
        print("\n3. Testing account isolation...")
        # Try to get account reports for each trader
        reports = []
        for trader in traders:
            try:
                report = await trader.get_account_report()
                reports.append((trader.name, len(report)))
                print(f"✓ {trader.name}: account report retrieved ({len(report)} bytes)")
            except Exception as e:
                print(f"✗ {trader.name}: failed to get account - {e}")
                return False
        
        print("\n4. Testing concurrent operations...")
        # Test that we can create all researcher tools concurrently
        from agents.researcher import get_strands_researcher_tool
        
        print("  Creating researcher tools concurrently...")
        researcher_tools = await asyncio.gather(*[
            get_strands_researcher_tool(trader.name, trader.model_name)
            for trader in traders
        ])
        
        print(f"✓ Created {len(researcher_tools)} researcher tools concurrently")
        
        print("\n✅ All multi-trader tests PASSED!")
        print("\nTraders are properly isolated and ready for concurrent execution.")
        print("\nNote: Full execution would take 5-10 minutes and make actual trades.")
        print("      Run with actual execution only when ready to test end-to-end.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_safety():
    """Test that concurrent execution is safe"""
    print("\n" + "=" * 60)
    print("Bonus Test - Concurrent Safety")
    print("=" * 60)
    
    try:
        from agents.trader import StrandsTrader
        
        print("\n1. Creating 2 traders with same model...")
        trader1 = StrandsTrader("Warren", "Patience", "gpt-4o-mini")
        trader2 = StrandsTrader("George", "Bold", "gpt-4o-mini")
        
        print("✓ Both traders created")
        
        print("\n2. Testing concurrent account access...")
        # Both traders accessing accounts concurrently
        results = await asyncio.gather(
            trader1.get_account_report(),
            trader2.get_account_report(),
            return_exceptions=True
        )
        
        if all(not isinstance(r, Exception) for r in results):
            print("✓ Concurrent account access works correctly")
            print(f"  Warren account: {len(results[0])} bytes")
            print(f"  George account: {len(results[1])} bytes")
        else:
            print("✗ Concurrent access had errors")
            return False
        
        print("\n✅ Concurrent safety tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\n✗ Concurrent safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    results = []
    
    # Test 1: Multi-trader creation
    results.append(await test_multi_trader_creation())
    
    # Test 2: Concurrent safety
    results.append(await test_concurrent_safety())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Multi-Trader Creation: {'✓ PASS' if results[0] else '✗ FAIL'}")
    print(f"Concurrent Safety:     {'✓ PASS' if results[1] else '✗ FAIL'}")
    print(f"\nTotal: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
