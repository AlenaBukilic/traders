"""
Main Entry Point with Feature Flag Support

This module provides a unified entry point that can run either the
OpenAI Agents or Strands Agents implementation based on environment configuration.

Usage:
    # Use Strands (new)
    USE_STRANDS_AGENTS=true python main.py
    
    # Use OpenAI Agents (original)
    USE_STRANDS_AGENTS=false python main.py
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

# Feature flag: Which framework to use
USE_STRANDS = os.getenv("USE_STRANDS_AGENTS", "false").strip().lower() == "true"


async def main():
    """Main entry point with framework selection"""
    
    if USE_STRANDS:
        print("=" * 60)
        print("🚀 Starting Strands Agents Trading Floor")
        print("=" * 60)
        print()
        
        from strands_trading_floor import run_every_n_minutes
        await run_every_n_minutes()
    else:
        print("=" * 60)
        print("📊 Starting OpenAI Agents Trading Floor (Original)")
        print("=" * 60)
        print()
        
        from trading_floor import run_every_n_minutes
        await run_every_n_minutes()


if __name__ == "__main__":
    try:
        # Print configuration
        framework = "Strands Agents SDK" if USE_STRANDS else "OpenAI Agents SDK"
        print(f"Framework: {framework}")
        print(f"Configuration: .env")
        print()
        
        # Run main loop
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Trading floor shut down by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
