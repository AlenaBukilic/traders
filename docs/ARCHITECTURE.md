# System Architecture

## Overview
The trading system uses a multi-agent architecture built on **Strands Agents SDK** (with OpenAI Agents as legacy fallback).

## Agent Hierarchy

```
Trading Floor (Orchestrator)
    ├── Trader: Warren (Patience Strategy)
    │   ├── Model: gpt-4o-mini (or configurable)
    │   ├── MCP Tools: Accounts, Market Data, Push Notifications
    │   └── Researcher Agent (nested)
    │       ├── Model: gpt-4o-mini (or configurable)
    │       └── MCP Tools: Web Search, Fetch, Memory
    │
    ├── Trader: George (Bold Strategy)
    │   ├── Model: deepseek-chat (if USE_MANY_MODELS)
    │   ├── MCP Tools: Accounts, Market Data, Push Notifications
    │   └── Researcher Agent (nested)
    │       └── MCP Tools: Web Search, Fetch, Memory
    │
    ├── Trader: Ray (Systematic Strategy)
    │   ├── Model: gemini-2.5-flash (if USE_MANY_MODELS)
    │   ├── MCP Tools: Accounts, Market Data, Push Notifications
    │   └── Researcher Agent (nested)
    │       └── MCP Tools: Web Search, Fetch, Memory
    │
    └── Trader: Cathie (Crypto Strategy)
        ├── Model: grok-3-mini-beta (if USE_MANY_MODELS)
        ├── MCP Tools: Accounts, Market Data, Push Notifications
        └── Researcher Agent (nested)
            └── MCP Tools: Web Search, Fetch, Memory
```

## Project Structure

```
traders/
├── agents/                       # Main agent implementations (Strands SDK)
│   ├── researcher.py            # Research agent with web search
│   ├── trader.py                # Trading agent with strategy execution
│   └── trading_floor.py         # Multi-agent orchestration
│
├── legacy/                      # Legacy OpenAI Agents implementation
│   ├── traders.py               # Original trader implementation
│   ├── trading_floor.py         # Original orchestration
│   ├── tracers.py               # OpenAI-specific tracing
│   └── README.md                # Legacy usage guide
│
├── core/                        # Shared utilities
│   ├── model_providers.py       # Model abstraction layer
│   ├── templates.py             # Prompt templates
│   └── observability.py         # Logging and tracing hooks
│
├── infrastructure/              # Infrastructure components
│   ├── accounts_server.py       # Account management MCP server
│   ├── accounts_client.py       # Account access client
│   ├── market_server.py         # Market data MCP server
│   ├── market.py                # Market utilities
│   ├── push_server.py           # Notification MCP server
│   ├── mcp_params.py            # MCP server configurations
│   └── database.py              # SQLite database utilities
│
├── tests/                       # Test suite
│   ├── validation/              # Phase validation tests
│   └── quick_tests/             # Quick validation scripts
│
├── docs/                        # Documentation
│   └── migration/               # Migration documentation
│
├── main.py                      # Main entry point
└── app.py                       # Gradio UI dashboard
```

## Infrastructure

### MCP Servers (Model Context Protocol)
The system uses MCP for tool integration:

**Trader MCP Tools:**
- `accounts_server.py`: Portfolio management, buy/sell operations
- `market_server.py`: Real-time market data (via Polygon API)
- `push_server.py`: Push notifications (via Pushover)

**Researcher MCP Tools:**
- `brave-search`: Web search for financial news
- `mcp-server-fetch`: Webpage content fetching
- `mcp-memory-libsql`: Knowledge graph per trader

### Database (SQLite)
- `accounts.db`: Account balances, holdings, transactions, logs
- `memory/*.db`: Per-trader knowledge graphs

### Models
Multi-provider support via `ModelProvider` abstraction:
- OpenAI (gpt-4o-mini, gpt-4.1-mini)
- DeepSeek (deepseek-chat)
- Google (gemini-2.5-flash)
- xAI (grok-3-mini-beta)
- OpenRouter (any model via unified API)

## Agent Communication

### Nested Agent Pattern
Trader agents use Researcher agents as tools:

