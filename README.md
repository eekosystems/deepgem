# deepgem

**deepgem** is a terminal agent that routes prompts between:
- **DeepSeek V3.1** via its OpenAI-compatible API (fast chat or deliberate reasoning), and
- the official **Gemini CLI** for agentic tool-use (shell/file ops, web fetch/search, MCP).

It shows a fun ASCII banner: “deepgem by eeko systems”.

## Install

### Quick Install (Recommended)

```bash
# One-line installer (Linux/macOS)
curl -sSL https://raw.githubusercontent.com/eekosystems/deepgem/main/install.sh | bash

# Or install from PyPI
pip install deepgem

# Then verify your setup
deepgem doctor
```

### Manual Install

Prerequisites:
- Python 3.10+
- Node.js/npm (for Gemini CLI)
- DeepSeek API key

```bash
# Install deepgem
pip install deepgem
# or with pipx (recommended for isolation)
pipx install deepgem

# Install Gemini CLI
npm install -g @google/gemini-cli
# or
brew install gemini-cli

# Set up API keys
export DEEPSEEK_API_KEY="sk-..."
export GEMINI_API_KEY="..."  # optional, can use OAuth instead

# Verify installation
deepgem doctor
```

### From Source

```bash
git clone https://github.com/eekosystems/deepgem
cd deepgem
pipx install .
# or
pip install .
```

## Quickstart

```bash
# DeepSeek chat
deepgem chat "Summarize the history of TCPA in 7 bullets."

# DeepSeek reasoner (heavier deliberation)
deepgem chat -m deepseek-reasoner "Design a minimal CRM schema; reason step-by-step."

# Use Gemini CLI (non-interactive)
deepgem gem -p "List files changed since yesterday and draft a PR summary." --include-directories .

# Smart router (chooses engine for you)
deepgem ask "Refactor this repo to add unit tests and a GitHub Actions workflow."
```

## Environment

```bash
export DEEPSEEK_API_KEY="sk-..."     # required

# Gemini CLI auth (choose one):
#   gemini   # OAuth flow
#   export GEMINI_API_KEY="..." && gemini

# Optional:
# export DEEPGEM_NO_BANNER=1                  # hide ASCII banner
# export DEEPGEM_DEFAULT_GEMINI_MODEL="gemini-2.5-pro"
# export GEMINI_BIN="gemini"                  # custom path to gemini
```

## Notes
- DeepSeek API is OpenAI-compatible; model IDs: `deepseek-chat` (non-thinking) and `deepseek-reasoner` (thinking).
- Streaming is enabled by default for DeepSeek (use `--no-stream` to disable).
- The router sends “code/tooling” prompts to Gemini CLI, long or “think step by step” prompts to DeepSeek Reasoner, and everything else to DeepSeek Chat.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest -q
```

## Docker (optional)
```bash
docker build -t deepgem .
docker run --rm -it   -e DEEPSEEK_API_KEY   -e GEMINI_API_KEY   deepgem deepgem chat "Hello from container"
```

## License
MIT
