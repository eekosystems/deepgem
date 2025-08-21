\
import os, sys, subprocess
from typing import Optional, List
import typer
from rich.console import Console

# OpenAI SDK works with DeepSeek via base_url
from openai import OpenAI

# ---------------- Banner ----------------
BANNER = r"""
██████╗ ███████╗███████╗██████╗     ██████╗ ███████╗███╗   ███╗
██╔══██╗██╔════╝██╔════╝██╔══██╗   ██╔════╝ ██╔════╝████╗ ████║
██║  ██║█████╗  █████╗  ██████╔╝   ██║  ███╗█████╗  ██╔████╔██║
██║  ██║██╔══╝  ██╔══╝  ██╔══██╗   ██║   ██║██╔══╝  ██║╚██╔╝██║
██████╔╝███████╗███████╗██║  ██║   ╚██████╔╝███████╗██║ ╚═╝ ██║
╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝╚═╝     ╚═╝
                      
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
    cmd: List[str] = [os.environ.get("GEMINI_BIN", "gemini")]
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
        proc = subprocess.run(cmd, text=True)
        return proc.returncode
    except FileNotFoundError:
        con.print(
            "[red]Gemini CLI not found.[/red] Install with "
            "[bold]npm i -g @google/gemini-cli[/bold] or [bold]brew install gemini-cli[/bold]."
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
