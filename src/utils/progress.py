"""Progress tracking utilities."""

import sys
import time
import math
from typing import Optional, Callable
from .colors import Colors


class ProgressTracker:
    """Progress tracking with callback support."""
    
    def __init__(self, job_id: str, callback: Optional[Callable] = None):
        self.job_id = job_id
        self.callback = callback
        self.start_time = time.time()
    
    def update(self, status: str, progress: int):
        """Update progress and call callback if provided."""
        if self.callback:
            self.callback(status, progress)
    
    def update_download(self, status: str, progress: int, extra_info: str = ""):
        """Update download progress with extra info."""
        if self.callback:
            self.callback(f"download_{status}", progress)


def update_progress(current: float, total: float, prefix: str = "", suffix: str = "", 
                   decimals: int = 1, length: int = 40, extra_info: str = ""):
    """
    Display animated progress bar with detailed information.
    
    Args:
        current: Current progress value
        total: Total progress value
        prefix: Prefix string
        suffix: Suffix string
        decimals: Number of decimal places for percentage
        length: Length of progress bar
        extra_info: Additional information to display
    """
    if total == 0:
        total = 1
    
    percent = min(100, (100 * (current / float(total))))
    filled_length = int(length * percent / 100)
    
    # Animated progress characters
    animation_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    animation_index = int(time.time() * 8) % len(animation_chars)
    
    # Progress bar coloring
    if percent < 30:
        bar_color = Colors.FAIL
    elif percent < 70:
        bar_color = Colors.WARNING
    else:
        bar_color = Colors.GREEN
    
    # Bar construction
    filled = '█' * filled_length
    if filled_length < length:
        # Animated character at progress end
        filled += animation_chars[animation_index]
        empty = '░' * (length - filled_length - 1)
    else:
        empty = ''
    
    bar = bar_color + filled + Colors.ENDC + empty
    
    # Additional info formatting
    info_str = f" │ {extra_info}" if extra_info else ""
    
    # Complete progress line
    progress_line = f'\r{prefix} │{bar}│ {percent:5.1f}% {suffix}{info_str}'
    
    # Overwrite previous line
    sys.stdout.write(progress_line + ' ' * 10)  # Extra space for cleanup
    sys.stdout.flush()
    
    if percent >= 100:
        print()  # New line when complete


class SmoothProgressSimulator:
    """Simulate smooth progress with realistic timing."""
    
    def __init__(self, duration_estimate: float, prefix: str = "Feldolgozás"):
        self.duration_estimate = duration_estimate
        self.prefix = prefix
        self.start_time = time.time()
        self.last_update = 0
    
    def update_progress_simulation(self, check_completion_callback: Optional[Callable] = None):
        """Run smooth progress simulation until completion."""
        while True:
            elapsed = time.time() - self.start_time
            
            # Non-linear progress curve (realistic feel)
            if elapsed < self.duration_estimate * 0.3:
                # First 30% quickly
                progress = (elapsed / (self.duration_estimate * 0.3)) * 40
            elif elapsed < self.duration_estimate * 0.7:
                # Middle 40% normally
                progress = 40 + ((elapsed - self.duration_estimate * 0.3) / (self.duration_estimate * 0.4)) * 40
            else:
                # Last 30% slowly
                progress = 80 + ((elapsed - self.duration_estimate * 0.7) / (self.duration_estimate * 0.3)) * 15
            
            progress = min(95, progress)  # Cap at 95% until actually complete
            
            # Time information
            eta = max(0, self.duration_estimate - elapsed)
            elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
            eta_str = f"{int(eta//60)}:{int(eta%60):02d}"
            
            extra_info = f"Eltelt: {elapsed_str} │ Hátra: ~{eta_str}"
            
            update_progress(
                progress, 100,
                prefix=self.prefix,
                extra_info=extra_info
            )
            
            # Check completion callback
            if check_completion_callback and elapsed - self.last_update > 0.5:
                self.last_update = elapsed
                status = check_completion_callback()
                if status == "done":
                    update_progress(100, 100, prefix="✓ Kész", 
                                  extra_info=f"Teljes idő: {elapsed_str}")
                    break
            
            time.sleep(0.1)  # 100ms refresh for smoothness


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"