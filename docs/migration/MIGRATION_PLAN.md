# Migration Plan: OpenAI Agents SDK to Strands Agents SDK

## Executive Summary

This document outlines a comprehensive migration strategy for the **Traders** project from OpenAI Agents SDK (`openai-agents==0.0.17`) to AWS Strands Agents SDK. The migration will be performed iteratively in small, testable chunks to minimize risk and ensure continuity of functionality.

## Current Architecture Analysis

### Technology Stack
- **Framework**: OpenAI Agents SDK (v0.0.17)
- **Model Providers**: Multiple (OpenAI, DeepSeek, Grok, Gemini) via OpenAI-compatible APIs
- **Tools**: Model Context Protocol (MCP) servers for external capabilities
- **UI**: Gradio-based dashboard
- **Database**: SQLite for accounts, transactions, and logs
- **Scheduling**: Asyncio-based periodic execution

### Core Components

#### 1. Agent Architecture (`traders.py`)
- **Trader Agent**: Main agent that manages trading decisions
  - Uses `Agent` class from `openai-agents`
  - Has instructions, model configuration, and tools
  - Access to nested Researcher agent via tool
- **Researcher Agent**: Nested agent for market research
  - Exposed as a tool to Trader via `agent.as_tool()`
  - Has separate MCP servers for web search and memory

#### 2. MCP Integration (`mcp_params.py`)
Trader MCP Servers:
- `accounts_server.py` - Account management (buy/sell/balance)
- `push_server.py` - Push notifications
- `market_server.py` or Polygon.io MCP - Market data

Researcher MCP Servers:
- `mcp-server-fetch` - Web page fetching
- `@modelcontextprotocol/server-brave-search` - Web search
- `mcp-memory-libsql` - Knowledge graph memory

#### 3. Multi-Agent Orchestration (`trading_floor.py`)
- Creates 4 trader instances (Warren, George, Ray, Cathie)
- Runs them concurrently with `asyncio.gather()`
- Scheduled execution every N minutes
- Each trader alternates between trading and rebalancing

#### 4. Observability (`tracers.py`)
- Custom `LogTracer` extending `TracingProcessor`
- Logs to SQLite database
- Tracks trace start/end, span start/end

#### 5. UI Layer (`app.py`)
- Separate Gradio dashboard
- Real-time updates of portfolio values, charts, transactions
- No direct coupling to agent runtime

## Strands Agents SDK: Key Differences

### Similarities (Easy Migration)
1. **Agent class structure** - Similar agent creation with instructions, model, tools
2. **MCP support** - Native MCP integration via `MCPServerStdio`
3. **Multi-agent patterns** - Supports agent-as-tool, swarm, graph patterns
4. **Async/await patterns** - Fully async compatible
5. **Observability** - Built-in tracing and telemetry

### Key Differences (Requires Adaptation)

| Feature | OpenAI Agents | Strands Agents | Migration Strategy |
|---------|--------------|----------------|-------------------|
| **Agent invocation** | `Runner.run(agent, message, max_turns)` | `agent.invoke(message)` or `agent(message)` | Update runner calls |
| **Model providers** | OpenAI-compatible clients | Provider-specific classes (OpenAI, Anthropic, Bedrock, etc.) | Use LiteLLM provider for unified interface |
| **Tracing** | `TracingProcessor` base class | Telemetry configuration with OpenTelemetry | Adapt LogTracer to new telemetry API |
| **Agent as tool** | `agent.as_tool()` | Agents as Tools pattern | Similar pattern, verify API compatibility |
| **Session management** | Built-in with `Agent` | Explicit session managers | Add session manager for conversation history |

## Migration Strategy: Incremental Phases

### Phase 0: Preparation (No Code Changes)
**Goal**: Set up Strands environment and validate compatibility

**Tasks**:
1. Review Strands documentation thoroughly
2. Create a separate `strands-migration` branch
3. Install Strands SDK alongside existing dependencies
4. Verify MCP server compatibility with Strands
5. Test basic Strands agent creation in isolation

**Success Criteria**:
- Strands SDK installed and importable
- Simple "hello world" agent runs successfully
- MCP servers start without errors

**Files Created**:
- `strands_test.py` - Validation script

**Estimated Effort**: 1-2 hours

---

### Phase 1: Model Provider Abstraction
**Goal**: Create a model provider layer compatible with both frameworks