```python
# Strands implementation
@tool(name="Researcher", description="Research financial news")
async def researcher_tool(query: str) -> str:
    result = await researcher.invoke_async(query)
    return result.message.content

trader = Agent(
    name="Warren",
    system_prompt=trader_instructions("Warren"),
    model=model,
    tools=[researcher_tool, *mcp_tools]
)
```

### Concurrent Execution
Multiple traders run in parallel:

```python
results = await asyncio.gather(
    *[trader.run() for trader in traders],
    return_exceptions=True
)
```

## Observability

### Strands Hooks
Custom hooks capture agent events:
- `before_invocation` / `after_invocation`
- `before_tool_call` / `after_tool_call`
- `before_model_call` / `after_model_call`

All events logged to SQLite for UI display:

```python
hook = create_log_hook("Warren")
agent = Agent(..., hooks=[hook])
```

### Gradio Dashboard
Real-time visualization of:
- Trading decisions and rationale
- Tool invocations (MCP calls)
- Model responses
- Portfolio performance

## Configuration

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=xxx
BRAVE_API_KEY=xxx
POLYGON_API_KEY=xxx
PUSHOVER_USER=xxx
PUSHOVER_TOKEN=xxx

# Feature Flags
USE_LEGACY_AGENTS=false         # Use OpenAI Agents instead of Strands
USE_MANY_MODELS=false           # Use different models per trader

# Execution
RUN_EVERY_N_MINUTES=60          # Trading cycle interval
RUN_EVEN_WHEN_MARKET_IS_CLOSED=false
```

### Trading Strategies
Each trader has a unique strategy defined in `templates.py`:
- **Warren (Patience)**: Value investing, long-term holds
- **George (Bold)**: Aggressive growth, high conviction
- **Ray (Systematic)**: Diversified, risk-parity
- **Cathie (Crypto)**: Innovation-focused, tech/crypto

## Implementation Details

### Key Differences: Strands vs OpenAI Agents

| Aspect | OpenAI Agents | Strands Agents |
|--------|---------------|----------------|
| **Agent Creation** | `Agent(instructions=...)` | `Agent(system_prompt=...)` |
| **Model Params** | `model`, `openai_client` | `model_id`, `client_args` |
| **Invocation** | `Runner.run(agent, msg)` | `await agent.invoke_async(msg)` |
| **Response** | Handled internally | Returns `AgentResult` |
| **Agent as Tool** | `.as_tool()` method | `@tool` decorator |
| **MCP Integration** | `MCPServerStdio` | `MCPClient` + transport |
| **Observability** | `add_trace_processor()` | `hooks=[...]` |

### Migration Status
- ✅ **Complete**: All agents migrated to Strands
- ✅ **Tested**: Full feature parity validated
- ✅ **Production-Ready**: Strands is default implementation
- ⚠️ **Legacy Available**: OpenAI Agents kept as fallback

For detailed migration history, see `docs/migration/MIGRATION_COMPLETE.md`.

## Deployment

### Running the System

**Normal operation (continuous):**
```bash
python main.py
```

**Single cycle (testing):**
```bash
python main.py once
```

**With Gradio UI:**
```bash
python app.py
```

**Legacy mode:**
```bash
export USE_LEGACY_AGENTS=true
python main.py
```

### Monitoring
- Logs: SQLite `accounts.db` → `logs` table
- UI: Gradio dashboard at http://localhost:7860
- Database: SQLite Browser for `accounts.db`

## Development

### Adding New Agents
1. Create agent in `agents/new_agent.py`
2. Use `ModelProvider.get_strands_model()`
3. Add logging: `hooks=[create_log_hook(name)]`
4. Export from `agents/__init__.py`

### Adding New MCP Tools
1. Create server in `infrastructure/`
2. Add params to `mcp_params.py`
3. Create `MCPClient` in agent code
4. Add to agent's `tools` list

### Testing
```bash
# Run validation tests
python tests/validation/phase0_validation.py

# Run specific test
python tests/test_trader_quick.py

# Run agent standalone
python agents/trader.py
```

## Future Enhancements
- [ ] Multi-turn conversation limits (Strands max_turns)
- [ ] Enhanced error recovery
- [ ] Performance metrics (Sharpe, returns)
- [ ] Backtesting framework
- [ ] Additional trading strategies
- [ ] More LLM providers
