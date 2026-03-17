"""
Interactive CLI for QuranReelGen.
Features:
 - First-run setup wizard
 - Cool ASCII art banner
 - Easy-to-use menu with Rich formatting
 - Persistent settings
"""
import sys
import os
import uuid
import logging

from .config import POPULAR_RECITERS, OUTPUT_DIR
from .models import ReelRequest
from .core import process_job
from .settings import (
    load_settings, save_settings, is_first_run, DEFAULT_SETTINGS, get_settings_path
)


# ─── ASCII Art ────────────────────────────────────────────────────
BANNER = r"""
[bold cyan]
   ██████╗ ██╗   ██╗██████╗  █████╗ ███╗   ██╗
  ██╔═══██╗██║   ██║██╔══██╗██╔══██╗████╗  ██║
  ██║   ██║██║   ██║██████╔╝███████║██╔██╗ ██║
  ██║▄▄ ██║██║   ██║██╔══██╗██╔══██║██║╚██╗██║
  ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║ ╚████║
   ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝

  ██████╗ ███████╗███████╗██╗          ██████╗ ███████╗███╗   ██╗
  ██╔══██╗██╔════╝██╔════╝██║         ██╔════╝ ██╔════╝████╗  ██║
  ██████╔╝█████╗  █████╗  ██║         ██║  ███╗█████╗  ██╔██╗ ██║
  ██╔══██╗██╔══╝  ██╔══╝  ██║         ██║   ██║██╔══╝  ██║╚██╗██║
  ██║  ██║███████╗███████╗███████╗    ╚██████╔╝███████╗██║ ╚████║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝     ╚═════╝ ╚══════╝╚═╝  ╚═══╝
[/bold cyan]"""

TAGLINE = "[dim italic]Generate beautiful Quran recitation reels in seconds[/dim italic]"
VERSION = "v2.0"


def _ensure_rich():
    """Ensure rich is installed, exit with a message if not."""
    try:
        from rich.console import Console
        return True
    except ImportError:
        print("\n[!] The 'rich' package is required for the interactive CLI.")
        print("    Install it with:  pip install rich\n")
        sys.exit(1)