**Rationale**: Model configuration is the foundation. Starting here enables parallel testing.

**Implementation**:

Create `model_providers.py`:
```python
from strands import OpenAIModel, LiteLLMModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

class ModelProvider:
    """Abstraction layer for model providers"""
    
    @staticmethod
    def get_strands_model(model_name: str):
        """Get Strands-compatible model instance"""
        
        # For unified multi-provider support, use LiteLLM
        if "/" in model_name:  # OpenRouter format
            return LiteLLMModel(
                model=model_name,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            )
        elif "deepseek" in model_name:
            return LiteLLMModel(
                model=model_name,
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1"
            )
        elif "grok" in model_name:
            return LiteLLMModel(
                model=model_name,
                api_key=os.getenv("GROK_API_KEY"),
                base_url="https://api.x.ai/v1"
            )
        elif "gemini" in model_name:
            return LiteLLMModel(
                model=model_name,
                api_key=os.getenv("GOOGLE_API_KEY"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        else:
            # Default OpenAI
            return OpenAIModel(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY")
            )
    
    @staticmethod
    def get_openai_agents_model(model_name: str):
        """Existing logic - keep for backward compatibility"""
        # Current implementation from traders.py
        pass
```

**Migration Steps**:
1. Create `model_providers.py`
2. Update imports in `traders.py` to use new provider
3. Add feature flag to switch between old/new model creation
4. Test with single trader instance

**Testing**:
```python
# Test script: test_model_provider.py
import asyncio
from model_providers import ModelProvider

async def test_strands_model():
    model = ModelProvider.get_strands_model("gpt-4o-mini")
    print(f"Created Strands model: {model}")
    # Add basic inference test here

asyncio.run(test_strands_model())
```

**Success Criteria**:
- Model provider creates Strands models successfully
- No breaking changes to existing code
- Can toggle between old/new providers with flag

**Files Modified**:
- `traders.py` - Add conditional model provider usage

**Files Created**:
- `model_providers.py`
- `test_model_provider.py`

**Estimated Effort**: 2-3 hours

---

### Phase 2: Simple Agent Migration (Researcher)
**Goal**: Migrate the simpler Researcher agent first

**Rationale**: Researcher has fewer dependencies (no nested agents), making it ideal for learning Strands patterns.

**Implementation**:

Create `strands_researcher.py`:
```python
from strands import Agent
from strands.mcp import MCPServerStdio
from contextlib import AsyncExitStack
from model_providers import ModelProvider
from templates import researcher_instructions
from mcp_params import researcher_mcp_server_params

async def get_strands_researcher(trader_name: str, model_name: str) -> Agent:
    """Create Researcher agent using Strands SDK"""
    
    async with AsyncExitStack() as stack:
        mcp_servers = [
            await stack.enter_async_context(
                MCPServerStdio(params, client_session_timeout_seconds=120)
            )
            for params in researcher_mcp_server_params(trader_name)
        ]
        
        researcher = Agent(
            name="Researcher",
            instructions=researcher_instructions(),
            model=ModelProvider.get_strands_model(model_name),
            mcp_servers=mcp_servers,
        )
        
        return researcher

async def test_researcher_standalone():
    """Test researcher in isolation"""
    researcher = await get_strands_researcher("Warren", "gpt-4o-mini")
    result = await researcher.invoke("Research Tesla stock performance this week")
    print(result.last_message)
```

**Strands API Mapping**:
- `Runner.run(agent, message, max_turns)` → `agent.invoke(message)`
- Access final response: `result.last_message` or `result.messages[-1]`
- Session handling: May need explicit session manager for conversation history

**Migration Steps**:
1. Create `strands_researcher.py` with Strands Agent implementation
2. Create side-by-side test comparing outputs
3. Verify MCP tools are accessible
4. Check web search and memory operations work correctly

**Testing**:
```python
# test_researcher_migration.py
async def compare_researchers():
    # Old implementation
    old_researcher = await get_researcher(...)
    old_result = await Runner.run(old_researcher, query, max_turns=30)
    
    # New implementation
    new_researcher = await get_strands_researcher(...)
    new_result = await new_researcher.invoke(query)
    
    print("Old:", old_result)
    print("New:", new_result.last_message)
```

**Success Criteria**:
- Researcher agent responds correctly to queries
- MCP tools (fetch, Brave search, memory) work
- Responses comparable to original implementation

