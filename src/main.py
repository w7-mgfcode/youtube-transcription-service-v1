#!/usr/bin/env python3
"""Entry point for YouTube Transcription Service - supports both CLI and API modes."""

import sys
import os
import argparse
from typing import Optional

from .config import settings
from .utils.colors import Colors, print_header


def main():
    """Main entry point with mode detection and argument parsing."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="YouTube Transcription Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start API server
  python src/main.py --mode api
  
  # CLI mode with URL
  python src/main.py --mode cli "https://youtube.com/watch?v=..."
  
  # CLI mode with test mode
  python src/main.py --mode cli --test "https://youtube.com/watch?v=..."
  
  # Interactive CLI mode (preserves v25.py behavior)
  python src/main.py --mode cli --interactive
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["api", "cli"],
        default=settings.mode,
        help="Operating mode (default: from config/env)"
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube URL (required for non-interactive CLI mode)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - process only first 60 seconds"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive CLI mode (like original v25.py)"
    )
    
    parser.add_argument(
        "--breath-detection", "--breath",
        action="store_true",
        default=True,
        help="Enable breath/pause detection (default: enabled)"
    )
    
    parser.add_argument(
        "--no-breath-detection", "--no-breath",
        action="store_false",
        dest="breath_detection",
        help="Disable breath/pause detection"
    )
    
    parser.add_argument(
        "--vertex-ai",
        action="store_true",
        help="Enable Vertex AI post-processing"
    )
    
    parser.add_argument(
        "--host",
        default=settings.api_host,
        help="API server host (API mode only)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api_port,
        help="API server port (API mode only)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="YouTube Transcription Service v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Determine operating mode
    mode = args.mode.lower()
    
    try:
        if mode == "api":
            start_api_mode(args.host, args.port)
        elif mode == "cli":
            start_cli_mode(args)
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(Colors.WARNING + "\n\n⚠ Megszakítva felhasználó által!" + Colors.ENDC)
        sys.exit(0)
    except Exception as e:
        print(Colors.FAIL + f"\n\n✗ Kritikus hiba: {e}" + Colors.ENDC)
        sys.exit(1)


def start_api_mode(host: str, port: int):
    """Start FastAPI server."""
    print(Colors.BLUE + f"🚀 API mód indítása: http://{host}:{port}" + Colors.ENDC)
    print(Colors.CYAN + f"   📚 API dokumentáció: http://{host}:{port}/docs" + Colors.ENDC)
    print(Colors.CYAN + f"   🔍 Health check: http://{host}:{port}/health" + Colors.ENDC)
    print()
    
    try:
        import uvicorn
        from .api import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_config=None  # Use default logging
        )
    except ImportError:
        print(Colors.FAIL + "✗ FastAPI vagy uvicorn nincs telepítve!" + Colors.ENDC)
        print("Telepítsd: pip install fastapi uvicorn")
        sys.exit(1)


def start_cli_mode(args):
    """Start CLI mode with different interaction styles."""
    from .core.transcriber import TranscriptionService
    from .cli import InteractiveCLI
    
    if args.interactive:
        # Interactive mode - preserves original v25.py experience
        cli = InteractiveCLI()
        cli.run()
    elif args.url:
        # Direct URL mode
        run_direct_cli(args)
    else:
        # No URL provided and not interactive - show help
        print(Colors.FAIL + "✗ URL szükséges CLI módhoz, vagy használd --interactive kapcsolót" + Colors.ENDC)
        print("Használat: python src/main.py --mode cli 'https://youtube.com/watch?v=...'")
        print("Vagy:      python src/main.py --mode cli --interactive")
        sys.exit(1)


def run_direct_cli(args):
    """Run direct CLI processing with provided URL."""
    transcriber = TranscriptionService()
    
    print_header()
    
    # Show processing parameters
    print(Colors.BOLD + "⚙️ Feldolgozási paraméterek:" + Colors.ENDC)
    print(f"   ├─ URL: {args.url}")
    print(f"   ├─ Teszt mód: {'Igen' if args.test else 'Nem'}")
    print(f"   ├─ Levegővétel detektálás: {'Igen' if args.breath_detection else 'Nem'}")
    print(f"   └─ Vertex AI: {'Igen' if args.vertex_ai else 'Nem'}")
    print()
    
    if args.test:
        print(Colors.WARNING + "⚡ TESZT MÓD: Csak az első 60 másodperc lesz feldolgozva!" + Colors.ENDC)
    
    if args.breath_detection:
        print(Colors.CYAN + "💨 Levegővétel detektálás bekapcsolva - szünetek jelölve lesznek (• és ••)" + Colors.ENDC)
    
    # Progress callback for CLI
    def print_progress(status: str, progress: int):
        if progress >= 0:
            print(f"[{progress:3d}%] {status}")
    
    try:
        # Process transcription
        result = transcriber.process(
            url=args.url,
            test_mode=args.test,
            breath_detection=args.breath_detection,
            use_vertex_ai=args.vertex_ai,
            progress_callback=print_progress
        )
        
        if result["status"] == "completed":
            print(Colors.BOLD + Colors.GREEN + f"\n✅ SIKERES FELDOLGOZÁS!" + Colors.ENDC)
            print(Colors.GREEN + f"   📁 Eredmény: {result['transcript_file']}" + Colors.ENDC)
            print(Colors.GREEN + f"   📺 Cím: {result['title']}" + Colors.ENDC)
            print(Colors.GREEN + f"   ⏱️  Időtartam: {result['duration']}s" + Colors.ENDC)
            print(Colors.GREEN + f"   📊 Szószám: {result['word_count']}" + Colors.ENDC)
            
            # Show pause statistics if available
            if args.breath_detection:
                try:
                    with open(result['transcript_file'], 'r', encoding='utf-8') as f:
                        content = f.read()
                        pause_count = content.count('•') + content.count('[szünet]') + content.count('[levegővétel]')
                        if pause_count > 0:
                            print(Colors.CYAN + f"   💨 Detektált szünetek: {pause_count} db" + Colors.ENDC)
                except:
                    pass
        else:
            print(Colors.FAIL + f"\n✗ Hiba: {result.get('error', 'Ismeretlen hiba')}" + Colors.ENDC)
            sys.exit(1)
            
    except Exception as e:
        print(Colors.FAIL + f"\n✗ Hiba: {e}" + Colors.ENDC)
        sys.exit(1)
    
    # Show completion message
    print(Colors.CYAN + "\n" + "="*70 + Colors.ENDC)
    print(Colors.BOLD + "   Köszönjük, hogy használtad a YouTube Transcribe-ot! 👋" + Colors.ENDC)
    print(Colors.CYAN + "="*70 + Colors.ENDC)


if __name__ == "__main__":
    main()