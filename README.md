# 🤖 Dummy Accordo Agent

> **GSoC 2026 MVP** - Agentic Workflow for Drafting Accord Project Templates

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## 🎯 Project Vision

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

## 🏗️ Architecture

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

## 🧠 Core Concepts

### Agent Personas

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Requirements Analyst** | Extracts structured intent from natural language | User's description | JSON with namespace, concepts, fields |
| **Model Generator** | Creates valid Concerto syntax | Structured intent | `.cto` file content |

### Tool Integration

This project **consumes** Accord Project tools via CLI - it does not modify them:

- `@accordproject/concerto-cli` - For parsing and validating `.cto` models

## 📦 Installation

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

## 🚀 Usage

```bash
# Run the CLI
accordo generate "I need a model for a vehicle rental agreement with 
renter name, vehicle type, rental period, and daily rate"

# Output: ./output/vehicle_rental.cto
```

## 📁 Project Structure

```
dummy-accordo-agent/
├── src/
│   ├── agents/           # Agent definitions
│   │   ├── requirements_agent.py
│   │   └── model_agent.py
│   │
│   ├── tools/            # CLI wrappers
│   │   └── concerto_tools.py
│   │
│   ├── cli/              # Command-line interface
│   │   └── main.py
│   │
│   └── prompts/          # LLM prompt templates
│
├── examples/             # Example inputs and outputs
├── tests/                # Test suite
├── output/               # Generated .cto files
│
├── package.json          # Node.js deps (concerto-cli)
├── pyproject.toml        # Python project config
└── README.md
```

## 🧪 Development

```bash
# Run tests
pytest

# Run linter
ruff check src/

# Type checking
mypy src/
```

## 📋 MVP Scope

### ✅ Included

- Natural language input via CLI
- CTO model generation
- Validation via `concerto-cli`
- Retry on validation failure
- Save output to file

### ❌ Explicitly Excluded (for MVP)

- Web UI
- Multiple LLM provider switching
- TemplateMark / logic generation
- Modifying Accord Project repos
- Complex multi-agent hierarchies

## 🤝 Contributing

This is a GSoC 2026 project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Accord Project](https://accordproject.org/) - For the Concerto modeling language
- [CrewAI](https://crewai.io/) - For the agentic workflow framework
- [Groq](https://groq.com/) - For fast, free LLM inference
- GSoC Mentors: Sanket Shevkar, Niall Roche
