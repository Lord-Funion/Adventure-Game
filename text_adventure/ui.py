"""Reusable terminal UI helpers for menus and short choices."""

from dataclasses import dataclass, field

from .pacing import ask, say
from .terminal_colors import Fore, Style


@dataclass(frozen=True)
class MenuOption:
    """One selectable row in a terminal menu."""

    key: str
    label: str
    value: str
    detail: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True
    status: str = ""


def normalize_choice(value):
    """Normalize player text so menu input feels forgiving."""
    return " ".join(value.strip().lower().split())


def divider(title):
    """Print a compact section title."""
    print(f"\n{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}=== {title} ==={Style.RESET_ALL}")


def stat_meter(current, maximum, width=16):
    """Return a small ASCII meter for health and mana displays."""
    if maximum <= 0:
        return "[" + "-" * width + "]"
    filled = round(width * max(0, min(current, maximum)) / maximum)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _option_inputs(option):
    inputs = {option.key, option.label, *option.aliases}
    return {normalize_choice(value) for value in inputs if value}


def choose_menu(title, options, prompt="Choose: ", subtitle=None, invalid=None):
    """Render a menu until the player chooses an enabled option."""
    invalid = invalid or "\nPlease choose one of the listed options."

    while True:
        divider(title)
        if subtitle:
            print(subtitle)

        for option in options:
            line = f"{option.key}. {option.label}"
            if option.detail:
                line += f" - {option.detail}"
            if option.status:
                line += f" ({option.status})"
            if not option.enabled:
                line = f"{Style.DIM}{line}{Style.RESET_ALL}"
                print(line)
                continue

            print(
                f"{Fore.LIGHTCYAN_EX}{option.key}{Style.RESET_ALL}. "
                f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{option.label}{Style.RESET_ALL}",
                end="",
            )
            if option.detail:
                detail = option.detail
                if "\033[" not in detail:
                    detail = f"{Fore.LIGHTWHITE_EX}{detail}{Style.RESET_ALL}"
                print(f" - {detail}", end="")
            if option.status:
                print(f" ({Fore.LIGHTYELLOW_EX}{option.status}{Style.RESET_ALL})", end="")
            print()

        choice = normalize_choice(ask(prompt))
        for option in options:
            if choice in _option_inputs(option):
                if option.enabled:
                    return option.value
                say(f"\n{option.label} is not available right now.", "quick")
                break
        else:
            say(invalid, "quick")


def ask_choice(prompt, choices, invalid):
    """Ask a short text choice and accept aliases for natural input."""
    normalized_choices = {
        value: {normalize_choice(alias) for alias in aliases}
        for value, aliases in choices.items()
    }

    while True:
        choice = normalize_choice(ask(prompt))
        for value, aliases in normalized_choices.items():
            if choice in aliases:
                return value
        say(invalid, "quick")


def money_text(amount):
    """Format money consistently across menus."""
    return f"{Fore.LIGHTYELLOW_EX}${amount}{Style.RESET_ALL}"