**Files Created**:
- `strands_researcher.py`
- `test_researcher_migration.py`

**Estimated Effort**: 3-4 hours

---

### Phase 3: Nested Agent Pattern (Agent-as-Tool)
**Goal**: Implement Researcher as a tool for Trader using Strands patterns

**Rationale**: The core architecture relies on nested agents. Must validate this pattern works in Strands.

**Documentation Reference**: 
- [Agents as Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/)
- Strands supports similar pattern to `agent.as_tool()`

**Implementation**:

Update `strands_researcher.py`:
```python
from strands.tools import tool
from templates import research_tool

async def get_strands_researcher_tool(trader_name: str, model_name: str):
    """Convert Researcher agent to a tool for Trader"""
    
    researcher = await get_strands_researcher(trader_name, model_name)
    
    # Strands approach: wrap agent invocation as a tool
    @tool(
        name="Researcher",
        description=research_tool()
    )
    async def researcher_tool(query: str) -> str:
        """Research tool that delegates to Researcher agent"""
        result = await researcher.invoke(query)
        return result.last_message
    
    return researcher_tool
```

**Alternative Pattern** (if Strands has direct agent-as-tool support):
```python
# Check Strands docs for exact API
researcher_tool = researcher.as_tool(
    name="Researcher",
    description=research_tool()
)
```

**Migration Steps**:
1. Implement researcher tool wrapper
2. Test tool invocation from simple test script
3. Verify tool parameters and responses
4. Validate error handling

**Testing**:
```python
async def test_researcher_tool():
    tool = await get_strands_researcher_tool("Warren", "gpt-4o-mini")
    
    # Test direct invocation
    result = await tool("Find latest news on AI stocks")
    print(f"Tool result: {result}")
```

**Success Criteria**:
- Researcher tool callable as a function
- Returns string responses suitable for Trader
- Error handling propagates correctly

**Files Modified**:
- `strands_researcher.py`

**Files Created**:
- `test_researcher_tool.py`

**Estimated Effort**: 2-3 hours

---

### Phase 4: Trader Agent Migration
**Goal**: Migrate main Trader agent to Strands SDK

**Rationale**: With Researcher tool working, now migrate the orchestrating Trader agent.

**Implementation**:

Create `strands_traders.py`:
```python
from strands import Agent
from strands.mcp import MCPServerStdio
from contextlib import AsyncExitStack
from model_providers import ModelProvider
from templates import trader_instructions, trade_message, rebalance_message
from mcp_params import trader_mcp_server_params
from strands_researcher import get_strands_researcher_tool
from accounts_client import read_accounts_resource, read_strategy_resource
import json

class StrandsTrader:
    def __init__(self, name: str, lastname: str = "Trader", model_name: str = "gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.agent = None
        self.do_trade = True
    
    async def create_agent(self, trader_mcp_servers, researcher_tool) -> Agent:
        """Create Trader agent with Strands SDK"""
        
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),
            model=ModelProvider.get_strands_model(self.model_name),
            tools=[researcher_tool],
            mcp_servers=trader_mcp_servers,
        )
        
        return self.agent
    
    async def get_account_report(self) -> str:
        """Same as original"""
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)
        return json.dumps(account_json)
    
    async def run_agent(self, trader_mcp_servers, researcher_tool):
        """Run agent using Strands invoke pattern"""
        
        self.agent = await self.create_agent(trader_mcp_servers, researcher_tool)
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        
        # Strands invocation - simpler than Runner.run
        result = await self.agent.invoke(message)
        
        return result
    
    async def run_with_mcp_servers(self):
        """Setup MCP servers and run agent"""
        
        async with AsyncExitStack() as stack:
            # Setup trader MCP servers
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            
            # Create researcher tool
            researcher_tool = await get_strands_researcher_tool(
                self.name,
                self.model_name
            )
            
            await self.run_agent(trader_mcp_servers, researcher_tool)
    
    async def run(self):
        """Main entry point - same interface as original"""
        try:
            await self.run_with_mcp_servers()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        self.do_trade = not self.do_trade
```

**Key Changes**:
1. Removed `trace()` wrapper (will add back in Phase 6)
2. Removed `max_turns` - Strands may handle differently (check docs)
3. Simplified invocation pattern
4. Maintained same public interface for compatibility

