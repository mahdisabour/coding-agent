# Quick Start Guide

Get started with Coding Agent's **Interactive Multi-Turn Mode** in 5 minutes!

## 🎯 What is Interactive Mode?

The Coding Agent now works like a **conversational pair programmer**:
- 💬 **Chat naturally** about your coding tasks
- 🧠 **Agent remembers** everything from the conversation
- 🔄 **Build iteratively** - no need to plan everything upfront
- 💾 **Save & resume** your work anytime
- 💰 **Track costs** per turn and across the whole session

**This is the recommended way to use the agent!**

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key (or compatible provider)

## Installation

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd coding_agent

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package with dependencies
uv pip install -e .

# Install development dependencies (optional)
uv pip install -e ".[dev]"
```

### 3. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor
```

**Required in `.env`:**
```bash
CODING_AGENT_OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Optional settings (with defaults):**
```bash
# Model settings
CODING_AGENT_MODEL_NAME=gpt-4-turbo-preview
CODING_AGENT_TEMPERATURE=0.1

# Memory settings (for interactive mode)
CODING_AGENT_MAX_TURNS_IN_CONTEXT=10      # How many turns to remember
CODING_AGENT_MAX_TOKENS_PER_TURN=8000     # Token limit per turn
CODING_AGENT_AUTO_SAVE_SESSION=true       # Auto-save after each turn

# Agent behavior
CODING_AGENT_MAX_ITERATIONS=10            # Max retries per turn
CODING_AGENT_ENABLE_REFLECTION=true       # Learn from failures
```

## 🚀 Your First Interactive Session

### Start the Agent

```bash
# Navigate to your project
cd /path/to/your/project

# Start interactive mode
coding-agent chat
```

You'll see a welcome screen:

```
┌──────────────────────────────────────────────────────┐
│ Coding Agent - Interactive Mode                     │
│                                                      │
│ Project: /Users/you/my-project                      │
│ Type your coding tasks or questions. Use /help.    │
└──────────────────────────────────────────────────────┘
```

### Have a Conversation

Here's a real example of building a feature step-by-step:

```
Project: ./my-app | Turns: 0 | Context: 0 messages

You: Create a REST API endpoint for user registration

━━━━━━━━━━━━━━━ Processing Turn 1 ━━━━━━━━━━━━━━━━━━

Agent:
┌──────────────────────────────────────────────────────┐
│ I've created a user registration endpoint:          │
│                                                      │
│ - POST /api/users/register                          │
│ - Located in routes/users.py                        │
│ - Accepts: username, email, password                │
│ - Returns: user_id and token                        │
│ - Basic validation included                         │
└──────────────────────────────────────────────────────┘

┌─────────────── Turn 1 Summary ──────────────────────┐
│ Status        │ ✓ Success                           │
│ Iterations    │ 1                                   │
│ Errors        │ 0                                   │
│ Input Tokens  │ 1,234                               │
│ Output Tokens │ 567                                 │
│ Cost          │ $0.0234                             │
└──────────────────────────────────────────────────────┘

Project: ./my-app | Turns: 1 | Context: 2 messages

You: Add email validation and password strength checking

━━━━━━━━━━━━━━━ Processing Turn 2 ━━━━━━━━━━━━━━━━━━

Agent:
┌──────────────────────────────────────────────────────┐
│ Updated the registration endpoint with:             │
│                                                      │
│ - Email format validation (regex)                   │
│ - Password strength requirements:                   │
│   * Minimum 8 characters                            │
│   * Must include uppercase, lowercase, number       │
│ - Clear error messages for validation failures      │
└──────────────────────────────────────────────────────┘

┌─────────────── Turn 2 Summary ──────────────────────┐
│ Status        │ ✓ Success                           │
│ Iterations    │ 1                                   │
│ Errors        │ 0                                   │
│ Input Tokens  │ 2,145                               │
│ Output Tokens │ 891                                 │
│ Cost          │ $0.0488                             │
└──────────────────────────────────────────────────────┘

You: Now add a check for duplicate emails

━━━━━━━━━━━━━━━ Processing Turn 3 ━━━━━━━━━━━━━━━━━━

Agent:
┌──────────────────────────────────────────────────────┐
│ Added duplicate email checking:                     │
│                                                      │
│ - Query database before registration                │
│ - Return 409 Conflict if email exists               │
│ - Appropriate error message                         │
└──────────────────────────────────────────────────────┘

┌─────────────── Turn 3 Summary ──────────────────────┐
│ Status        │ ✓ Success                           │
│ Cost          │ $0.0391                             │
└──────────────────────────────────────────────────────┘

You: /stats

┌────────────── Session Statistics ──────────────────┐
│ Total Turns      │ 3                               │
│ Successful       │ 3                               │
│ Failed           │ 0                               │
│ Success Rate     │ 100.0%                          │
│                  │                                 │
│ Total Input      │ 5,523                           │
│ Total Output     │ 2,349                           │
│ Total Tokens     │ 7,872                           │
│                  │                                 │
│ Total Cost       │ $0.1113                         │
│ Avg Cost/Turn    │ $0.0371                         │
└──────────────────────────────────────────────────────┘

