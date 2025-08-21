\
import os, sys, subprocess
from typing import Optional, List
import typer
from rich.console import Console

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # Also set console code page to UTF-8
    os.system("chcp 65001 >nul 2>&1")

# OpenAI SDK works with DeepSeek via base_url
from openai import OpenAI

# ---------------- Banner ----------------
BANNER = r"""
██████╗ ███████╗███████╗██████╗     ██████╗ ███████╗███╗   ███╗
██╔══██╗██╔════╝██╔════╝██╔══██╗   ██╔════╝ ██╔════╝████╗ ████║
██║  ██║█████╗  █████╗  ██████╔╝   ██║  ███╗█████╗  ██╔████╔██║
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝    ██║   ██║██╔══╝  ██║╚██╔╝██║
██████╔╝███████╗███████╗██║        ╚██████╔╝███████╗██║ ╚═╝ ██║
╚═════╝ ╚══════╝╚══════╝╚═╝         ╚═════╝ ╚══════╝╚═╝     ╚═╝
                      
                      deepgem by eeko systems
"""

def maybe_print_banner(con: Console):
    if os.environ.get("DEEPGEM_NO_BANNER"):
        return
    con.print(BANNER, style="bold")

# ---------------- Typer app ----------------
typer_app = typer.Typer(help="DeepSeek ↔ Gemini CLI agent")

con = Console()

# ---------------- DeepSeek plumbing ----------------
def deepseek_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        con.print("[red]DEEPSEEK_API_KEY not set[/red]")
        raise typer.Exit(code=2)
    # DeepSeek is OpenAI-compatible; V3.1 models:
    #   - deepseek-chat        (non-thinking)
    #   - deepseek-reasoner    (thinking)
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def deepseek_chat(
    prompt: str,
    model: str = "deepseek-chat",
    system: Optional[str] = None,
    stream: bool = True,
) -> int:
    client = deepseek_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        if stream:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and getattr(delta, "content", None):
                    sys.stdout.write(delta.content)
                    sys.stdout.flush()
            sys.stdout.write("\n")
            return 0
        else:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
            )
            con.print(resp.choices[0].message.content)
            return 0
    except Exception as e:
        con.print(f"[red]DeepSeek error:[/red] {e}")
        return 1

