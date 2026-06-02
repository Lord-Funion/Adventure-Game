"""Small helpers for text output timing.

The original game slept for 1.5 seconds after almost every line. That made
important moments feel the same as ordinary status text, so this module keeps
the pauses shorter and gives story beats a little more weight.
"""

import os
import re
import time

from .terminal_colors import Fore, Style


PAUSES = {
    "none": 0.0,
    "quick": 0.18,
    "line": 0.42,
    "beat": 0.7,
    "scene": 0.95,
}

SPEED_MULTIPLIERS = {
    "instant": 0.0,
    "fast": 0.55,
    "normal": 1.0,
    "slow": 1.35,
}


def _speed_multiplier():
    speed = os.getenv("TEXT_ADVENTURE_SPEED", "normal").strip().lower()
    return SPEED_MULTIPLIERS.get(speed, SPEED_MULTIPLIERS["normal"])


def pause(kind="line"):
    """Pause long enough for text to be readable without dragging."""
    time.sleep(PAUSES.get(kind, PAUSES["line"]) * _speed_multiplier())


def _paint_plain_message(message, kind):
    """Add color to plain text without interfering with already-colored text."""
    if "\033[" in message:
        return message

    leading = re.match(r"^\s*", message).group(0)
    body = message[len(leading):]
    if not body:
        return message

    lowered = body.lower()
    color = ""
    if body.startswith("===") or "the end" in lowered:
        color = Fore.LIGHTYELLOW_EX + Style.BRIGHT
    elif "game over" in lowered or "damage" in lowered or "attacks" in lowered:
        color = Fore.LIGHTRED_EX
    elif "good job" in lowered or "you learned" in lowered or "you bought" in lowered:
        color = Fore.LIGHTGREEN_EX
    elif "credits:" in lowered:
        color = Fore.LIGHTBLACK_EX
    elif '"' in body or kind == "beat":
        color = Fore.LIGHTCYAN_EX
    elif kind == "scene":
        color = Fore.LIGHTMAGENTA_EX

    if not color:
        return message
    return f"{leading}{color}{body}{Style.RESET_ALL}"


def say(message, kind="line"):
    """Print one story line, then wait for the requested pacing."""
    print(_paint_plain_message(message, kind))
    pause(kind)


def ask(prompt):
    """Read player input with normalized whitespace."""
    painted_prompt = prompt if "\033[" in prompt else f"{Fore.LIGHTCYAN_EX}{prompt}{Style.RESET_ALL}"
    return " ".join(input(painted_prompt).strip().split())
