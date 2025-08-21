#!/bin/bash
# deepgem installer script
# Quick setup for deepgem: DeepSeek ↔ Gemini CLI agent

set -e

echo ""
echo "██████╗ ███████╗███████╗██████╗     ██████╗ ███████╗███╗   ███╗"
echo "██╔══██╗██╔════╝██╔════╝██╔══██╗   ██╔════╝ ██╔════╝████╗ ████║"
echo "██║  ██║█████╗  █████╗  ██████╔╝   ██║  ███╗█████╗  ██╔████╔██║"
echo "██║  ██║██╔══╝  ██╔══╝  ██╔═══╝    ██║   ██║██╔══╝  ██║╚██╔╝██║"
echo "██████╔╝███████╗███████╗██║        ╚██████╔╝███████╗██║ ╚═╝ ██║"
echo "╚═════╝ ╚══════╝╚══════╝╚═╝         ╚═════╝ ╚══════╝╚═╝     ╚═╝"
echo ""
echo "                    deepgem installer"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
    else
        echo -e "${RED}✗${NC} Python 3.10+ required (found $PYTHON_VERSION)"
        echo "Please upgrade Python: https://www.python.org/downloads/"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo "Please install Python 3.10+: https://www.python.org/downloads/"
    exit 1
fi

# Check if pipx is installed, otherwise use pip
if command -v pipx &> /dev/null; then
    INSTALLER="pipx"
    echo -e "${GREEN}✓${NC} pipx found (recommended)"
else
    INSTALLER="pip"
    echo -e "${YELLOW}!${NC} pipx not found, using pip instead"
    echo "   Consider installing pipx for isolated environments:"
    echo "   python3 -m pip install --user pipx"
fi

# Install deepgem
echo ""
echo "Installing deepgem..."
if [ "$INSTALLER" = "pipx" ]; then
    if pipx list | grep -q "deepgem"; then
        echo "Upgrading existing deepgem installation..."
        pipx upgrade deepgem || pipx install --force deepgem
    else
        pipx install deepgem
    fi
else
    python3 -m pip install --upgrade deepgem
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} deepgem installed successfully"
else
    echo -e "${RED}✗${NC} Failed to install deepgem"
    exit 1
fi

# Check for npm (needed for Gemini CLI)
echo ""
echo "Checking for Node.js/npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm $NPM_VERSION found"
    
    # Check if Gemini CLI is installed
    if command -v gemini &> /dev/null; then
        echo -e "${GREEN}✓${NC} Gemini CLI already installed"
    else
        echo "Installing Gemini CLI..."
        npm install -g @google/gemini-cli
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Gemini CLI installed"
        else
            echo -e "${YELLOW}!${NC} Failed to install Gemini CLI globally"
            echo "   You may need to run: sudo npm install -g @google/gemini-cli"
            echo "   Or use a Node version manager like nvm"
        fi
    fi
else
    echo -e "${YELLOW}!${NC} npm not found - Gemini CLI features will be unavailable"
    echo "   Install Node.js from: https://nodejs.org/"
    echo "   Then run: npm install -g @google/gemini-cli"
fi

# Setup API keys
echo ""
echo "Setting up API keys..."

# Check for existing keys
DEEPSEEK_SET=false
GEMINI_SET=false

if [ ! -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} DEEPSEEK_API_KEY already set"
    DEEPSEEK_SET=true
fi

if [ ! -z "$GEMINI_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} GEMINI_API_KEY already set"
    GEMINI_SET=true
fi

# Offer to set up keys
if [ "$DEEPSEEK_SET" = false ] || [ "$GEMINI_SET" = false ]; then
    echo ""
    echo "Would you like to set up API keys now? (y/n)"
    read -r SETUP_KEYS
    
    if [ "$SETUP_KEYS" = "y" ] || [ "$SETUP_KEYS" = "Y" ]; then
        SHELL_RC=""
        
        # Detect shell configuration file
        if [ -n "$BASH_VERSION" ]; then
            if [ -f "$HOME/.bashrc" ]; then
                SHELL_RC="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                SHELL_RC="$HOME/.bash_profile"
            fi
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        fi
        
        if [ "$DEEPSEEK_SET" = false ]; then
            echo ""
            echo "Enter your DeepSeek API key (get one at https://platform.deepseek.com/):"
            read -r DEEPSEEK_KEY
            if [ ! -z "$DEEPSEEK_KEY" ]; then
                export DEEPSEEK_API_KEY="$DEEPSEEK_KEY"
                if [ ! -z "$SHELL_RC" ]; then
                    echo "export DEEPSEEK_API_KEY=\"$DEEPSEEK_KEY\"" >> "$SHELL_RC"
                    echo -e "${GREEN}✓${NC} DEEPSEEK_API_KEY saved to $SHELL_RC"
                fi
            fi
        fi
        
        if [ "$GEMINI_SET" = false ]; then
            echo ""
            echo "Enter your Gemini API key (optional, or use OAuth with 'gemini' command):"
            read -r GEMINI_KEY
            if [ ! -z "$GEMINI_KEY" ]; then
                export GEMINI_API_KEY="$GEMINI_KEY"
                if [ ! -z "$SHELL_RC" ]; then
                    echo "export GEMINI_API_KEY=\"$GEMINI_KEY\"" >> "$SHELL_RC"
                    echo -e "${GREEN}✓${NC} GEMINI_API_KEY saved to $SHELL_RC"
                fi
            fi
        fi
        
        if [ ! -z "$SHELL_RC" ]; then
            echo ""
            echo "API keys have been added to $SHELL_RC"
            echo "Run this to load them in your current session:"
            echo -e "${YELLOW}source $SHELL_RC${NC}"
        fi
    fi
fi

# Run doctor command
echo ""
echo "Running setup verification..."
echo "────────────────────────────────────────"
deepgem doctor

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Quick start:"
echo "  deepgem chat \"Hello, what can you do?\""
echo "  deepgem ask \"Write a Python script that counts files\""
echo "  deepgem doctor  # Check your setup anytime"
echo ""
echo "Documentation: https://github.com/eekosystems/deepgem"
echo "════════════════════════════════════════════════════════════════"