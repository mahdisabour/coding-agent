# Coding Agent

A professional CLI-based coding agent powered by LangGraph, featuring **interactive multi-turn conversations**, MCP (Model Context Protocol) server integration, SWE-bench evaluation support, and comprehensive usage tracking.

## Quick Start

```bash
# Start an interactive session (recommended)
coding-agent chat --project-root ./your-project

# Or solve a single task
coding-agent solve "Add error handling to auth.py" --project-root ./your-project
```

## Features

- **🎯 Interactive Multi-Turn Mode**: Have natural conversations with context memory across turns
- **🧠 Conversation Memory**: Agent remembers previous interactions and builds on context
- **💾 Session Management**: Save and resume work at any time
- **📊 Real-Time Cost Tracking**: Monitor token usage and costs per turn and cumulatively
- **🏗️ Modular Agent Architecture**: Built with LangGraph featuring distinct nodes for planning, execution, verification, and reflection
- **🔌 MCP Server Integration**: Tools exposed via Model Context Protocol for standardized access
- **🛠️ Rich Tool Set**: File operations, code search, symbol lookup, and shell command execution
- **📈 SWE-bench Evaluation**: Built-in support for benchmarking on SWE-bench Lite dataset
- **💰 Usage & Cost Tracking**: Detailed token usage and cost estimation per node and overall
- **🔗 OpenAI-Compatible**: Works with OpenAI API and compatible providers
- **✨ Professional CLI**: Rich terminal interface with progress tracking and formatted output

## Two Modes of Operation

### Interactive Mode (Recommended)

Multi-turn conversations with context memory - ideal for complex projects:

```bash
coding-agent chat --project-root ./my-project
```

**Benefits:**
- Context preserved across turns
- Build solutions iteratively
- Track costs across entire session
- Save and resume sessions
- Natural conversation flow

See [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) for detailed guide.

### Single-Turn Mode

One-shot task execution - ideal for quick fixes:

```bash
coding-agent solve "Fix typo in README" --project-root .
```

## Architecture

The agent follows a structured workflow:

1. **Plan**: Analyzes the task and creates an execution strategy
2. **Execute**: Uses available tools to implement the plan
3. **Verify**: Validates the solution meets requirements
4. **Reflect**: (Optional) Analyzes failures and refines approach for next iteration

### Agent Nodes

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌─────────┐
│  Plan   │  - Analyze task
└────┬────┘  - Create strategy
     │
     ▼
┌─────────┐
│ Execute │  - Use tools
└────┬────┘  - Implement solution
     │
     ▼
┌─────────┐
│ Verify  │  - Check correctness
└────┬────┘  - Validate quality
     │
     ├─ Pass ──────────────┐
     │                     ▼
     └─ Fail ──▶ ┌──────────┐
                 │ Reflect  │
                 └────┬─────┘
                      │
                      └──▶ Plan (retry)
```

## Installation

### Prerequisites

- Python 3.11 or higher
- uv package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd coding_agent
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and preferences
```

## Configuration

### Environment Variables

Configure the agent via environment variables (`.env` file):

```bash
# Required
CODING_AGENT_OPENAI_API_KEY=your-api-key-here

# Optional (with defaults)
CODING_AGENT_OPENAI_API_BASE=https://api.openai.com/v1
CODING_AGENT_MODEL_NAME=gpt-4-turbo-preview
CODING_AGENT_TEMPERATURE=0.1
CODING_AGENT_MAX_TOKENS=4096
CODING_AGENT_MAX_ITERATIONS=10
CODING_AGENT_ENABLE_REFLECTION=true
CODING_AGENT_LOG_LEVEL=INFO
CODING_AGENT_TRACK_USAGE=true
```

### Configuration File

Alternatively, use a YAML configuration file (`configs/default.yaml`):

```yaml
model:
  name: gpt-4-turbo-preview
  temperature: 0.1
  max_tokens: 4096

agent:
  max_iterations: 10
  enable_reflection: true

logging:
  level: INFO
```

## Usage

### Interactive Chat (Recommended)

Start an interactive session:

```bash
# Basic usage
coding-agent chat

# With specific project
coding-agent chat --project-root /path/to/project

# Load previous session
coding-agent chat --load-session my_session.json
```

**Within the interactive session:**

```bash
You: Create a REST API for user management

Agent: [Creates API structure...]

You: Add authentication with JWT

Agent: [Adds JWT auth building on previous context...]

You: /stats  # Check token usage and costs

You: /save api_session.json  # Save your progress

You: /exit
```

**Available commands in chat:**
- `/help` - Show commands
- `/stats` - Session statistics
- `/context` - Current context info
- `/save [file]` - Save session
- `/load <file>` - Load session
- `/clear` - Clear context
- `/exit` - Exit

### Single-Turn Task (Quick Fixes)

Run the agent on a specific task:

```bash
coding-agent solve "Add a function to calculate fibonacci numbers" --project-root /path/to/project
```

With verbose output:

```bash
coding-agent solve "Fix the bug in auth.py" --project-root ./my-app --verbose
```

Disable usage tracking:

```bash
coding-agent solve "Refactor database queries" --no-tracking
```

### Run Evaluations

Evaluate on SWE-bench Lite:

```bash
coding-agent evaluate --dataset "SWE-bench/SWE-bench_Lite" --limit 10
```