# ---------------- Gemini CLI plumbing ----------------
def run_gemini_cli(
    prompt: Optional[str],
    model: Optional[str] = None,
    include_dirs: Optional[str] = None,
    extra: Optional[List[str]] = None,
) -> int:
    # Requires `gemini` in PATH. Non-interactive uses -p/--prompt.
    import shutil
    import platform
    import json
    from pathlib import Path
    
    # Check if Gemini is configured
    if not os.environ.get("GEMINI_API_KEY"):
        settings_path = Path.home() / ".gemini" / "settings.json"
        if not settings_path.exists() or not settings_path.read_text().strip():
            con.print("\n[yellow]Gemini CLI needs authentication.[/yellow]")
            con.print("\nChoose an option:")
            con.print("1. Enter API key (recommended)")
            con.print("2. Skip for now")
            con.print("\nGet your API key at: [cyan]https://makersuite.google.com/app/apikey[/cyan]")
            
            choice = typer.prompt("\nEnter choice (1/2)", default="1")
            
            if choice == "1":
                api_key = typer.prompt("\nPaste your Gemini API key", hide_input=True)
                if api_key:
                    os.environ["GEMINI_API_KEY"] = api_key
                    # Save to .env file for persistence
                    env_file = Path.cwd() / ".env"
                    with open(env_file, "a") as f:
                        f.write(f"\nGEMINI_API_KEY={api_key}\n")
                    con.print("[green]✅ API key saved! Continuing with your request...[/green]\n")
                    # Don't return, continue with the command
                else:
                    con.print("[red]No key entered. Exiting.[/red]")
                    return 1
            else:
                con.print("[yellow]Skipped. Set up authentication later with:[/yellow]")
                con.print("  set GEMINI_API_KEY=your-key")
                con.print("  Then try your command again.")
                return 0
    
    # Try to find gemini more aggressively on Windows
    gemini_cmd = os.environ.get("GEMINI_BIN", "gemini")
    if platform.system() == "Windows" and not shutil.which(gemini_cmd):
        # Check common npm locations on Windows
        possible_paths = [
            os.path.join(os.environ.get("APPDATA", ""), "npm", "gemini.cmd"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming", "npm", "gemini.cmd"),
            "gemini.cmd"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                gemini_cmd = path
                break
    
    cmd: List[str] = [gemini_cmd]
    if prompt:
        cmd += ["-p", prompt]
    if model:
        cmd += ["-m", model]
    elif (default := os.environ.get("DEEPGEM_DEFAULT_GEMINI_MODEL")):
        cmd += ["-m", default]
    if include_dirs:
        cmd += ["--include-directories", include_dirs]
    if extra:
        cmd += extra

    try:
        proc = subprocess.run(cmd, text=True, shell=(platform.system() == "Windows"))
        return proc.returncode
    except (FileNotFoundError, OSError) as e:
        con.print(
            f"[red]Gemini CLI not found or error:[/red] {e}\n"
            "Install with [bold]npm i -g @google/gemini-cli[/bold] or [bold]brew install gemini-cli[/bold]."
        )
        return 127

# ---------------- Simple heuristic router ----------------
CODE_HINTS = (
    "code", "bug", "test", "compile", "stack trace", "build", "function",
    "class", "typescript", "python", "node", "react", "docker", "sql",
    "write a script", "refactor", "fix", "unit test", "terminal", "shell",
)

def pick_engine(prompt: str, force: Optional[str]) -> str:
    if force in {"gemini", "deepseek-chat", "deepseek-reasoner"}:
        return force
    p = prompt.lower()
    if any(k in p for k in CODE_HINTS):
        return "gemini"                 # let Gemini CLI use tools/MCP/web
    if len(p) > 1200 or "think step by step" in p or "chain-of-thought" in p:
        return "deepseek-reasoner"      # heavier reasoning
    return "deepseek-chat"

# ---------------- Root callback (prints banner) ----------------
@typer_app.callback(invoke_without_command=True)
def _root(ctx: typer.Context):
    maybe_print_banner(con)
    if ctx.invoked_subcommand is None:
        con.print("[dim]Use 'deepgem --help' to see commands.[/dim]")

# ---------------- Commands ----------------
@typer_app.command()
def chat(
    prompt: str = typer.Argument(..., help="Your message"),
    model: str = typer.Option("deepseek-chat", "--model", "-m", help="deepseek-chat or deepseek-reasoner"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable token streaming"),
):
    """Talk to DeepSeek (OpenAI-compatible)."""
    raise typer.Exit(code=deepseek_chat(prompt, model, system, stream=not no_stream))

@typer_app.command()
def gem(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Prompt to run non-interactively"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Gemini model, e.g. gemini-2.5-pro"),
    include: Optional[str] = typer.Option(None, "--include-directories", help="Comma-separated dirs to include as context"),
    extra: List[str] = typer.Argument(None, help="Pass-through args to `gemini`"),
):
    """Delegate to Gemini CLI (great for coding, shell tools, MCP, web)."""
    raise typer.Exit(code=run_gemini_cli(prompt, model, include, extra))

@typer_app.command()
def ask(
    prompt: str = typer.Argument(..., help="Your request"),
    force: Optional[str] = typer.Option(None, "--force", "-f", help="'gemini' | 'deepseek-chat' | 'deepseek-reasoner'"),
    system: Optional[str] = typer.Option(None, "--system", "-s"),
    gem_model: Optional[str] = typer.Option(None, "--gem-model", help="Override Gemini model"),
    include: Optional[str] = typer.Option(None, "--include-directories", help="Dirs gemini should scan (comma-separated)"),
):
    """Smart router: Gemini CLI for code/tool tasks; DeepSeek for chat/reasoning."""
    engine = pick_engine(prompt, force)
    con.print(f"[dim]engine:[/dim] {engine}")
    if engine == "gemini":
        raise typer.Exit(code=run_gemini_cli(prompt, gem_model, include, extra=None))
    elif engine == "deepseek-reasoner":
        raise typer.Exit(code=deepseek_chat(prompt, "deepseek-reasoner", system, stream=True))
    else:
        raise typer.Exit(code=deepseek_chat(prompt, "deepseek-chat", system, stream=True))

@typer_app.command()
def setup():
    """Interactive setup wizard for deepgem - installs dependencies and configures API keys."""
    import shutil
    import platform
    import getpass
    from pathlib import Path
    con.print("\n[bold cyan]Welcome to deepgem setup wizard![/bold cyan]")
    con.print("This will help you install dependencies and configure API keys.\n")
    
    # Track what we set up
    setup_complete = []
    
    # 1. Check Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        con.print("✅ Python version: [green]" + platform.python_version() + "[/green]")
    else:
        con.print(f"❌ Python version: [red]{platform.python_version()}[/red] (requires 3.10+)")
        con.print("[red]Please upgrade Python first: https://python.org/downloads[/red]")
        raise typer.Exit(1)
    
    # 2. Check/Install Gemini CLI
    gemini_path = shutil.which(os.environ.get("GEMINI_BIN", "gemini"))
    if not gemini_path:
        con.print("\n❌ Gemini CLI not found")
        
        # Check if npm is available (on Windows, look for npm.cmd)
        npm_path = shutil.which("npm.cmd") if platform.system() == "Windows" else shutil.which("npm")
        if npm_path:
            response = typer.prompt("Would you like to install Gemini CLI now? (Y/n)", default="Y")
            if response.lower() != 'n':
                con.print("[dim]Installing @google/gemini-cli...[/dim]")
                try:
                    npm_cmd = ["npm.cmd" if platform.system() == "Windows" else "npm", "install", "-g", "@google/gemini-cli"]
                    result = subprocess.run(
                        npm_cmd,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        con.print("✅ Gemini CLI installed successfully!")
                        setup_complete.append("Gemini CLI")
                    else:
                        con.print(f"[yellow]⚠️  Failed to install Gemini CLI[/yellow]")
                        if "EACCES" in result.stderr or "permission" in result.stderr.lower():
                            con.print("[yellow]Try running with admin privileges or use:[/yellow]")
                            con.print("[bold]sudo npm install -g @google/gemini-cli[/bold]")
                except FileNotFoundError:
                    con.print("[yellow]npm is not installed. Node.js is required for Gemini CLI.[/yellow]")
                    con.print("\n[bold]To install Node.js:[/bold]")
                    if platform.system() == "Windows":
                        con.print("  Option 1: [cyan]winget install OpenJS.NodeJS[/cyan]")
                        con.print("  Option 2: Download from [cyan]https://nodejs.org/[/cyan]")
                        con.print("\n[yellow]After installing Node.js, restart your terminal and run 'deepgem setup' again.[/yellow]")
                    else:
                        con.print("  macOS:   [cyan]brew install node[/cyan]")
                        con.print("  Linux:   [cyan]sudo apt install nodejs npm[/cyan]")
                except Exception as e:
                    con.print(f"[yellow]Error installing Gemini CLI: {e}[/yellow]")
        else:
            con.print("[yellow]npm not found. Node.js is required for Gemini CLI.[/yellow]")
            con.print("\n[bold]To install Node.js:[/bold]")
            if platform.system() == "Windows":
                con.print("  Option 1: [cyan]winget install OpenJS.NodeJS[/cyan]")
                con.print("  Option 2: Download from [cyan]https://nodejs.org/[/cyan]")
                con.print("\n[yellow]After installing Node.js, restart your terminal and run 'deepgem setup' again.[/yellow]")
            else:
                con.print("  macOS:   [cyan]brew install node[/cyan]")
                con.print("  Linux:   [cyan]sudo apt install nodejs npm[/cyan]")
            con.print("\n[dim]Note: Gemini CLI is optional. DeepSeek features will still work.[/dim]")
    else:
        con.print(f"✅ Gemini CLI: [green]found[/green] at {gemini_path}")
    
    # 3. Setup DeepSeek API key
    con.print("\n[bold]DeepSeek API Configuration[/bold]")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    
    if deepseek_key:
        con.print(f"✅ DeepSeek API key: [green]already configured[/green]")
        response = typer.prompt("Would you like to update it? (y/N)", default="N")
        if response.lower() == 'y':
            deepseek_key = None
    
    if not deepseek_key:
        con.print("\nGet your API key at: [cyan]https://platform.deepseek.com/[/cyan]")
        key_input = getpass.getpass("Enter your DeepSeek API key (sk-...): ")
        
        if key_input:
            if not key_input.startswith("sk-"):
                con.print("[yellow]⚠️  Warning: Key should start with 'sk-'[/yellow]")
            
            # Test the key
            con.print("[dim]Testing API key...[/dim]")
            try:
                test_client = OpenAI(api_key=key_input, base_url="https://api.deepseek.com")
                test_client.models.list()
                con.print("✅ API key validated successfully!")
                
                # Save the key
                save_key_to_env("DEEPSEEK_API_KEY", key_input)
                os.environ["DEEPSEEK_API_KEY"] = key_input
                setup_complete.append("DeepSeek API key")
                
            except Exception as e:
                con.print(f"[red]❌ API key validation failed: {e}[/red]")
                response = typer.prompt("Save anyway? (y/N)", default="N")
                if response.lower() == 'y':
                    save_key_to_env("DEEPSEEK_API_KEY", key_input)
                    os.environ["DEEPSEEK_API_KEY"] = key_input
    
    # 4. Setup Gemini API key (optional)
    con.print("\n[bold]Gemini API Configuration (Optional)[/bold]")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if gemini_key:
        con.print(f"✅ Gemini API key: [green]already configured[/green]")
    else:
        con.print("Gemini CLI can use OAuth or API key authentication.")
        con.print("Get API key at: [cyan]https://makersuite.google.com/app/apikey[/cyan]")
        response = typer.prompt("Would you like to add a Gemini API key? (y/N)", default="N")
        
        if response.lower() == 'y':
            key_input = getpass.getpass("Enter your Gemini API key: ")
            if key_input:
                save_key_to_env("GEMINI_API_KEY", key_input)
                os.environ["GEMINI_API_KEY"] = key_input
                setup_complete.append("Gemini API key")
    
    # 5. Final verification
    con.print("\n" + "═" * 60)
    con.print("[bold cyan]Setup Summary[/bold cyan]\n")
    
    if setup_complete:
        con.print("[green]Successfully configured:[/green]")
        for item in setup_complete:
            con.print(f"  ✅ {item}")
    
    # Run doctor to show final status
    con.print("\n[bold]Running system check...[/bold]")
    con.print("─" * 60)
    return doctor()

def save_key_to_env(key_name: str, key_value: str):
    """Save API key to .env file and appropriate shell config."""
    import platform
    from pathlib import Path
    
    # Save to .env file in current directory
    env_file = Path.cwd() / ".env"
    env_lines = []
    key_found = False
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith(f"{key_name}="):
                    env_lines.append(f"{key_name}={key_value}\n")
                    key_found = True
                else:
                    env_lines.append(line)
    
    if not key_found:
        env_lines.append(f"{key_name}={key_value}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    con.print(f"[green]✅ Saved to .env file[/green]")
    
    # Also save to shell config on Unix-like systems
    if platform.system() != "Windows":
        home = Path.home()
        shell = os.environ.get("SHELL", "")
        
        if "zsh" in shell:
            rc_file = home / ".zshrc"
        elif "bash" in shell:
            rc_file = home / ".bashrc"
        else:
            rc_file = home / ".profile"
        
        # Check if already in file
        if rc_file.exists():
            with open(rc_file, 'r') as f:
                content = f.read()
                if f"export {key_name}=" not in content:
                    with open(rc_file, 'a') as f:
                        f.write(f'\nexport {key_name}="{key_value}"\n')
                    con.print(f"[green]✅ Added to {rc_file.name}[/green]")
    
    # On Windows, optionally set user environment variable
    elif platform.system() == "Windows":
        response = typer.prompt("Save as Windows environment variable? (Y/n)", default="Y")
        if response.lower() != 'n':
            try:
                subprocess.run(
                    ["setx", key_name, key_value],
                    capture_output=True,
                    check=True
                )
                con.print(f"[green]✅ Saved as Windows user environment variable[/green]")
                con.print("[yellow]Note: Restart your terminal for this to take effect[/yellow]")
            except:
                pass

@typer_app.command()
def doctor():
    """Check your deepgem setup and diagnose common issues."""
    import shutil
    import platform
    
    issues = []
    warnings = []
    
    con.print("\n[bold cyan]deepgem doctor[/bold cyan] - Checking your setup...\n")
    
    # Check Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        con.print("✅ Python version: [green]" + platform.python_version() + "[/green]")
    else:
        con.print(f"❌ Python version: [red]{platform.python_version()}[/red] (requires 3.10+)")
        issues.append("Python 3.10+ required. Upgrade Python.")
    
    # Check DeepSeek API key
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        if deepseek_key.startswith("sk-"):
            con.print("✅ DeepSeek API key: [green]configured[/green]")
        else:
            con.print("⚠️  DeepSeek API key: [yellow]found but may be invalid[/yellow]")
            warnings.append("DEEPSEEK_API_KEY should start with 'sk-'")
    else:
        con.print("❌ DeepSeek API key: [red]not found[/red]")
        issues.append("Set DEEPSEEK_API_KEY environment variable")
    
    # Check Gemini CLI
    gemini_path = shutil.which(os.environ.get("GEMINI_BIN", "gemini"))
    if gemini_path:
        con.print(f"✅ Gemini CLI: [green]found[/green] at {gemini_path}")
        
        # Check Gemini API key
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            con.print("✅ Gemini API key: [green]configured[/green]")
        else:
            con.print("⚠️  Gemini API key: [yellow]not found[/yellow]")
            warnings.append("GEMINI_API_KEY not set - Gemini may require OAuth instead")
    else:
        con.print("❌ Gemini CLI: [red]not found[/red]")
        issues.append("Install with: npm install -g @google/gemini-cli")
    
    # Check OpenAI package
    try:
        import openai
        con.print(f"✅ OpenAI SDK: [green]installed[/green] (v{openai.__version__})")
    except ImportError:
        con.print("❌ OpenAI SDK: [red]not installed[/red]")
        issues.append("Install deepgem dependencies: pip install deepgem")
    
    # Test DeepSeek connection (optional)
    if deepseek_key and not issues:
        con.print("\n[dim]Testing DeepSeek connection...[/dim]")
        try:
            client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
            response = client.models.list()
            con.print("✅ DeepSeek API: [green]connected successfully[/green]")
        except Exception as e:
            con.print(f"⚠️  DeepSeek API: [yellow]connection failed[/yellow]")
            warnings.append(f"DeepSeek connection error: {str(e)[:100]}")
    
    # Summary
    con.print("\n" + "─" * 50)
    if not issues and not warnings:
        con.print("\n[bold green]✨ All systems operational![/bold green]")
        con.print("\nTry these commands:")
        con.print("  deepgem chat \"Hello, world!\"")
        con.print("  deepgem ask \"Write a Python hello world script\"")
        if gemini_path:
            con.print("  deepgem gem -p \"List files in current directory\"")
    elif issues:
        con.print(f"\n[bold red]Found {len(issues)} issue(s) to fix:[/bold red]")
        for i, issue in enumerate(issues, 1):
            con.print(f"  {i}. {issue}")
        if warnings:
            con.print(f"\n[bold yellow]Also {len(warnings)} warning(s):[/bold yellow]")
            for warning in warnings:
                con.print(f"  ⚠️  {warning}")
    else:
        con.print(f"\n[bold yellow]Setup looks good with {len(warnings)} warning(s):[/bold yellow]")
        for warning in warnings:
            con.print(f"  ⚠️  {warning}")
        con.print("\n[green]You should be ready to use deepgem![/green]")
    
    con.print("")
    return 0 if not issues else 1