You: /save user_registration_feature.json

Session saved to: user_registration_feature.json

You: /exit
```

**Notice how:**
- Each turn builds on previous context
- The agent remembers the endpoint from turn 1
- You see cost tracking after each turn
- Cumulative statistics show total session cost

## 📋 Interactive Commands

Within a chat session, you have these commands:

| Command | What it does |
|---------|-------------|
| `/help` | Show all available commands |
| `/stats` | Display session statistics (turns, tokens, costs) |
| `/context` | Show summary of conversation context |
| `/save [filename]` | Save session to file (optional filename) |
| `/load <filename>` | Load a previous session |
| `/clear` | Clear working context (keeps history) |
| `/reset` | Reset entire session (asks confirmation) |
| `/exit` | Exit the session (also: `/quit`, `/q`) |

Just type normally to send a task or question to the agent!

## 💡 Common Workflows

### Workflow 1: Building a Feature

```bash
coding-agent chat --project-root ./my-app

You: Create a blog post model
You: Add categories to the blog post
You: Create an API to list posts by category
You: Add pagination to the list endpoint
You: /save blog_api_v1.json
You: /exit
```

### Workflow 2: Debugging

```bash
coding-agent chat --project-root ./my-app

You: The login endpoint is returning 500 errors
You: Check the database connection in auth.py
You: Fix the connection pool configuration
You: Add error logging for better debugging
You: /stats  # Check token usage
You: /exit
```

### Workflow 3: Resume Previous Work

```bash
# Continue from where you left off
coding-agent chat --load-session blog_api_v1.json

You: Add full-text search to the blog posts
You: Optimize the search query for performance
You: /save blog_api_v2.json
You: /exit
```

### Workflow 4: Exploration and Learning

```bash
coding-agent chat --project-root ./new-codebase

You: What does the authentication system use?
You: Show me how the JWT tokens are generated
You: Are there any security issues with the current implementation?
You: /context  # See what we've discussed
You: /exit
```

## 🎓 Tips for Effective Sessions

### 1. Start Broad, Refine Later

✅ **Good:**
```
You: Create a user authentication system
You: Add password hashing with bcrypt
You: Add JWT token generation
```

❌ **Less Effective:**
```
You: Create a complete user authentication system with password hashing, JWT tokens, refresh tokens, email verification, and 2FA
```

### 2. Check Stats Regularly

Monitor your costs:
```
You: /stats  # After 3-5 turns
```

### 3. Save Important Milestones

```
You: /save feature_complete.json      # After completing a feature
You: /save before_refactor.json       # Before major changes
You: /save debugging_session.json     # When solving complex issues
```

### 4. Use Context Command

See what the agent remembers:
```
You: /context
```

Output shows:
- Total turns in session
- Recent conversation topics
- Files that were accessed
- Current working assumptions

## 🔧 Single-Turn Mode (Still Available)

For quick, one-off tasks where context isn't needed:

```bash
# Fix a typo
coding-agent solve "Fix typo in README.md line 42" --project-root .

# Simple file creation
coding-agent solve "Create .gitignore for Python project" --project-root .

# Quick refactor
coding-agent solve "Rename function getUserData to fetchUserData" --project-root .
```

**When to use single-turn:**
- Simple one-line fixes
- Creating single files
- Quick refactors
- Automated scripts/CI pipelines

**When to use interactive:**
- Building features (anything multi-step)
- Debugging issues
- Learning/exploring codebases
- Iterative development

## 📊 Understanding Turn Summaries

After each turn, you see:

```
┌─────────────── Turn N Summary ──────────────────────┐
│ Status        │ ✓ Success / ✗ Failed                │
│ Iterations    │ Number of plan-execute cycles       │
│ Errors        │ Count of errors encountered         │
│ Input Tokens  │ Tokens sent to model (your + agent) │
│ Output Tokens │ Tokens from model response          │
│ Cost          │ Estimated cost for this turn        │
└──────────────────────────────────────────────────────┘
```

**What they mean:**
- **Iterations > 1**: Task required retries (agent learned from failures)
- **Errors > 0**: Check the details - agent may have recovered
- **High tokens**: Complex task or lots of context

## 📈 Session Statistics

Use `/stats` to see cumulative data:

```
Session Statistics:
├─ Total Turns: 5
├─ Successful: 4 (80%)
├─ Failed: 1 (20%)
├─ Total Tokens: 12,543
├─ Total Cost: $0.1842
└─ Avg Cost/Turn: $0.0368
```

**Monitor costs:**
- Set a budget before starting
- Use `/stats` every few turns
- Save expensive sessions for later review

## 🧪 Testing the Agent

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=coding_agent --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v
```

### Quick Evaluation

Test on SWE-bench Lite subset:

