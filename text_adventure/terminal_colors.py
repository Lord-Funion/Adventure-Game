"""Optional terminal color support with a no-dependency fallback."""

try:
    from colorama import Fore, Style, just_fix_windows_console
except ModuleNotFoundError:
    class _EmptyCodes:
        def __getattr__(self, _name):
            return ""

    Fore = _EmptyCodes()
    Style = _EmptyCodes()

    def just_fix_windows_console():
        return None
