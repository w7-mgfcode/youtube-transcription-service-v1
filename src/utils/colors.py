"""Console colors and formatting utilities."""

import sys


class Colors:
    """ANSI color codes for console output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'  # Same as WARNING for consistency
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """Display application header with styling."""
    print(Colors.CYAN + "=" * 70 + Colors.ENDC)
    print(Colors.BOLD + Colors.CYAN + "  🎥 YouTube Videó → Szöveges Átirat (Google Speech API)" + Colors.ENDC)
    print(Colors.CYAN + "=" * 70 + Colors.ENDC)
    print(Colors.WARNING + "  ⚡ Optimalizált verzió: FLAC konverzió, progress bar, teszt mód" + Colors.ENDC)
    print(Colors.CYAN + "=" * 70 + Colors.ENDC + "\n")


def colored_text(text: str, color: str) -> str:
    """Apply color to text."""
    color_code = getattr(Colors, color.upper(), Colors.ENDC)
    return f"{color_code}{text}{Colors.ENDC}"


def print_colored(text: str, color: str = ""):
    """Print colored text to console."""
    if color:
        print(colored_text(text, color))
    else:
        print(text)