Full evaluation with custom output:

```bash
coding-agent evaluate --split test --output results/eval_run1.json
```

### MCP Server

Start the MCP server to expose tools:

```bash
mcp-server
```

The server exposes the following tools:
- `read_file`: Read file contents
- `create_file`: Create new files
- `update_file`: Update existing files
- `list_directory`: List directory contents
- `search_files`: Find files by pattern
- `run_command`: Execute shell commands
- `search_code`: Search code by pattern
- `search_symbols`: Find function/class definitions

## Project Structure

```
coding_agent/
├── src/
│   ├── coding_agent/
│   │   ├── agent/              # LangGraph workflow
│   │   │   ├── graph.py        # Workflow definition
│   │   │   ├── nodes.py        # Agent nodes
│   │   │   ├── state.py        # State management
│   │   │   └── prompts.py      # System prompts
│   │   ├── tools/              # Agent tools
│   │   │   ├── file_ops.py     # File operations
│   │   │   ├── shell.py        # Shell commands
│   │   │   └── search.py       # Code search
│   │   ├── mcp/                # MCP server
│   │   │   └── server.py       # Server implementation
│   │   ├── evaluation/         # Benchmarking
│   │   │   ├── runner.py       # Evaluation runner
│   │   │   └── metrics.py      # Metrics calculation
│   │   ├── cli/                # CLI interface
│   │   │   └── main.py         # Command-line interface
│   │   ├── config/             # Configuration
│   │   │   └── settings.py     # Settings management
│   │   └── utils/              # Utilities
│   │       ├── logging.py      # Logging setup
│   │       └── usage_tracker.py # Token tracking
│   └── mcp_server/
│       └── main.py             # MCP server entry
├── tests/                      # Test suite
├── configs/                    # Configuration files
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

## Available Tools

### File Operations

- **read_file**: Read contents of a file
- **create_file**: Create a new file with content
- **update_file**: Update existing file
- **list_directory**: List files and directories
- **search_files**: Find files matching glob pattern

### Code Search

- **search_code**: Search for code using regex patterns
- **search_symbols**: Find function and class definitions

### Execution

- **run_command**: Execute shell commands with timeout

## Usage Tracking

The agent tracks token usage and estimates costs for each operation:

```
==========================================================
USAGE SUMMARY
==========================================================
Total Input Tokens:  12,543
Total Output Tokens: 3,892
Total Tokens:        16,435
Estimated Cost:      $0.2421
Total Operations:    8

Per-Node Breakdown:
----------------------------------------------------------

planner:
  Calls:         2
  Input Tokens:  4,231
  Output Tokens: 892
  Cost:          $0.0691

executor:
  Calls:         2
  Input Tokens:  5,123
  Output Tokens: 1,823
  Cost:          $0.1060

verifier:
  Calls:         2
  Input Tokens:  2,145
  Output Tokens: 891
  Cost:          $0.0488

reflector:
  Calls:         2
  Input Tokens:  1,044
  Output Tokens: 286
  Cost:          $0.0182
==========================================================
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .
```

### Adding New Tools

1. Create tool function in `src/coding_agent/tools/`
2. Add `@tool` decorator
3. Register in `src/coding_agent/mcp/server.py`
4. Update agent nodes to include the tool

Example:

```python
from langchain_core.tools import tool

@tool
def my_custom_tool(arg: str, project_root: str = ".") -> str:
    """Description of what this tool does.

    Args:
        arg: Description of argument
        project_root: Root directory

    Returns:
        Result description
    """
    # Implementation
    return "result"
```

## Extending the Agent

### Custom Nodes

Add new nodes to the workflow by:

1. Creating node function in `src/coding_agent/agent/nodes.py`
2. Adding prompts in `src/coding_agent/agent/prompts.py`
3. Updating graph in `src/coding_agent/agent/graph.py`

### Custom Evaluation Datasets

To evaluate on custom datasets:

1. Ensure dataset is compatible with HuggingFace `datasets`
2. Run: `coding-agent evaluate --dataset "your/dataset" --split test`

## API Compatibility

The agent uses OpenAI-compatible APIs. To use alternative providers:

```bash
# For Azure OpenAI
CODING_AGENT_OPENAI_API_BASE=https://your-resource.openai.azure.com/
CODING_AGENT_MODEL_NAME=your-deployment-name

# For other providers (e.g., Together, Anyscale)
CODING_AGENT_OPENAI_API_BASE=https://api.together.xyz/v1
CODING_AGENT_MODEL_NAME=meta-llama/Llama-3-70b-chat-hf
```

## Troubleshooting

### Common Issues

**API Key Error**
```
Error: OpenAI API key not set
```
Solution: Ensure `CODING_AGENT_OPENAI_API_KEY` is set in `.env`

**Model Not Found**
```
Error: Model xyz not found
```
Solution: Verify model name is correct for your API provider

**Permission Errors**
```
Error: Permission denied
```
Solution: Ensure the agent has write permissions in the project directory

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Citation

If you use this agent in your research, please cite:

```bibtex
@software{coding_agent,
  title = {Coding Agent: Professional CLI-based AI Coding Assistant},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/coding-agent}
}
```

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- MCP protocol support
- Evaluated on [SWE-bench](https://www.swebench.com/)