def _get_rich_imports():
    """Import all rich components in one place."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich import box
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.rule import Rule
    from rich.columns import Columns
    from rich.padding import Padding
    from rich.align import Align
    return Console, Panel, Text, Table, box, Prompt, IntPrompt, Confirm, Rule, Columns, Padding, Align


def show_banner(console, Panel, box):
    """Display the ASCII art banner."""
    console.print(BANNER)
    console.print(f"  {TAGLINE}   [bold dim]({VERSION})[/bold dim]\n", justify="center")


def setup_wizard(console, Panel, Table, box, Prompt, IntPrompt, Confirm, Rule):
    """
    First-run setup wizard. Guides the user through initial configuration.
    Returns the settings dict.
    """
    settings = load_settings()

    console.print()
    console.print(
        Panel(
            "[bold yellow]🔧  Welcome! Let's set up QuranReelGen.[/bold yellow]\n\n"
            "[dim]This wizard runs once to configure your defaults.\n"
            "You can change any of these later from the main menu.[/dim]",
            border_style="yellow",
            box=box.DOUBLE,
            padding=(1, 3),
        )
    )
    console.print()

    # ── Step 1: Output Directory ──────────────────────────────
    console.print(Rule("[bold cyan]Step 1 of 5 — Output Directory[/bold cyan]", style="cyan"))
    console.print()
    console.print("  [dim]Where should generated videos be saved?[/dim]")
    console.print(f"  [dim]Press Enter for default: [bold]{OUTPUT_DIR}[/bold][/dim]")
    console.print()
    out_dir = Prompt.ask("  📂 Output directory", default=OUTPUT_DIR)
    out_dir = os.path.expanduser(out_dir)
    if not os.path.isabs(out_dir):
        out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    settings["output_dir"] = out_dir
    console.print(f"  [green]✓[/green] Output directory set to [bold]{out_dir}[/bold]\n")

    # ── Step 2: Default Reciter ────────────────────────────────
    console.print(Rule("[bold cyan]Step 2 of 5 — Default Reciter[/bold cyan]", style="cyan"))
    console.print()
    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column("#", style="bold cyan", width=4)
    tbl.add_column("Reciter", style="white")
    for idx, (rid, rname) in enumerate(POPULAR_RECITERS, 1):
        marker = " [yellow]★[/yellow]" if rid == settings["default_reciter"] else ""
        tbl.add_row(str(idx), f"{rname}{marker}")
    console.print(tbl)
    console.print()
    ri = Prompt.ask("  🎤 Pick a default reciter (number)", default="1")
    if ri.isdigit() and 1 <= int(ri) <= len(POPULAR_RECITERS):
        settings["default_reciter"] = POPULAR_RECITERS[int(ri) - 1][0]
    reciter_name = next((n for i, n in POPULAR_RECITERS if i == settings["default_reciter"]), settings["default_reciter"])
    console.print(f"  [green]✓[/green] Default reciter: [bold]{reciter_name}[/bold]\n")

    # ── Step 3: Video Orientation ──────────────────────────────
    console.print(Rule("[bold cyan]Step 3 of 5 — Video Orientation[/bold cyan]", style="cyan"))
    console.print()
    console.print("  [dim]Choose the default video orientation:[/dim]")
    console.print("    [cyan]1[/cyan]  Vertical  (9:16 — Reels, Shorts, TikTok)")
    console.print("    [cyan]2[/cyan]  Horizontal (16:9 — YouTube)")
    console.print()
    ori = Prompt.ask("  📐 Orientation", choices=["1", "2"], default="1")
    settings["default_orientation"] = "vertical" if ori == "1" else "horizontal"
    console.print(f"  [green]✓[/green] Orientation: [bold]{settings['default_orientation'].title()}[/bold]\n")

    # ── Step 4: Video Quality ──────────────────────────────────
    console.print(Rule("[bold cyan]Step 4 of 5 — Video Quality[/bold cyan]", style="cyan"))
    console.print()
    console.print("  [dim]Higher quality = slower rendering[/dim]")
    console.print("    [cyan]1[/cyan]  Ultrafast  [dim](quickest, lower quality)[/dim]")
    console.print("    [cyan]2[/cyan]  Veryfast   [dim](good balance)[/dim]")
    console.print("    [cyan]3[/cyan]  Fast       [dim](better quality)[/dim]")
    console.print("    [cyan]4[/cyan]  Medium     [dim](best quality, slowest)[/dim]")
    console.print()
    quality_map = {"1": "ultrafast", "2": "veryfast", "3": "fast", "4": "medium"}
    q = Prompt.ask("  🎞️  Quality preset", choices=["1", "2", "3", "4"], default="1")
    settings["default_video_quality"] = quality_map[q]
    console.print(f"  [green]✓[/green] Quality: [bold]{settings['default_video_quality']}[/bold]\n")

    # ── Step 5: Translation ────────────────────────────────────
    console.print(Rule("[bold cyan]Step 5 of 5 — Translations[/bold cyan]", style="cyan"))
    console.print()
    settings["include_translation"] = Confirm.ask(
        "  🌐 Include English translation by default?",
        default=settings["include_translation"]
    )
    console.print(f"  [green]✓[/green] Translation: [bold]{'Enabled' if settings['include_translation'] else 'Disabled'}[/bold]\n")

    # ── Done ──────────────────────────────────────────────────
    settings["first_run_complete"] = True
    save_settings(settings)

    console.print()
    console.print(
        Panel(
            "[bold green]✅  Setup complete![/bold green]\n\n"
            f"[dim]Settings saved to {get_settings_path()}[/dim]\n"
            "[dim]You can reconfigure anytime from the main menu → [bold]Settings[/bold][/dim]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 3),
        )
    )
    console.print()
    Prompt.ask("  Press [bold cyan]Enter[/bold cyan] to continue", default="")

    return settings


def interactive_cli():
    """Menu-driven interactive CLI for generating reels."""
    _ensure_rich()
    Console, Panel, Text, Table, box, Prompt, IntPrompt, Confirm, Rule, Columns, Padding, Align = _get_rich_imports()

    console = Console()
    console.clear()
    show_banner(console, Panel, box)

    # ── First-run setup ───────────────────────────────────────
    if is_first_run():
        settings = setup_wizard(console, Panel, Table, box, Prompt, IntPrompt, Confirm, Rule)
    else:
        settings = load_settings()

    # ── Current session values (seeded from saved settings) ───
    session = {
        "surah": 1,
        "ayah_start": 1,
        "ayah_end": 3,
        "reciter_id": settings.get("default_reciter", "ar.alafasy"),
        "bg_type": settings.get("default_bg_type", "color"),
        "bg_value": settings.get("default_bg_value", "#000000"),
        "font_size": settings.get("default_font_size", 100),
        "font_color": settings.get("default_font_color", "#FFFFFF"),
        "orientation": settings.get("default_orientation", "vertical"),
        "translation": settings.get("include_translation", False),
        "custom_text": None,
        "fps": settings.get("default_fps", 24),
        "video_quality": settings.get("default_video_quality", "ultrafast"),
        "output_dir": settings.get("output_dir", OUTPUT_DIR),
    }

    def reciter_display(rid):
        for i, n in POPULAR_RECITERS:
            if i == rid:
                return n
        return rid

    def print_menu():
        console.clear()
        show_banner(console, Panel, box)

        # Build the settings table
        tbl = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow",
            border_style="bright_black",
            title="[bold]Current Session[/bold]",
            title_style="bold white",
            width=68,
            padding=(0, 1),
        )
        tbl.add_column("#", style="bold cyan", width=4, justify="center")
        tbl.add_column("Setting", style="white", width=24)
        tbl.add_column("Value", style="bold green", width=36)

        tbl.add_row("1", "📖  Surah", str(session["surah"]))
        tbl.add_row("2", "📄  Ayah Range", f"{session['ayah_start']} → {session['ayah_end']}")
        tbl.add_row("3", "🎤  Reciter", reciter_display(session["reciter_id"]))
        tbl.add_row("4", "🎨  Background", f"{session['bg_type']} ({session['bg_value']})")
        tbl.add_row("5", "✏️   Font", f"{session['font_size']}px  {session['font_color']}")
        tbl.add_row("6", "📐  Orientation", session["orientation"].title())
        tbl.add_row("7", "🌐  Translation", "[green]Yes[/green]" if session["translation"] else "[red]No[/red]")
        tbl.add_row("8", "🎞️   Quality / FPS", f"{session['video_quality']}  •  {session['fps']} fps")
        tbl.add_row("9", "✍️   Custom Text", session["custom_text"] or "[dim]None[/dim]")

        console.print(Align.center(tbl))
        console.print()

        # Action bar
        console.print(
            "  [bold green]  ▶  G [/bold green] [white]Generate Reel[/white]"
            "      [bold magenta]  ⚙  S [/bold magenta] [white]Settings[/white]"
            "      [bold red]  ✕  Q [/bold red] [white]Quit[/white]",
            justify="center",
        )
        console.print()

    while True:
        print_menu()
        choice = Prompt.ask(
            "  [bold cyan]❯[/bold cyan] Choose an option",
            default="G",
            show_default=False,
        ).strip().upper()

        if choice == "Q":
            console.print("\n  [dim]Bye! 👋[/dim]\n")
            sys.exit(0)

        elif choice == "G":
            # Confirm before generating
            console.print()
            console.print(
                Panel(
                    f"[bold]Surah {session['surah']}, Ayahs {session['ayah_start']}–{session['ayah_end']}[/bold]\n"
                    f"Reciter: {reciter_display(session['reciter_id'])}\n"
                    f"Output: {session['output_dir']}",
                    title="[bold cyan]📋 Generation Summary[/bold cyan]",
                    border_style="cyan",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
            if Confirm.ask("\n  Start generating?", default=True):
                break
            # else loop back to menu

        elif choice == "S":
            # Re-run setup wizard
            console.clear()
            show_banner(console, Panel, box)
            settings = setup_wizard(console, Panel, Table, box, Prompt, IntPrompt, Confirm, Rule)
            # Apply saved settings back to session
            session["reciter_id"] = settings.get("default_reciter", session["reciter_id"])
            session["orientation"] = settings.get("default_orientation", session["orientation"])
            session["video_quality"] = settings.get("default_video_quality", session["video_quality"])
            session["translation"] = settings.get("include_translation", session["translation"])
            session["output_dir"] = settings.get("output_dir", session["output_dir"])

        elif choice == "1":
            session["surah"] = IntPrompt.ask("  📖 Surah number (1–114)", default=session["surah"])

        elif choice == "2":
            session["ayah_start"] = IntPrompt.ask("  Start Ayah", default=session["ayah_start"])
            session["ayah_end"] = IntPrompt.ask(
                "  End Ayah", default=max(session["ayah_end"], session["ayah_start"])
            )

        elif choice == "3":
            console.print()
            tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            tbl.add_column("#", style="bold cyan", width=4)
            tbl.add_column("Reciter", style="white")
            tbl.add_column("", style="dim")
            for idx, (rid, rname) in enumerate(POPULAR_RECITERS, 1):
                marker = "[yellow]★ current[/yellow]" if rid == session["reciter_id"] else ""
                tbl.add_row(str(idx), rname, marker)
            console.print(tbl)
            console.print()
            ri = Prompt.ask("  🎤 Enter reciter # or ID", default="1")
            if ri.isdigit() and 1 <= int(ri) <= len(POPULAR_RECITERS):
                session["reciter_id"] = POPULAR_RECITERS[int(ri) - 1][0]
            else:
                session["reciter_id"] = ri

        elif choice == "4":
            console.print()
            console.print("    [cyan]1[/cyan]  Solid Color")
            console.print("    [cyan]2[/cyan]  Video Background")
            console.print()
            bt = Prompt.ask("  🎨 Background type", choices=["1", "2"], default="1")
            session["bg_type"] = "color" if bt == "1" else "video"
            if session["bg_type"] == "color":
                session["bg_value"] = Prompt.ask("  Hex color", default=session["bg_value"])
            else:
                session["bg_value"] = Prompt.ask("  Video URL or path", default=session["bg_value"])

        elif choice == "5":
            session["font_size"] = IntPrompt.ask("  Font size (px)", default=session["font_size"])
            session["font_color"] = Prompt.ask("  Font color (hex)", default=session["font_color"])

        elif choice == "6":
            console.print()
            console.print("    [cyan]1[/cyan]  Vertical  (9:16)")
            console.print("    [cyan]2[/cyan]  Horizontal (16:9)")
            console.print()
            ori = Prompt.ask("  📐 Orientation", choices=["1", "2"], default="1" if session["orientation"] == "vertical" else "2")
            session["orientation"] = "vertical" if ori == "1" else "horizontal"

        elif choice == "7":
            session["translation"] = Confirm.ask(
                "  🌐 Include English translation?", default=session["translation"]
            )

        elif choice == "8":
            session["fps"] = IntPrompt.ask("  FPS", default=session["fps"])
            console.print()
            console.print("    [cyan]1[/cyan]  Ultrafast  [dim](quickest)[/dim]")
            console.print("    [cyan]2[/cyan]  Veryfast   [dim](balanced)[/dim]")
            console.print("    [cyan]3[/cyan]  Fast       [dim](better quality)[/dim]")
            console.print("    [cyan]4[/cyan]  Medium     [dim](best quality)[/dim]")
            console.print()
            quality_map = {"1": "ultrafast", "2": "veryfast", "3": "fast", "4": "medium"}
            rev_map = {v: k for k, v in quality_map.items()}
            q = Prompt.ask(
                "  🎞️  Quality preset",
                choices=["1", "2", "3", "4"],
                default=rev_map.get(session["video_quality"], "1"),
            )
            session["video_quality"] = quality_map[q]

        elif choice == "9":
            ans = Prompt.ask("  ✍️  Custom Arabic text (leave empty to clear)", default="")
            session["custom_text"] = ans if ans else None

    # ── Build the request ──────────────────────────────────────
    return ReelRequest(
        surah=session["surah"],
        ayah_start=session["ayah_start"],
        ayah_end=session["ayah_end"],
        reciter_id=session["reciter_id"],
        bg_type=session["bg_type"],
        bg_value=session["bg_value"],
        custom_text=session["custom_text"],
        font_size=session["font_size"],
        font_color=session["font_color"],
        include_translation=session["translation"],
        orientation=session["orientation"],
        output_dir=session["output_dir"],
        fps=session["fps"],
        video_quality=session["video_quality"],
    )


def run_cli_job(req: ReelRequest):
    """Execute the generation job and display results."""
    _ensure_rich()
    from rich.console import Console
    from rich.panel import Panel
    from rich import box

    console = Console()
    job_id = f"cli_{uuid.uuid4().hex[:8]}"
    jobs = {job_id: {"status": "queued", "progress": 0}}

    console.print()
    console.print(
        Panel(
            "[bold cyan]⏳  Generating your reel…[/bold cyan]\n\n"
            "[dim]This may take a moment depending on the number of ayahs and your quality settings.[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()

    process_job(job_id, req, jobs)

    if jobs[job_id]["status"] == "completed":
        path = jobs[job_id]["output_file"]
        console.print(
            Panel(
                f"[bold green]✅  Success![/bold green]\n\n"
                f"Video saved to:\n[bold underline]{path}[/bold underline]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]❌  Generation failed[/bold red]\n\n"
                f"Error: {jobs[job_id].get('error', 'Unknown error')}",
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )
    console.print()
