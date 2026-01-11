"""
Trading Floor - Multi-Agent Orchestration

This module manages multiple concurrent Trader agents, creating
a simulated trading floor where multiple traders with different strategies
operate simultaneously.

Key Features:
- Concurrent execution of 4 traders
- Each trader has unique strategy and model
- Scheduled execution every N minutes
- Market hours checking
- Graceful error handling per trader
"""

from agents.trader import Trader
from typing import List
import asyncio
from infrastructure.market import is_market_open
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
    ]
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini"]
else:
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4


def create_traders() -> List[Trader]:
    """
    Create a list of traders with different strategies and models.
    
    Returns:
        List of Trader instances ready to execute
    """
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    """
    Main execution loop for the trading floor.
    
    This function:
    1. Creates all traders
    2. Runs them concurrently every N minutes
    3. Checks market hours (optional)
    4. Handles errors gracefully
    5. Continues indefinitely until interrupted
    """
    traders = create_traders()
    
    print(f"Created {len(traders)} traders:")
    for trader in traders:
        print(f"  - {trader.name} ({trader.lastname}) using {trader.model_name}")
    
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            print(f"\n{'='*60}")
            print(f"Running trading cycle at {asyncio.get_event_loop().time()}")
            print(f"{'='*60}\n")
            
            results = await asyncio.gather(
                *[trader.run() for trader in traders],
                return_exceptions=True
            )
            
            for trader, result in zip(traders, results):
                if isinstance(result, Exception):
                    print(f"⚠ {trader.name} encountered error: {result}")
                else:
                    print(f"✓ {trader.name} completed successfully")
            
            print(f"\n{'='*60}")
            print(f"Trading cycle complete")
            print(f"{'='*60}\n")
        else:
            print("Market is closed, skipping run")
        
        print(f"Sleeping for {RUN_EVERY_N_MINUTES} minutes...")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


async def run_once():
    """
    Run a single trading cycle (useful for testing).
    
    This function runs all traders once and exits, making it ideal
    for validation and testing without waiting for the scheduler.
    """
    traders = create_traders()
    
    print(f"\n{'='*60}")
    print(f"Single Cycle Test - Running {len(traders)} traders")
    print(f"{'='*60}\n")
    
    for trader in traders:
        print(f"  - {trader.name} ({trader.lastname}) using {trader.model_name}")
    print()
    
    results = await asyncio.gather(
        *[trader.run() for trader in traders],
        return_exceptions=True
    )
    
    print(f"\n{'='*60}")
    print("Results:")
    print(f"{'='*60}")
    
    success_count = 0
    for trader, result in zip(traders, results):
        if isinstance(result, Exception):
            print(f"✗ {trader.name}: Failed - {result}")
        else:
            print(f"✓ {trader.name}: Completed")
            success_count += 1
    
    print(f"\n{success_count}/{len(traders)} traders completed successfully")
    print(f"{'='*60}\n")
    
    return success_count == len(traders)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        print("Running in single-cycle test mode")
        try:
            success = asyncio.run(run_once())
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"Starting trading floor")
        print(f"Running every {RUN_EVERY_N_MINUTES} minutes")
        print(f"Market hours check: {'disabled' if RUN_EVEN_WHEN_MARKET_IS_CLOSED else 'enabled'}")
        print(f"Multi-model mode: {'enabled' if USE_MANY_MODELS else 'disabled'}")
        print()
        
        try:
            asyncio.run(run_every_n_minutes())
        except KeyboardInterrupt:
            print("\n\nTrading floor shut down by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n\nFatal error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
