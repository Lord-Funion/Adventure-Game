"""Startup logo rendering for the terminal game."""

import os

from colorama import Fore, Style


def _print_text_logo():
    print(
        Fore.LIGHTYELLOW_EX
        + r"""
    ___       __                 __
   /   | ____/ /   _____  ____  / /___  __________
  / /| |/ __  / | / / _ \/ __ \/ __/ / / / ___/ _ \
 / ___ / /_/ /| |/ /  __/ / / / /_/ /_/ / /  /  __/
/_/  |_\__,_/ |___/\___/_/ /_/\__/\__,_/_/   \___/
          ______
         / ____/___ _____ ___  ___
        / / __/ __ `/ __ `__ \/ _ \
       / /_/ / /_/ / / / / / /  __/
       \____/\__,_/_/ /_/ /_/\___/
"""
        + Style.RESET_ALL
    )


def show_startup_logo():
    """Show the adventure logo before the main menu or loaded save starts."""
    if os.getenv("TEXT_ADVENTURE_HIDE_LOGO"):
        return

    _print_text_logo()
