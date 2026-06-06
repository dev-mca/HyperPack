"""
Console output helpers - colors, banners, prompts
Works on Windows, Linux, macOS
"""

import os
import sys
import platform

# Enable ANSI colors on Windows
if platform.system() == "Windows":
    os.system("color")  # enables ANSI in cmd/powershell


class Color:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


def banner():
    print(f"""
{Color.CYAN}{Color.BOLD}
  ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗  █████╗  ██████╗██╗  ██╗
  ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██║ ██╔╝
  ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝██████╔╝███████║██║     █████╔╝ 
  ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗██╔═══╝ ██╔══██║██║     ██╔═██╗ 
  ██║  ██║   ██║   ██║     ███████╗██║  ██║██║     ██║  ██║╚██████╗██║  ██╗
  ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
{Color.RESET}{Color.GRAY}  Install any Android icon pack on Xiaomi HyperOS  •  v1.0.0{Color.RESET}
""")


def step(number, total, text):
    print(f"\n{Color.CYAN}{Color.BOLD}[{number}/{total}]{Color.RESET} {Color.WHITE}{text}{Color.RESET}")


def success(text):
    print(f"  {Color.GREEN}✓{Color.RESET}  {text}")


def error(text):
    print(f"  {Color.RED}✗{Color.RESET}  {text}")


def warn(text):
    print(f"  {Color.YELLOW}⚠{Color.RESET}  {text}")


def info(text):
    print(f"  {Color.GRAY}→{Color.RESET}  {text}")


def progress(text):
    print(f"  {Color.CYAN}…{Color.RESET}  {text}", end="\r")


def done(text):
    print(f"  {Color.GREEN}✓{Color.RESET}  {text}              ")  # spaces clear the \r line


def ask(prompt, default=None):
    """Prompt user for input with optional default."""
    if default:
        full_prompt = f"  {Color.YELLOW}?{Color.RESET}  {prompt} {Color.GRAY}[{default}]{Color.RESET}: "
    else:
        full_prompt = f"  {Color.YELLOW}?{Color.RESET}  {prompt}: "
    
    try:
        value = input(full_prompt).strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def ask_yes_no(prompt, default=True):
    """Yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    full_prompt = f"  {Color.YELLOW}?{Color.RESET}  {prompt} {Color.GRAY}[{hint}]{Color.RESET}: "
    try:
        value = input(full_prompt).strip().lower()
        if not value:
            return default
        return value in ("y", "yes", "ja", "j")
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def separator():
    width = min(os.get_terminal_size().columns, 72) if sys.stdout.isatty() else 72
    print(f"  {Color.GRAY}{'─' * (width - 2)}{Color.RESET}")


def section(title):
    print(f"\n{Color.MAGENTA}{Color.BOLD}  {title}{Color.RESET}")
    separator()
