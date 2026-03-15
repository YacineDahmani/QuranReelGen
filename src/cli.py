import sys
import os
import uuid
import logging
from .config import POPULAR_RECITERS, OUTPUT_DIR
from .models import ReelRequest
from .core import process_job

def interactive_cli():
    """Menu-driven interactive CLI for generating reels."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        from rich import box
        from rich.prompt import Prompt, IntPrompt, Confirm
    except ImportError:
        print("\n[!] The 'rich' package is required for interactive mode.")
        print("    Install it with:  pip install rich\n")
        sys.exit(1)

    console = Console()

    # Default settings
    settings = {
        "surah": 1,
        "ayah_start": 1,
        "ayah_end": 3,
        "reciter_id": POPULAR_RECITERS[0][0],
        "bg_type": "color",
        "bg_value": "#000000",
        "font_size": 100,
        "font_color": "#FFFFFF",
        "orientation": "vertical",
        "translation": False,
        "custom_text": None,
        "fps": 24,
        "video_quality": "ultrafast"
    }

    def print_menu():
        console.clear()
        header = Text("Quran Reel Generator", style="bold cyan justify-center")
        console.print(Panel(header, border_style="cyan", box=box.ROUNDED))
        
        tbl = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow", width=60)
        tbl.add_column("Option", style="bold cyan", width=6)
        tbl.add_column("Setting", style="white")
        tbl.add_column("Current Value", style="green")
        
        tbl.add_row("[1]", "Surah", str(settings["surah"]))
        tbl.add_row("[2]", "Ayah Range", f"{settings['ayah_start']} - {settings['ayah_end']}")
        tbl.add_row("[3]", "Reciter", settings["reciter_id"])
        tbl.add_row("[4]", "Background", f"{settings['bg_type']} ({settings['bg_value']})")
        tbl.add_row("[5]", "Font Size & Color", f"{settings['font_size']}px, {settings['font_color']}")
        tbl.add_row("[6]", "Orientation", settings["orientation"])
        tbl.add_row("[7]", "Include Translation", "Yes" if settings["translation"] else "No")
        tbl.add_row("[8]", "Advanced/Video Settings", f"{settings['fps']} fps, {settings['video_quality']}")
        tbl.add_row("[9]", "Custom Arabic Text", settings["custom_text"] or "(None)")
        
        console.print(tbl)
        console.print("  [bold green][G][/bold green] Generate Reel   [bold red][Q][/bold red] Quit")
        console.print()

    while True:
        print_menu()
        choice = Prompt.ask("Select an option to change", default="G", show_default=False).upper()

        if choice == "Q":
            console.print("[dim]Cancelled.[/dim]")
            sys.exit(0)
        elif choice == "G":
            break
        elif choice == "1":
            settings["surah"] = IntPrompt.ask("Surah number (1-114)", default=settings["surah"])
        elif choice == "2":
            settings["ayah_start"] = IntPrompt.ask("Start Ayah", default=settings["ayah_start"])
            settings["ayah_end"] = IntPrompt.ask("End Ayah", default=max(settings["ayah_end"], settings["ayah_start"]))
        elif choice == "3":
            console.print("\n[bold]Popular Reciters:[/bold]")
            for idx, (rid, rname) in enumerate(POPULAR_RECITERS, 1):
                console.print(f"  [cyan]{idx}[/cyan]. {rname} [dim]({rid})[/dim]")
            ri = Prompt.ask("Enter reciter ID or number", default="1")
            if ri.isdigit() and 1 <= int(ri) <= len(POPULAR_RECITERS):
                settings["reciter_id"] = POPULAR_RECITERS[int(ri)-1][0]
            else:
                settings["reciter_id"] = ri
        elif choice == "4":
            settings["bg_type"] = Prompt.ask("Type", choices=["color", "video"], default=settings["bg_type"])
            if settings["bg_type"] == "color":
                settings["bg_value"] = Prompt.ask("Hex color", default=settings["bg_value"])
            else:
                settings["bg_value"] = Prompt.ask("Video URL/Path", default=settings["bg_value"])
        elif choice == "5":
            settings["font_size"] = IntPrompt.ask("Font size", default=settings["font_size"])
            settings["font_color"] = Prompt.ask("Font color (hex)", default=settings["font_color"])
        elif choice == "6":
            settings["orientation"] = Prompt.ask("Orientation", choices=["vertical", "horizontal"], default=settings["orientation"])
        elif choice == "7":
            settings["translation"] = Confirm.ask("Include English translation?", default=settings["translation"])
        elif choice == "8":
            settings["fps"] = IntPrompt.ask("FPS", default=settings["fps"])
            settings["video_quality"] = Prompt.ask("Quality", choices=["ultrafast", "veryfast", "fast", "medium"], default=settings["video_quality"])
        elif choice == "9":
            ans = Prompt.ask("Custom text (leave empty to clear)", default="")
            settings["custom_text"] = ans if ans else None

    return ReelRequest(
        surah=settings["surah"],
        ayah_start=settings["ayah_start"],
        ayah_end=settings["ayah_end"],
        reciter_id=settings["reciter_id"],
        bg_type=settings["bg_type"],
        bg_value=settings["bg_value"],
        custom_text=settings["custom_text"],
        font_size=settings["font_size"],
        font_color=settings["font_color"],
        include_translation=settings["translation"],
        orientation=settings["orientation"],
        output_dir=OUTPUT_DIR,
        fps=settings["fps"],
        video_quality=settings["video_quality"]
    )

def run_cli_job(req: ReelRequest):
    from rich.console import Console
    console = Console()
    job_id = f"cli_{uuid.uuid4().hex[:8]}"
    jobs = {job_id: {"status": "queued", "progress": 0}}
    
    console.print(f"\n[bold cyan]Processing...[/bold cyan]\n")
    process_job(job_id, req, jobs)

    if jobs[job_id]["status"] == "completed":
        path = jobs[job_id]["output_file"]
        console.print(f"\n[bold green]Success![/bold green] Video saved to: [underline]{path}[/underline]\n")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {jobs[job_id].get('error')}\n")
