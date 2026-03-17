import argparse
import sys
import os
import logging
import tempfile

# Add project root to sys.path to ensure quran_reel is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api import start_api
from src.cli import interactive_cli, run_cli_job
from src.models import ReelRequest
from src.settings import load_settings, reset_settings

def setup_logging():
    log_file = os.path.join(tempfile.gettempdir(), 'quran_reel.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Quran Reel Generator — create beautiful Quran recitation videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                    Launch interactive CLI (default)\n"
            "  python main.py --api              Start the REST API server\n"
            "  python main.py --surah 36 --ayah-start 1 --ayah-end 5\n"
            "  python main.py --reset            Reset all settings to defaults\n"
        ),
    )
    parser.add_argument("--api", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI (default)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="API port (default: 8001)")
    parser.add_argument("--reset", action="store_true", help="Reset all settings to defaults and re-run setup")
    
    # Optional flags for non-interactive CLI (for scripting)
    parser.add_argument("--surah", type=int, help="Surah number")
    parser.add_argument("--ayah-start", type=int, help="Start Ayah")
    parser.add_argument("--ayah-end", type=int, help="End Ayah")
    parser.add_argument("--reciter", type=str, default=None, help="Reciter ID (default: from settings)")
    
    args = parser.parse_args()

    if args.reset:
        reset_settings()
        print("Settings have been reset. Next launch will show the setup wizard.")
        return

    if args.api:
        start_api(host=args.host, port=args.port)
    elif args.surah and args.ayah_start and args.ayah_end:
        # Direct CLI mode if flags are provided (for scripting)
        settings = load_settings()
        req = ReelRequest(
            surah=args.surah,
            ayah_start=args.ayah_start,
            ayah_end=args.ayah_end,
            reciter_id=args.reciter or settings.get("default_reciter", "ar.alafasy"),
            output_dir=settings.get("output_dir", None),
            fps=settings.get("default_fps", 24),
            video_quality=settings.get("default_video_quality", "ultrafast"),
            orientation=settings.get("default_orientation", "vertical"),
            include_translation=settings.get("include_translation", False),
        )
        run_cli_job(req)
    else:
        # Default to interactive CLI
        req = interactive_cli()
        run_cli_job(req)

if __name__ == "__main__":
    main()