```bash
coding-agent evaluate --limit 5 --output quick_eval.json
```

## 🔌 MCP Server (Advanced)

The agent's tools are exposed via MCP (Model Context Protocol):

```bash
# Start MCP server
mcp-server
```

Available tools:
- `read_file`, `create_file`, `update_file`
- `list_directory`, `search_files`
- `run_command`
- `search_code`, `search_symbols`

## 🗂️ Project Structure

```
coding_agent/
├── src/coding_agent/       # Main package
│   ├── agent/              # LangGraph workflow + session management
│   ├── tools/              # Agent tools (file ops, search, shell)
│   ├── mcp/                # MCP server
│   ├── evaluation/         # SWE-bench benchmarking
│   ├── cli/                # CLI + interactive interface
│   ├── config/             # Settings management
│   └── utils/              # Logging, memory, usage tracking
├── tests/                  # Test suite
├── configs/                # Configuration files
└── *.md                    # Documentation
```

## 🐛 Troubleshooting

### API Key Not Found

```bash
# Check if .env exists
cat .env | grep OPENAI_API_KEY

# If not, add it:
echo "CODING_AGENT_OPENAI_API_KEY=sk-your-key" >> .env
```

### Import Errors

```bash
# Reinstall the package
uv pip install -e .
```

### Permission Errors

```bash
# Ensure write permissions
chmod -R u+w /path/to/project
```

### High Token Usage

```bash
# Reduce context window
export CODING_AGENT_MAX_TURNS_IN_CONTEXT=5

# Or clear context during session
You: /clear
```

### Session File Too Large

Sessions grow with conversation:
```bash
# Archive old sessions
mkdir archived_sessions
mv session_*.json archived_sessions/
```

## 📚 Next Steps

### Learn More
1. Read [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) - Complete interactive guide
2. Read [README.md](README.md) - Full documentation
3. Read [MULTI_TURN_UPDATE.md](MULTI_TURN_UPDATE.md) - What's new

### Try Examples
1. Build a simple API endpoint
2. Debug an existing issue
3. Refactor a module
4. Explore an unfamiliar codebase

### Customize
1. Add new tools to `src/coding_agent/tools/`
2. Adjust configuration in `.env`
3. Create custom prompts in `src/coding_agent/agent/prompts.py`

### Benchmark
1. Run evaluations: `coding-agent evaluate --limit 10`
2. Compare different configurations
3. Track performance over time

## 🎬 Complete Example: Building a TODO API

Here's a complete session building a TODO API from scratch:

```bash
$ coding-agent chat --project-root ./todo-api

┌──────────────────────────────────────────────────────┐
│ Coding Agent - Interactive Mode                     │
│ Project: /Users/you/todo-api                        │
└──────────────────────────────────────────────────────┘

You: Create a Todo model with title, description, and completed status

Agent: Created models/todo.py with Todo class...
✓ Success | $0.02

You: Add created_at and updated_at timestamps

Agent: Updated Todo model with timestamps...
✓ Success | $0.03

You: Create CRUD API endpoints for todos

Agent: Created routes/todos.py with:
- GET /todos (list all)
- POST /todos (create)
- GET /todos/:id (get one)
- PUT /todos/:id (update)
- DELETE /todos/:id (delete)
✓ Success | $0.05

You: Add filtering by completed status to the list endpoint

Agent: Updated GET /todos with ?completed=true/false filter...
✓ Success | $0.03

You: Write tests for all the endpoints

Agent: Created tests/test_todos.py with comprehensive tests...
✓ Success | $0.06

You: /stats

Session Statistics:
Total Turns: 5
Success Rate: 100%
Total Cost: $0.19

You: /save todo_api_complete.json
Session saved!

You: /exit

┌──────────────────────────────────────────────────────┐
│ Session Ended                                        │
│ Built complete TODO API in 5 conversational turns   │
│ Total Cost: $0.19                                    │
└──────────────────────────────────────────────────────┘
```

## 🚀 Ready to Start?

```bash
# Navigate to your project
cd /path/to/your/project

# Start chatting with your AI pair programmer
coding-agent chat
```

**Happy coding!** 🎉

---

## Quick Reference Card

```bash
# Start interactive session
coding-agent chat [--project-root PATH] [--load-session FILE]

# In-session commands
/help      # Show commands
/stats     # Session statistics
/context   # Show context
/save      # Save session
/load      # Load session
/clear     # Clear context
/reset     # Reset all
/exit      # Quit

# Single-turn mode
coding-agent solve "TASK" --project-root PATH

# Evaluation
coding-agent evaluate --limit N

# MCP server
mcp-server

# Tests
pytest tests/
```

**Environment:**
```bash
CODING_AGENT_OPENAI_API_KEY=sk-...          # Required
CODING_AGENT_MAX_TURNS_IN_CONTEXT=10        # Context window
CODING_AGENT_MAX_ITERATIONS=10              # Retries per turn
CODING_AGENT_ENABLE_REFLECTION=true         # Learn from failures
```
