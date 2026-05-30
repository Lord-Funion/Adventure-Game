"""Small helpers for text output timing.

The original game slept for 1.5 seconds after almost every line. That made
important moments feel the same as ordinary status text, so this module keeps
the pauses shorter and gives story beats a little more weight.
"""

import os
import time


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


def say(message, kind="line"):
    """Print one story line, then wait for the requested pacing."""
    print(message)
    pause(kind)


def ask(prompt):
    """Read player input with normalized whitespace."""
    return " ".join(input(prompt).strip().split())
