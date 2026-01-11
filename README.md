# 📈 AI Trading System

A multi-agent AI trading system powered by **Strands Agents SDK**, featuring autonomous traders with distinct strategies, real-time market research, and intelligent portfolio management.

## ✨ Features

- 🤖 **Multi-Agent Architecture**: 4 autonomous traders with unique strategies
- 🔬 **Nested Agents**: Each trader has a dedicated research agent
- 📊 **Real-Time Market Data**: Live data via Polygon API
- 🌐 **Web Research**: Financial news via Brave Search
- 💾 **Knowledge Graphs**: Per-trader memory using SQLite
- 📱 **Push Notifications**: Trade alerts via Pushover
- 🎨 **Live Dashboard**: Real-time Gradio UI
- 🔄 **Model Flexibility**: Support for OpenAI, DeepSeek, Gemini, Grok, and more

## 🏗️ Architecture

```
Trading Floor
 ├── Warren (Patience) → Researcher
 ├── George (Bold) → Researcher
 ├── Ray (Systematic) → Researcher
 └── Cathie (Crypto) → Researcher
```

Each trader:
- Has a unique investment strategy
- Can research stocks independently
- Makes autonomous buy/sell decisions
- Manages its own portfolio

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- API Keys:
  - OpenAI (or other LLM provider)
  - Brave Search
  - Polygon.io
  - Pushover (optional)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd traders

# Install dependencies
pip install -r requirements.txt
# or with uv
uv pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env`:

```bash
# Required API Keys
OPENAI_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# Optional
PUSHOVER_USER=your_user_key
PUSHOVER_TOKEN=your_token

# Feature Flags
USE_LEGACY_AGENTS=false         # Use Strands (default) or OpenAI Agents
USE_MANY_MODELS=false           # Use different models per trader

# Execution
RUN_EVERY_N_MINUTES=60          # Trading cycle interval
RUN_EVEN_WHEN_MARKET_IS_CLOSED=false
```

### Running

**Start the trading system:**
```bash
python main.py
```

**Run a single cycle (testing):**
```bash
python main.py once
```

**Launch the UI dashboard:**
```bash
python app.py
```

**Use legacy OpenAI Agents SDK:**
```bash
export USE_LEGACY_AGENTS=true
python main.py
```

## 📁 Project Structure

```
traders/
├── agents/              # Main agent implementations (Strands SDK)
│   ├── researcher.py   # Research agent
│   ├── trader.py       # Trading agent
│   └── trading_floor.py # Orchestration
├── legacy/             # Legacy OpenAI Agents implementation
├── core/               # Shared utilities
│   ├── model_providers.py
│   ├── templates.py
│   └── observability.py
├── infrastructure/     # MCP servers, database
├── tests/              # Test suite
├── docs/               # Documentation
├── main.py            # Entry point
└── app.py             # Gradio UI
```

## 🎯 Trading Strategies

### Warren (Patience)
- **Style**: Value investing
- **Approach**: Long-term holds, fundamentals-focused
- **Risk**: Conservative

### George (Bold)
- **Style**: Aggressive growth
- **Approach**: High conviction, concentrated positions
- **Risk**: High

### Ray (Systematic)
- **Style**: Diversification
- **Approach**: Risk-parity, balanced portfolio
- **Risk**: Moderate

### Cathie (Crypto)
- **Style**: Innovation-focused
- **Approach**: Tech and crypto exposure
- **Risk**: Very high

## 🔧 Development

### Project Organization

The project uses a modular structure:

- **`agents/`**: Strands-based implementations (default)
- **`legacy/`**: OpenAI Agents implementations (reference)
- **`core/`**: Shared utilities (models, templates, observability)
- **`infrastructure/`**: MCP servers, database, external services

### Adding a New Trader

1. Modify `agents/trading_floor.py`:
```python
names = ["Warren", "George", "Ray", "Cathie", "NewTrader"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto", "YourStrategy"]
```

2. Add strategy in `core/templates.py`:
```python
def trader_instructions(name: str) -> str:
    strategies = {
        "NewTrader": "Your custom strategy here...",
        # ...
    }
```

3. Initialize account:
```bash
# Account will be auto-created on first run
```

### Testing

```bash
# Validation tests
python tests/validation/phase0_validation.py

# Quick tests
python tests/test_trader_quick.py
python tests/test_researcher_quick.py

# Standalone agent test
python agents/trader.py
```

### Model Providers

The system supports multiple LLM providers via `ModelProvider`:

```python
from core.model_providers import ModelProvider

# OpenAI
model = ModelProvider.get_strands_model("gpt-4o-mini")

# DeepSeek
model = ModelProvider.get_strands_model("deepseek-chat")

# Gemini
model = ModelProvider.get_strands_model("gemini-2.5-flash-preview-04-17")

# Grok
model = ModelProvider.get_strands_model("grok-3-mini-beta")

# OpenRouter (any model)
model = ModelProvider.get_strands_model("anthropic/claude-3.5-sonnet")
```

## 📊 Monitoring

### Gradio Dashboard
- Real-time agent activity
- Tool invocations
- Trading decisions
- Portfolio performance

### Database
SQLite database (`accounts.db`) contains:
- `accounts`: Balances and holdings
- `transactions`: Trade history
- `logs`: Agent activity logs

View with:
```bash
sqlite3 accounts.db
sqlite> SELECT * FROM logs ORDER BY datetime DESC LIMIT 10;
```

## 🔄 Migration from OpenAI Agents

This project was migrated from OpenAI Agents SDK to Strands Agents SDK.

**Key Changes:**
- `Agent(instructions=...)` → `Agent(system_prompt=...)`
- `Runner.run()` → `agent.invoke_async()`
- `.as_tool()` → `@tool` decorator
- `MCPServerStdio` → `MCPClient`

See [Migration Documentation](docs/migration/) for full details.

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
uv pip install -r requirements.txt
```

### MCP connection issues
```bash
# Check MCP servers are accessible
npx -y @modelcontextprotocol/server-brave-search --help
```

### Database locked
```bash
# Close Gradio UI or other connections to accounts.db
```

### Legacy mode not working
```bash
# Make sure OpenAI Agents SDK is installed
pip install openai-agents
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Migration Guide](docs/migration/MIGRATION_COMPLETE.md) - OpenAI → Strands migration
- [Legacy README](legacy/README.md) - Using OpenAI Agents SDK

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional trading strategies
- More LLM providers
- Enhanced error handling
- Backtesting framework
- Performance metrics

## ⚠️ Disclaimer

This is an experimental trading system for educational purposes. 

**DO NOT** use this with real money without:
- Thorough testing
- Risk management
- Understanding of limitations
- Compliance with regulations

The agents make autonomous decisions based on LLM outputs, which can be unpredictable.

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- **Strands Agents SDK** - Modern agent framework
- **OpenAI Agents SDK** - Original implementation
- **Model Context Protocol (MCP)** - Tool integration
- **Polygon.io** - Market data
- **Brave Search** - Web research
- **Gradio** - UI framework
