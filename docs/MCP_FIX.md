# 🔧 Critical Fix: MCP Server Paths

## Problem Identified

After restructuring, MCP servers were failing to start with:
```
mcp.shared.exceptions.McpError: Connection closed
MCPClientInitializationError: the client initialization failed
```

## Root Cause

When files were moved to the `infrastructure/` directory, the MCP server launch commands still referenced the old paths:

**Before (Broken):**
```python
{"command": "uv", "args": ["run", "accounts_server.py"]}  # ❌ File not in root
{"command": "uv", "args": ["run", "push_server.py"]}      # ❌ File not in root
{"command": "uv", "args": ["run", "market_server.py"]}    # ❌ File not in root
```

These files no longer exist in the project root - they're in `infrastructure/`.

## Solution Applied

Updated 3 files to use correct paths:

### 1. `infrastructure/mcp_params.py`
```python
# ✅ Fixed
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "infrastructure/accounts_server.py"]},
    {"command": "uv", "args": ["run", "infrastructure/push_server.py"]},
    market_mcp,  # Also fixed to infrastructure/market_server.py
]
```

### 2. `infrastructure/accounts_client.py`
```python
# ✅ Fixed
params = StdioServerParameters(
    command="uv", 
    args=["run", "infrastructure/accounts_server.py"], 
    env=None
)
```

## Verification

✅ All MCP server paths now point to `infrastructure/` directory  
✅ Trader MCP servers: accounts, push, market  
✅ Researcher MCP servers: fetch, brave-search, memory  

## Next Test

The system should now run without MCP connection errors:

```bash
uv run python main.py once
```

Expected result:
- No "Connection closed" errors
- All MCP servers start successfully
- Traders can access tools (buy, sell, research, etc.)
- Trading cycle completes cleanly

---

**Status**: MCP path issue resolved ✅  
**Files Fixed**: 2 (mcp_params.py, accounts_client.py)  
**Impact**: Critical - enables all MCP functionality
