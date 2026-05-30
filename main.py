"""Launcher for the reorganized text adventure."""

import sys

from colorama import just_fix_windows_console

from text_adventure.story import run_game


if __name__ == "__main__":
    just_fix_windows_console()
    load_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_game(load_path)
