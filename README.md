
**deepgem** is a terminal agent that routes prompts between:
- **DeepSeek V3.1** via its OpenAI-compatible API (fast chat or deliberate reasoning), and
- the official **Gemini CLI** for agentic tool-use (shell/file ops, web fetch/search, MCP).

It shows a fun ASCII banner: “deepgem by eeko systems”.

## Install

### Super Quick Install (Windows)

```bash
# Clone the repo
git clone https://github.com/eekosystems/deepgem
cd deepgem

# Run the one-click installer
quickinstall.bat

# IMPORTANT: Close and reopen your terminal after install!

# Set up authentication (one time only):
# For DeepSeek (required):
set DEEPSEEK_API_KEY=sk-your-key-here

# For Gemini (choose one):
gemini auth              # OAuth login (recommended)
# OR
set GEMINI_API_KEY=your-gemini-key

# Then you can use:
deepgem chat "hello"     # Talk to DeepSeek
dg "analyze this code"   # Use Gemini for code analysis
```

**Note:** The installer automatically:
- Installs deepgem
- Creates `deepgem` and `dg` commands  
- Adds them to your PATH
- Installs Gemini CLI (if npm is available)
- Fixes Windows-specific PATH and encoding issues

### Quick Install (Recommended)

```bash
# Install from PyPI (when published)
pip install deepgem

# Run interactive setup wizard
deepgem setup

# Or use one-line installer (Linux/macOS)
curl -sSL https://raw.githubusercontent.com/eekosystems/deepgem/main/install.sh | bash
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

### Super Simple Code Helper (dg command)
```bash
# Navigate to any project folder
cd your-project

# Use the super simple 'dg' command:
dg "what does this code do?"
dg "fix the bugs"
dg "add error handling"
dg "write unit tests"
dg "refactor this code"
```

### Regular Commands
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

## Setup Issues & Fixes

### Windows Unicode/Emoji Display Issues
- **Fixed:** UTF-8 encoding is automatically set for Windows consoles
- If you see garbled characters, the fix is already included

### NPM Not Found on Windows  
- **Fixed:** Automatically detects `npm.cmd` on Windows
- If Node.js is installed but npm isn't found, run: `winget install OpenJS.NodeJS`

### PATH Issues (Windows)
- **Fixed:** `quickinstall.bat` now automatically adds commands to PATH
- If `dg` or `gemini` commands aren't found after install:
  ```bash
  # Add npm and user directory to PATH
  setx PATH "%PATH%;C:\Users\%USERNAME%\AppData\Roaming\npm;C:\Users\%USERNAME%"
  # Then restart your terminal
  ```

### The 'dg' Command
- Automatically created by `quickinstall.bat` 
- Adds both `deepgem` and `dg` commands to your PATH
- **IMPORTANT:** Always restart terminal after running `quickinstall.bat`
- Makes coding assistance super simple - just `dg "your request"`

## Important: Authentication Required

### DeepSeek (Required)
Get your API key from https://platform.deepseek.com/
```bash
set DEEPSEEK_API_KEY=sk-your-key-here
```

### Gemini (Required for `dg` command)
Option 1: OAuth (Recommended - opens browser for Google login)
```bash
gemini auth
```

Option 2: API Key
```bash
set GEMINI_API_KEY=your-key-here
```
Get key from: https://makersuite.google.com/app/apikey

Without authentication, you'll see error messages when trying to use the commands.

## Notes
- DeepSeek API is OpenAI-compatible; model IDs: `deepseek-chat` (non-thinking) and `deepseek-reasoner` (thinking).
- Streaming is enabled by default for DeepSeek (use `--no-stream` to disable).
- The router sends "code/tooling" prompts to Gemini CLI, long or "think step by step" prompts to DeepSeek Reasoner, and everything else to DeepSeek Chat.

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
