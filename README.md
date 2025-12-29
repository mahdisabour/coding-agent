# Coding Agent

A professional CLI-based coding agent powered by LangGraph ReAct loop, featuring **interactive multi-turn conversations** with memory and comprehensive usage tracking.

## Quick Start

```bash
# Start an interactive session (recommended)
coding-agent chat --project-root ./your-project

# Or solve a single task
coding-agent solve "Add error handling to auth.py" --project-root ./your-project
```

## Features

- **🎯 Interactive Multi-Turn Mode**: Natural conversations with full context memory
- **🧠 Conversation Memory**: Agent remembers previous interactions and builds on context
- **💾 Session Management**: Save and resume work at any time
- **🤖 ReAct Loop**: Reasoning and acting cycle for autonomous problem-solving
- **🛠️ Rich Tool Set**: File operations, code search, symbol lookup, and shell command execution
- **💰 Session-Level Token Tracking**: Monitor total token usage and costs after completion
- **🔗 OpenAI-Compatible**: Works with OpenAI API and compatible providers
- **✨ Professional CLI**: Rich terminal interface with progress tracking

## Architecture

The agent uses a **ReAct (Reasoning + Acting) loop** powered by LangChain's `create_agent`:

1. **Reason**: Agent analyzes the task and decides which tool to use
2. **Act**: Execute the chosen tool with appropriate parameters
3. **Observe**: Process tool results and update understanding
4. **Repeat**: Continue until task is complete

The agent autonomously selects and executes tools based on the task requirements.

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

Create a `.env` file in the project root:

```bash
# Required
CODING_AGENT_OPENAI_API_KEY=your-api-key-here

# Optional (defaults shown)
CODING_AGENT_MODEL_NAME=gpt-4-turbo-preview
CODING_AGENT_TEMPERATURE=0.1
CODING_AGENT_MAX_TOKENS=4096
CODING_AGENT_LOG_LEVEL=INFO
CODING_AGENT_TRACK_USAGE=true

# Cost estimation (USD per 1M tokens)
CODING_AGENT_COST_PER_MILLION_INPUT_TOKENS=10.0
CODING_AGENT_COST_PER_MILLION_OUTPUT_TOKENS=30.0
```

## Usage

### Interactive Chat (Recommended)

```bash
# Start interactive session
coding-agent chat --project-root /path/to/project

# Load previous session
coding-agent chat --load-session my_session.json
```

**Available commands:**
- `/help` - Show commands
- `/stats` - Session statistics
- `/context` - Current context info
- `/save [file]` - Save session
- `/load <file>` - Load session
- `/clear` - Clear working context
- `/reset` - Reset entire session
- `/exit` - Exit session

### Single Task Mode

```bash
# Solve a specific task
coding-agent solve "Add error handling to auth.py" --project-root .

# With verbose logging
coding-agent solve "Fix bug in parser" --verbose

# Disable token tracking
coding-agent solve "Refactor code" --no-tracking
```

## Project Structure


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

The agent tracks token usage and estimates costs at the **session level**:

**In Interactive Mode** (`/stats` command):
```
Session Statistics
────────────────────────────────────────
Total Turns             5
Total Input Tokens      12,543
Total Output Tokens     3,892
Total Tokens            16,435
Total Cost              $0.2421
Avg Cost/Turn           $0.0484
```

**In Single Task Mode** (shown after completion):
```
============================================================
Token Usage
============================================================
Input Tokens:  4,231
Output Tokens: 892
Total Tokens:  5,123
Estimated Cost: $0.0691
============================================================
```


## API Compatibility

Works with OpenAI-compatible APIs:

```bash
# Azure OpenAI
CODING_AGENT_OPENAI_API_BASE=https://your-resource.openai.azure.com/
CODING_AGENT_MODEL_NAME=your-deployment-name

# Other providers (Together, Anyscale, etc.)
CODING_AGENT_OPENAI_API_BASE=https://api.together.xyz/v1
CODING_AGENT_MODEL_NAME=meta-llama/Llama-3-70b-chat-hf
```

