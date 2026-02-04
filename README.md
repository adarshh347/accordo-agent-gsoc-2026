# Dummy Accordo Agent

> **GSoC 2026 MVP** - Agentic Workflow for Drafting Accord Project Templates

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## Project Vision

This project provides an **LLM-powered agent workflow** that converts natural language contract requirements into valid [Concerto](https://concerto.accordproject.org/) (`.cto`) models. It acts as an intelligent front-end to the Accord Project tooling.

### The Problem

Creating Accord Project templates currently requires:
- Legal/domain knowledge for the contract logic
- Technical knowledge of the Concerto modeling language
- Understanding of the Accord Project stack

### The Solution

An agentic workflow that:
1. **Understands** natural language requirements
2. **Generates** structurally correct Concerto models
3. **Validates** output using official Accord CLI tools
4. **Iterates** on errors until the model is valid

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (Natural Language)            │
│         "I need a loan agreement with borrower info..."     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Requirements Analyst Agent                      │
│         (NL → Structured Intent JSON)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Concerto Model Generator Agent                    │
│         (Structured Intent → .cto file)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Validation Loop                             │
│    ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│    │ Generate CTO │───▶│ Validate via │───▶│  Success?  │  │
│    │              │    │ concerto-cli │    │            │  │
│    └──────────────┘    └──────────────┘    └─────┬──────┘  │
│           ▲                                       │         │
│           │              No                       │ Yes     │
│           └───────────────────────────────────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Valid .cto Output                         │
└─────────────────────────────────────────────────────────────┘
```

## Core Concepts

### Agent Personas

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Requirements Analyst** | Extracts structured intent from natural language | User's description | JSON with namespace, concepts, fields |
| **Model Generator** | Creates valid Concerto syntax | Structured intent | `.cto` file content |

### Tool Integration

This project **consumes** Accord Project tools via CLI - it does not modify them:

- `@accordproject/concerto-cli` - For parsing and validating `.cto` models

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- [Groq API Key](https://console.groq.com/keys) (free)

### Setup

```bash
# Clone the repository
git clone https://github.com/adarshh347/dummy-accordo-agent.git
cd dummy-accordo-agent

# Install Node.js dependencies (Accord CLI tools)
npm install

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your Groq API key (free at https://console.groq.com/keys)
```

## Usage

### Quick Start (Without pip install)

```bash
# Set your Groq API key
export GROQ_API_KEY=your_key_here

# Run the CLI directly
python3 accordo.py generate "I need a loan agreement with borrower and amount"
```

### CLI Commands

#### Generate a Model
```bash
# Basic usage
python3 accordo.py generate "A loan agreement with borrower name and loan amount"

# With custom namespace
python3 accordo.py generate "Vehicle rental contract" -n org.rental

# Output to specific directory
python3 accordo.py generate "Employee contract" -o ./models

# Quiet mode (just output CTO)
python3 accordo.py generate "Simple agreement" -q
```

#### Validate a Model
```bash
# Validate a .cto file
python3 accordo.py validate examples/valid_model.cto

# Verbose output
python3 accordo.py validate model.cto -v
```

#### Preview Structured Intent
```bash
# See what the agent extracts before generating CTO
python3 accordo.py preview "A rental agreement with renter and vehicle info"
```

#### System Info
```bash
# Check configuration status
python3 accordo.py info
```

### If Installed via pip

```bash
# After: pip install -e .
accordo generate "Your description here"
accordo validate output/model.cto
accordo preview "Your description"
accordo info
```

### Web UI

The project includes a web-based frontend for generating models.

```bash
# Terminal 1: Start the API server
python3 api.py

# Terminal 2: Serve the frontend
python3 -m http.server 3000 -d frontend

# Open http://localhost:3000 in your browser
```

**API Endpoints:**
- `POST /generate` - Generate a model from description
- `POST /validate` - Validate CTO code
- `GET /health` - Check API status
- `GET /docs` - Interactive API documentation


## Project Structure

```
dummy-accordo-agent/
├── accordo.py            # CLI entry point
├── api.py                # REST API server (FastAPI)
├── src/
│   ├── agents/           # Agent definitions
│   │   ├── requirements_agent.py  # NL → Structured Intent
│   │   └── model_agent.py         # Intent → Valid .cto
│   │
│   ├── tools/            # CLI wrappers
│   │   └── concerto_tools.py      # concerto-cli Python wrapper
│   │
│   ├── cli/              # Command-line interface
│   │   └── main.py                # Click-based CLI
│   │
│   ├── prompts/          # LLM prompt templates
│   │   └── templates.py           # Agent prompts
│   │
│   ├── models.py         # Pydantic data models
│   ├── llm_client.py     # Groq API wrapper
│   └── workflow.py       # Main orchestrator
│
├── frontend/             # Web UI
│   ├── index.html        # Main page
│   ├── styles.css        # Styling
│   └── app.js            # Frontend logic
│
├── scripts/              # Development scripts
│   ├── verify_tools.py   # Test concerto-cli wrapper
│   ├── test_models.py    # Test data models
│   └── demo_workflow.py  # Full workflow demo
│
├── docs/                 # Documentation
│   ├── agent_personas.md # Agent specifications
│   └── concerto_error_modes.md  # Error handling
│
├── examples/             # Example .cto files
├── tests/                # Test suite
├── output/               # Generated .cto files
│
├── package.json          # Node.js deps (concerto-cli)
├── pyproject.toml        # Python project config
└── README.md
```


## Development

```bash
# Run tests
pytest

# Run linter
ruff check src/

# Type checking
mypy src/
```

## MVP Scope

### Included

- Natural language input via CLI and Web UI
- CTO model generation from natural language
- Validation via `concerto-cli`
- Retry on validation failure
- REST API for frontend integration
- Save output to file

### Explicitly Excluded (for MVP)

- Multiple LLM provider switching
- TemplateMark / logic generation
- Modifying Accord Project repos
- Complex multi-agent hierarchies

## Contributing

This is a GSoC 2026 project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Accord Project](https://accordproject.org/) - For the Concerto modeling language
- [Groq](https://groq.com/) - For fast, free LLM inference
- GSoC Mentors: Sanket Shevkar, Niall Roche