**Migration Steps**:
1. Create `strands_traders.py` with StrandsTrader class
2. Test single trader execution
3. Verify MCP tools accessible (buy_shares, sell_shares, etc.)
4. Compare trading decisions with original

**Testing**:
```python
# test_strands_trader.py
async def test_single_trader():
    trader = StrandsTrader("Warren", "Patience", "gpt-4o-mini")
    await trader.run()
    
    # Verify account state changed
    from accounts import Account
    account = Account.get("Warren")
    print(f"Balance: {account.balance}")
    print(f"Holdings: {account.holdings}")
```

**Success Criteria**:
- Trader agent executes without errors
- Can invoke Researcher tool successfully
- Makes buy/sell decisions via MCP tools
- Account database updated correctly

**Files Created**:
- `strands_traders.py`
- `test_strands_trader.py`

**Estimated Effort**: 4-5 hours

---

### Phase 5: Multi-Agent Orchestration
**Goal**: Migrate concurrent multi-trader execution

**Rationale**: Validate Strands can handle multiple concurrent agents with shared resources.

**Implementation**:

Create `strands_trading_floor.py`:
```python
from strands_traders import StrandsTrader
from typing import List
import asyncio
from dotenv import load_dotenv
import os
from market import is_market_open

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

def create_strands_traders() -> List[StrandsTrader]:
    """Create Strands-based traders"""
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(StrandsTrader(name, lastname, model_name))
    return traders

async def run_every_n_minutes():
    """Main execution loop - compatible interface"""
    # Observability will be added in Phase 6
    traders = create_strands_traders()
    
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            # Run all traders concurrently
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Market is closed, skipping run")
        
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

if __name__ == "__main__":
    print(f"Starting Strands trading floor - every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
```

**Migration Steps**:
1. Create `strands_trading_floor.py`
2. Test with 2 traders first, then scale to 4
3. Monitor for race conditions in database access
4. Verify concurrent MCP server usage

**Testing**:
```python
# test_multi_trader.py
async def test_concurrent_traders():
    traders = [
        StrandsTrader("Warren", "Patience", "gpt-4o-mini"),
        StrandsTrader("George", "Bold", "gpt-4o-mini"),
    ]
    
    await asyncio.gather(*[trader.run() for trader in traders])
    
    # Verify both accounts modified
    for trader in traders:
        account = Account.get(trader.name)
        print(f"{trader.name} balance: {account.balance}")
```

**Success Criteria**:
- Multiple traders execute concurrently
- No database locking issues
- Each trader maintains separate state
- Comparable performance to original

**Files Created**:
- `strands_trading_floor.py`
- `test_multi_trader.py`

**Estimated Effort**: 2-3 hours

---

### Phase 6: Observability & Tracing
**Goal**: Restore tracing and logging functionality with Strands telemetry

**Rationale**: Observability is critical for debugging and monitoring production behavior.

