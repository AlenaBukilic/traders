"""
Trading Floor Entry Point

This is the main entry point for the trading system.

Default: Uses Strands Agents SDK (modern implementation)
Legacy: Set USE_LEGACY_AGENTS=true to use OpenAI Agents SDK (reference implementation)

Usage:
    # Run with Strands (default)
    python main.py
    
    # Run with legacy OpenAI Agents
    export USE_LEGACY_AGENTS=true
    python main.py
    
    # Run single cycle test
    python main.py once
"""

import os
from dotenv import load_dotenv
import asyncio
import sys

load_dotenv(override=True)

# Feature flag (default to Strands)
USE_LEGACY = os.getenv("USE_LEGACY_AGENTS", "false").strip().lower() == "true"

if USE_LEGACY:
    print("⚠️  Using LEGACY OpenAI Agents SDK")
    print("   (Set USE_LEGACY_AGENTS=false to use Strands)")
    from legacy.trading_floor import run_every_n_minutes, create_traders
else:
    print("✅ Using Strands Agents SDK (default)")
    print("   (Set USE_LEGACY_AGENTS=true to use legacy)")
    from agents.trading_floor import run_every_n_minutes, create_traders


# Configuration from environment
RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"


async def run_once():
    """Run a single trading cycle for testing"""
    if USE_LEGACY:
        from legacy.trading_floor import run_once as legacy_run_once
        return await legacy_run_once()
    else:
        from agents.trading_floor import run_once as strands_run_once
        return await strands_run_once()


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("Trading System")
    print(f"{'='*60}")
    print(f"Configuration:")
    print(f"  - Run interval: Every {RUN_EVERY_N_MINUTES} minutes")
    print(f"  - Market hours check: {'Disabled' if RUN_EVEN_WHEN_MARKET_IS_CLOSED else 'Enabled'}")
    print(f"  - Multi-model mode: {'Enabled' if USE_MANY_MODELS else 'Disabled'}")
    print(f"{'='*60}\n")
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        print("Running in single-cycle test mode\n")
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
        # Normal mode: run continuously
        print(f"Starting trading floor...\n")
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
