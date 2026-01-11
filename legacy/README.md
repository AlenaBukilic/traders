# Legacy OpenAI Agents Implementation

⚠️ **This is the legacy implementation using OpenAI Agents SDK.**

## Status
- **Maintained**: No active development
- **Purpose**: Reference implementation and fallback
- **Last Updated**: January 2026 (Migration completed)

## When to Use
Use the legacy implementation if:
- You encounter issues with Strands SDK
- You need to compare behavior
- You're debugging migration issues

## How to Use
Set environment variable:
```bash
export USE_LEGACY_AGENTS=true
python main.py
```

Or run directly:
```bash
python legacy/trading_floor.py
```

## Files
- `traders.py`: Original Trader and Researcher agent implementations
- `trading_floor.py`: Multi-agent orchestration
- `tracers.py`: OpenAI Agents-specific tracing

## Migration
See `docs/migration/MIGRATION_COMPLETE.md` for full migration details.

## Key Differences from Strands
- Uses OpenAI Agents SDK (`agents` package)
- `Agent(instructions=...)` instead of `Agent(system_prompt=...)`
- `Runner.run()` instead of `agent.invoke_async()`
- `.as_tool()` method instead of `@tool` decorator
- `MCPServerStdio` instead of `MCPClient`
- TracingProcessor instead of hooks