**Documentation Reference**:
- [Strands Observability](https://strandsagents.com/latest/documentation/docs/user-guide/observability-debugging/observability/)
- [Metrics](https://strandsagents.com/latest/documentation/docs/user-guide/observability-debugging/metrics/)
- [Traces](https://strandsagents.com/latest/documentation/docs/user-guide/observability-debugging/traces/)

**Implementation**:

Create `strands_observability.py`:
```python
from strands.telemetry import TelemetryConfig, Tracer
from database import write_log
import os

class StrandsLogTracer:
    """Adapter for Strands telemetry to write to SQLite logs"""
    
    def __init__(self):
        self.current_trader_name = None
    
    def set_trader_name(self, name: str):
        """Set context for current trader"""
        self.current_trader_name = name
    
    def on_agent_start(self, event):
        """Called when agent starts processing"""
        if self.current_trader_name:
            agent_name = event.get("agent_name", "unknown")
            write_log(
                self.current_trader_name,
                "agent",
                f"Started: {agent_name}"
            )
    
    def on_agent_end(self, event):
        """Called when agent finishes"""
        if self.current_trader_name:
            agent_name = event.get("agent_name", "unknown")
            write_log(
                self.current_trader_name,
                "agent",
                f"Ended: {agent_name}"
            )
    
    def on_tool_start(self, event):
        """Called when tool execution starts"""
        if self.current_trader_name:
            tool_name = event.get("tool_name", "unknown")
            write_log(
                self.current_trader_name,
                "function",
                f"Started {tool_name}"
            )
    
    def on_tool_end(self, event):
        """Called when tool execution ends"""
        if self.current_trader_name:
            tool_name = event.get("tool_name", "unknown")
            write_log(
                self.current_trader_name,
                "function",
                f"Ended {tool_name}"
            )
    
    def on_model_start(self, event):
        """Called when LLM generation starts"""
        if self.current_trader_name:
            write_log(
                self.current_trader_name,
                "generation",
                "Started generation"
            )
    
    def on_model_end(self, event):
        """Called when LLM generation ends"""
        if self.current_trader_name:
            write_log(
                self.current_trader_name,
                "response",
                "Ended generation"
            )

def configure_strands_telemetry() -> StrandsLogTracer:
    """Setup Strands telemetry configuration"""
    
    log_tracer = StrandsLogTracer()
    
    # Configure Strands telemetry (adjust based on actual API)
    config = TelemetryConfig(
        enabled=True,
        # Add callbacks/hooks for our log tracer
        # Exact API depends on Strands implementation
    )
    
    return log_tracer
```

**Update StrandsTrader**:
```python
# In strands_traders.py

from strands_observability import configure_strands_telemetry

class StrandsTrader:
    def __init__(self, name: str, lastname: str = "Trader", model_name: str = "gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.agent = None
        self.do_trade = True
        self.tracer = configure_strands_telemetry()
    
    async def run(self):
        """Main entry point with tracing"""
        try:
            self.tracer.set_trader_name(self.name)
            
            trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
            write_log(self.name, "trace", f"Started: {trace_name}")
            
            await self.run_with_mcp_servers()
            
            write_log(self.name, "trace", f"Ended: {trace_name}")
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
            write_log(self.name, "trace", f"Error: {e}")
        
        self.do_trade = not self.do_trade
```

**Migration Steps**:
1. Research exact Strands telemetry API
2. Create adapter layer for database logging
3. Integrate with StrandsTrader
4. Test log output matches original format
5. Update Gradio UI if log format changed

**Testing**:
```python
# test_strands_observability.py
async def test_logging():
    trader = StrandsTrader("Warren", "Patience", "gpt-4o-mini")
    await trader.run()
    
    # Verify logs written
    from database import read_log
    logs = read_log("Warren", last_n=20)
    
    log_types = [log[1] for log in logs]
    assert "trace" in log_types
    assert "agent" in log_types
    assert "function" in log_types
```

**Success Criteria**:
- Logs written to database in original format
- Gradio UI displays logs correctly
- All trace/span events captured
- No performance degradation

**Files Created**:
- `strands_observability.py`
- `test_strands_observability.py`

**Files Modified**:
- `strands_traders.py`

**Estimated Effort**: 4-5 hours

---

### Phase 7: Feature Parity & Edge Cases
**Goal**: Ensure complete feature parity and handle edge cases

**Implementation Tasks**:

1. **Max Turns Handling**
   - Original uses `max_turns=30` in `Runner.run()`
   - Research Strands equivalent (may be agent config or invoke parameter)
   - Add configuration if needed

2. **Session Management**
   - Verify conversation history handling
   - Original may rely on implicit session management
   - May need explicit `SessionManager` for Strands

3. **Error Handling**
   - Test MCP server failures
   - Test API rate limits
   - Test invalid stock symbols
   - Test insufficient funds scenarios

4. **Streaming Support** (if needed)
   - Original doesn't use streaming
   - Strands supports streaming via callback handlers
   - Document for future enhancement

5. **Push Notifications**
   - Verify `push_server.py` MCP integration works
   - Test notification delivery

**Testing Scenarios**:
```python
# test_edge_cases.py

async def test_max_turns():
    """Verify max turns configuration"""
    trader = StrandsTrader("Warren", "Patience", "gpt-4o-mini")
    # Add max_turns configuration
    # Test agent stops after limit
    pass

async def test_mcp_failure():
    """Test graceful handling of MCP server failure"""
    # Start trader with intentionally broken MCP server
    # Verify error logged and trader continues
    pass

async def test_insufficient_funds():
    """Test insufficient funds scenario"""
    account = Account.get("TestTrader")
    account.balance = 10.0
    account.save()
    
    trader = StrandsTrader("TestTrader", "Test", "gpt-4o-mini")
    await trader.run()
    
    # Should log error, not crash
    logs = read_log("TestTrader", last_n=50)
    # Verify error handling
```

**Success Criteria**:
- All edge cases handled gracefully
- Error messages informative
- System stable under failure conditions
- Logs contain diagnostic information

**Files Created**:
- `test_edge_cases.py`

**Estimated Effort**: 3-4 hours

---

### Phase 8: Integration & Validation
**Goal**: Full end-to-end testing with Gradio UI

**Implementation**:

Create feature flag system in `.env`:
```bash
# Feature flags
USE_STRANDS_AGENTS=true  # Toggle between OpenAI Agents and Strands
RUN_EVERY_N_MINUTES=60
RUN_EVEN_WHEN_MARKET_IS_CLOSED=false
USE_MANY_MODELS=false
```

Create unified entry point `main.py`:
```python
import os
from dotenv import load_dotenv
import asyncio

load_dotenv(override=True)

USE_STRANDS = os.getenv("USE_STRANDS_AGENTS", "false").strip().lower() == "true"

if USE_STRANDS:
    print("Using Strands Agents SDK")
    from strands_trading_floor import run_every_n_minutes
else:
    print("Using OpenAI Agents SDK")
    from trading_floor import run_every_n_minutes

if __name__ == "__main__":
    asyncio.run(run_every_n_minutes())
```

Update `app.py` imports:
```python
# app.py stays mostly the same
# It reads from database, so backend is transparent
# May need to update trader class imports for type checking

import os
from dotenv import load_dotenv

load_dotenv(override=True)

USE_STRANDS = os.getenv("USE_STRANDS_AGENTS", "false").strip().lower() == "true"

# Import appropriate trader class for instantiation
if USE_STRANDS:
    from strands_trading_floor import names, lastnames, short_model_names
else:
    from trading_floor import names, lastnames, short_model_names

# Rest of app.py unchanged - it reads from database
```

**Testing Scenarios**:

1. **Side-by-side comparison**
   ```bash
   # Run OpenAI version for 1 hour
   USE_STRANDS_AGENTS=false RUN_EVERY_N_MINUTES=10 python main.py
   
   # Reset accounts
   
   # Run Strands version for 1 hour
   USE_STRANDS_AGENTS=true RUN_EVERY_N_MINUTES=10 python main.py
   
   # Compare: trades, portfolio values, log entries
   ```

2. **Long-running stability test**
   ```bash
   # Run for 24 hours with Strands
   USE_STRANDS_AGENTS=true python main.py
   
   # Monitor:
   # - Memory usage
   # - Database size
   # - Error frequency
   # - Trading performance
   ```

3. **UI validation**
   ```bash
   # Start Strands backend
   USE_STRANDS_AGENTS=true python main.py &
   
   # Start Gradio UI
   python app.py
   
   # Verify:
   # - Real-time updates work
   # - Charts render correctly
   # - Logs display properly
   # - No UI errors
   ```

**Success Criteria**:
- Strands version produces comparable results
- UI works seamlessly with either backend
- No regressions in functionality
- Performance acceptable (within 20% of original)
- Can toggle between versions without code changes

**Files Created**:
- `main.py`
- `test_integration.py`

**Files Modified**:
- `app.py` (minimal changes for import compatibility)

**Estimated Effort**: 4-5 hours

---

### Phase 9: Documentation & Cleanup
**Goal**: Clean up codebase and document migration

**Tasks**:

1. **Update README.md**
   ```markdown
   # Traders - AI Trading Simulation
   
   ## Architecture
   Now supports both OpenAI Agents and Strands Agents SDK.
   
   ### Switching Frameworks
   Set `USE_STRANDS_AGENTS=true` in `.env` to use Strands.
   
   ### Installation
   ```bash
   pip install -r requirements.txt
   ```
   
   ### Running
   ```bash
   python main.py  # Backend
   python app.py   # UI
   ```
   ```

2. **Update requirements.txt**
   ```
   # Core dependencies
   gradio>=5.7.0
   pydantic==2.11.5
   python-dotenv==1.2.1
   requests==2.32.5
   nest-asyncio==1.6.0
   
   # Agent frameworks (choose one or both)
   openai-agents==0.0.17  # Original
   strands-agents>=1.0.0  # New
   
   # Model providers
   openai==1.85.0
   
   # ... rest of dependencies
   ```

3. **Create migration guide**
   - `MIGRATION_GUIDE.md` - This document
   - Lessons learned
   - Known issues
   - Performance comparison

4. **Code cleanup**
   - Remove debug print statements
   - Add type hints where missing
   - Update docstrings
   - Format with black/ruff

5. **Create comparison report**
   - Trading performance metrics
   - Execution time comparison
   - Resource usage
   - Feature compatibility matrix

**Files Created**:
- `MIGRATION_GUIDE.md` (this document)
- `COMPARISON_REPORT.md`

**Files Modified**:
- `README.md`
- `requirements.txt`
- All migrated files (cleanup)

**Estimated Effort**: 3-4 hours

---

### Phase 10: Deprecation & Production Cutover
**Goal**: Fully migrate to Strands and remove OpenAI Agents dependency

**Tasks**:

1. **Validate production readiness**
   - Run for 1 week with Strands in production
   - Monitor error rates
   - Collect performance metrics
   - Gather user feedback (if applicable)

2. **Set Strands as default**
   ```bash
   # .env.example
   USE_STRANDS_AGENTS=true  # Default to Strands
   ```

3. **Deprecation plan**
   - Add deprecation warnings to old code
   - Schedule removal date (e.g., 2 months after cutover)
   - Document rollback procedure

4. **Remove old code** (after confidence period)
   - Delete `traders.py` (keep as `traders_openai_agents_legacy.py` initially)
   - Delete `trading_floor.py`
   - Remove `openai-agents` from requirements.txt
   - Update all imports

5. **Rename new files**
   ```bash
   mv strands_traders.py traders.py
   mv strands_trading_floor.py trading_floor.py
   mv strands_researcher.py researcher.py
   ```

**Success Criteria**:
- Production stable on Strands for 1+ week
- No critical issues
- Team comfortable with new codebase
- Documentation complete

**Estimated Effort**: 2-3 hours + observation period

---

## Implementation Checklist

### Pre-Migration
- [ ] Review Strands documentation thoroughly
- [ ] Set up development environment
- [ ] Create feature branch
- [ ] Back up production database

### Phase-by-Phase
- [ ] Phase 0: Preparation (1-2 hours)
- [ ] Phase 1: Model Provider Abstraction (2-3 hours)
- [ ] Phase 2: Simple Agent Migration (3-4 hours)
- [ ] Phase 3: Nested Agent Pattern (2-3 hours)
- [ ] Phase 4: Trader Agent Migration (4-5 hours)
- [ ] Phase 5: Multi-Agent Orchestration (2-3 hours)
- [ ] Phase 6: Observability & Tracing (4-5 hours)
- [ ] Phase 7: Feature Parity & Edge Cases (3-4 hours)
- [ ] Phase 8: Integration & Validation (4-5 hours)
- [ ] Phase 9: Documentation & Cleanup (3-4 hours)
- [ ] Phase 10: Deprecation & Production Cutover (2-3 hours + observation)

**Total Estimated Effort**: 30-40 hours of active development + observation period

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Strands API incompatibility | High | Medium | Thorough Phase 0 validation; maintain feature flag |
| Performance degradation | Medium | Low | Benchmark each phase; optimize if needed |
| MCP compatibility issues | High | Low | Test in Phase 2; MCP is standard protocol |
| Loss of observability | Medium | Medium | Dedicated Phase 6; test thoroughly |
| Nested agent pattern failure | High | Low | Validate in Phase 3 before proceeding |

### Process Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Extended development time | Low | Medium | Small phases; can pause after any phase |
| Incomplete migration | Medium | Low | Feature flag allows hybrid operation |
| Production issues | High | Low | Long validation period; easy rollback |

### Rollback Plan

At any phase, can rollback by:
1. Set `USE_STRANDS_AGENTS=false` in `.env`
2. Restart services
3. System returns to OpenAI Agents implementation

No data loss possible - database schema unchanged.

---

## Success Metrics

### Functional Metrics
- ✅ All 4 traders execute successfully
- ✅ Trading decisions logged correctly
- ✅ Gradio UI displays all data
- ✅ MCP servers integrate properly
- ✅ Multi-agent orchestration stable

### Performance Metrics
- Agent invocation time: < 120% of baseline
- Memory usage: < 110% of baseline
- Database operations: No change (same DB)
- Concurrent execution: 4+ agents stable

### Quality Metrics
- Test coverage: > 80%
- No critical bugs after 1 week production
- All logging preserved
- Error handling complete

---

## Key API Mappings

### Agent Creation
```python
# OpenAI Agents
from agents import Agent, OpenAIChatCompletionsModel
agent = Agent(
    name="Trader",
    instructions="...",
    model=OpenAIChatCompletionsModel(model="gpt-4o-mini", openai_client=client),
    tools=[tool],
    mcp_servers=mcp_servers,
)

# Strands Agents
from strands import Agent, OpenAIModel
agent = Agent(
    name="Trader",
    instructions="...",
    model=OpenAIModel(model="gpt-4o-mini"),
    tools=[tool],
    mcp_servers=mcp_servers,
)
```

### Agent Invocation
```python
# OpenAI Agents
from agents import Runner
await Runner.run(agent, message, max_turns=30)

# Strands Agents
result = await agent.invoke(message)
# or simply: result = await agent(message)
```

### MCP Integration
```python
# OpenAI Agents
from agents.mcp import MCPServerStdio
server = MCPServerStdio(params, client_session_timeout_seconds=120)

# Strands Agents
from strands.mcp import MCPServerStdio
server = MCPServerStdio(params, client_session_timeout_seconds=120)
# Similar API!
```

### Tracing
```python
# OpenAI Agents
from agents import TracingProcessor, add_trace_processor, trace
class LogTracer(TracingProcessor):
    def on_trace_start(self, trace): pass
    def on_span_start(self, span): pass

add_trace_processor(LogTracer())
with trace("operation"):
    await agent_operation()

# Strands Agents
from strands.telemetry import TelemetryConfig
# Configure via TelemetryConfig
# Exact API to be determined from Strands docs
```

---

## Questions to Answer During Migration

### Phase 0
- [ ] Does Strands support LiteLLM for unified multi-provider?
- [ ] What's the exact API for telemetry/observability?
- [ ] Is there a max_turns equivalent?

### Phase 3
- [ ] Does Strands have `agent.as_tool()` method?
- [ ] If not, what's the recommended pattern?

### Phase 6
- [ ] What's the exact telemetry callback API?
- [ ] Can we hook into all the same events?
- [ ] Is there a simpler logging integration?

---

## Additional Considerations

### Deployment
- No deployment changes needed
- Same Docker setup works
- Same AWS infrastructure compatible
- MCP servers remain identical

### Dependencies
- Review Strands SDK dependencies for conflicts
- May need to update OpenAI client version
- Test with latest LiteLLM if using for providers

### Testing Strategy
- Unit tests for each component
- Integration tests for multi-agent
- End-to-end test with UI
- Performance benchmarks
- Load testing with multiple traders

### Documentation Needs
- API migration guide (this document)
- New developer onboarding
- Architecture decision record
- Troubleshooting guide

---

## Lessons Learned (Post-Migration)

_To be filled in after migration completion_

### What Went Well
- 

### Challenges Faced
- 

### Would Do Differently
- 

### Strands SDK Strengths
- 

### Strands SDK Limitations
- 

---

## Support & Resources

### Strands Documentation
- Main docs: https://strandsagents.com/latest/documentation/docs/
- Examples: https://strandsagents.com/latest/documentation/docs/examples/
- Python API: https://strandsagents.com/latest/documentation/docs/api-reference/python/agent/agent/

### Community
- GitHub Issues: [Strands Agents Repo]
- Community Discussion: [Link if available]

### Internal Resources
- Migration branch: `strands-migration`
- Test reports: `test_reports/`
- Benchmark data: `benchmarks/`

---

## Conclusion

This migration plan provides a structured, low-risk approach to transitioning from OpenAI Agents SDK to Strands Agents SDK. By breaking the work into small, testable phases and maintaining backward compatibility via feature flags, we can:

1. **Validate early**: Test Strands compatibility before committing
2. **Fail fast**: Detect issues in isolated components
3. **Maintain stability**: Keep production running on OpenAI Agents during migration
4. **Rollback easily**: Toggle feature flag to revert at any time
5. **Learn incrementally**: Build Strands expertise phase by phase

The incremental approach means the project can pause after any phase if priorities change, or accelerate if early phases go smoothly. Each phase delivers testable value and increases confidence in the final migration.

**Recommended Timeline**: 2-3 weeks at 2-3 hours per day, plus 1-2 weeks observation period before full cutover.

**Go/No-Go Decision Point**: After Phase 4 (Trader Agent Migration), assess whether to proceed. If Trader agent works well with Strands, the remaining phases are lower risk.
