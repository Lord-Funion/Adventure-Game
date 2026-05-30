"""Encrypted and authenticated save-file helpers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
from datetime import UTC, datetime


SAVE_DIR = Path(__file__).resolve().parents[1] / "saves"
SAVE_SUFFIX = ".tasave"
SAVE_FORMAT_VERSION = 1

_MAGIC = "TEXT_ADVENTURE_SAVE"
_KDF_ROUNDS = 120_000
_APP_KEY = (
    b"Adventure Game save key v1. This protects saves from casual editing, "
    b"but local games cannot be perfectly cheat-proof."
)
_SAFE_SLOT_CHARS = re.compile(r"[^A-Za-z0-9_. -]+")


class SaveError(Exception):
    """Raised when a save cannot be read, verified, or decoded."""


def _urlsafe_b64encode(value):
    return base64.urlsafe_b64encode(value).decode("ascii")


def _urlsafe_b64decode(value):
    try:
        return base64.urlsafe_b64decode(value.encode("ascii"))
    except (binascii.Error, ValueError, TypeError) as exc:
        raise SaveError("The save file is not valid base64 data.") from exc


def _base_key():
    extra_key = os.getenv("TEXT_ADVENTURE_SAVE_KEY", "").encode("utf-8")
    return hashlib.sha256(_APP_KEY + extra_key).digest()


def _derive_keys(salt):
    material = hashlib.pbkdf2_hmac(
        "sha256",
        _base_key(),
        salt,
        _KDF_ROUNDS,
        dklen=64,
    )
    return material[:32], material[32:]


def _keystream(key, nonce, length):
    output = bytearray()
    counter = 0
    while len(output) < length:
        block_id = counter.to_bytes(8, "big")
        output.extend(hmac.new(key, nonce + block_id, hashlib.sha256).digest())
        counter += 1
    return bytes(output[:length])


def _xor_bytes(left, right):
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def _mac_body(container):
    fields = [
        container["magic"],
        str(container["version"]),
        container["salt"],
        container["nonce"],
        container["payload"],
    ]
    return "|".join(fields).encode("utf-8")


def _encrypt_payload(payload):
    plain = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    encryption_key, mac_key = _derive_keys(salt)
    cipher_text = _xor_bytes(plain, _keystream(encryption_key, nonce, len(plain)))

    container = {
        "magic": _MAGIC,
        "version": SAVE_FORMAT_VERSION,
        "kdf": "pbkdf2-hmac-sha256",
        "rounds": _KDF_ROUNDS,
        "cipher": "hmac-sha256-stream-xor",
        "salt": _urlsafe_b64encode(salt),
        "nonce": _urlsafe_b64encode(nonce),
        "payload": _urlsafe_b64encode(cipher_text),
    }
    container["mac"] = _urlsafe_b64encode(
        hmac.new(mac_key, _mac_body(container), hashlib.sha256).digest()
    )
    return container


def _decrypt_payload(container):
    if not isinstance(container, dict):
        raise SaveError("The save file is not a save container.")
    if container.get("magic") != _MAGIC:
        raise SaveError("This is not an Adventure Game save file.")
    if container.get("version") != SAVE_FORMAT_VERSION:
        raise SaveError("This save version is not supported.")

    required_fields = ("salt", "nonce", "payload", "mac")
    if any(field not in container for field in required_fields):
        raise SaveError("The save file is missing required data.")

    salt = _urlsafe_b64decode(container["salt"])
    nonce = _urlsafe_b64decode(container["nonce"])
    cipher_text = _urlsafe_b64decode(container["payload"])
    expected_mac = _urlsafe_b64decode(container["mac"])
    encryption_key, mac_key = _derive_keys(salt)
    actual_mac = hmac.new(mac_key, _mac_body(container), hashlib.sha256).digest()
    if not hmac.compare_digest(expected_mac, actual_mac):
        raise SaveError("The save file failed its tamper check.")

    plain = _xor_bytes(cipher_text, _keystream(encryption_key, nonce, len(cipher_text)))
    try:
        return json.loads(plain.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SaveError("The save payload could not be decoded.") from exc


def sanitize_slot_name(value):
    """Return a filesystem-friendly save slot name."""
    cleaned = _SAFE_SLOT_CHARS.sub("", value).strip(" .")
    return cleaned or "adventure-save"


def default_save_path(stem=None):
    """Build a save path in the local saves directory."""
    if stem is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        stem = f"adventure_{timestamp}"
    return SAVE_DIR / f"{sanitize_slot_name(stem)}{SAVE_SUFFIX}"


def path_from_player_input(value, for_save=False):
    """Resolve a typed save name or path to a .tasave path."""
    value = value.strip()
    if not value:
        return default_save_path()

    path = Path(value).expanduser()
    if path.parent == Path("."):
        path = SAVE_DIR / sanitize_slot_name(path.name)
    if not path.suffix:
        path = path.with_suffix(SAVE_SUFFIX)
    elif for_save and path.suffix != SAVE_SUFFIX:
        path = path.with_suffix(SAVE_SUFFIX)
    return path


def list_save_files():
    """Return known save files, newest first."""
    if not SAVE_DIR.exists():
        return []
    return sorted(
        SAVE_DIR.glob(f"*{SAVE_SUFFIX}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def make_save_payload(state):
    """Build the plain save payload before encryption."""
    return {
        "game": "Adventure Game",
        "format_version": SAVE_FORMAT_VERSION,
        "saved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "state": state,
    }


def make_save_text(state):
    """Return encrypted save data in the same format as a .tasave file."""
    container = _encrypt_payload(make_save_payload(state))
    return json.dumps(container, sort_keys=True)


def write_save_text(save_text, path):
    """Write already-created encrypted save data to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(save_text, encoding="utf-8")
    return path


def save_game(state, path):
    """Write an encrypted save file and return the final path."""
    return write_save_text(make_save_text(state), path)


def load_game_text(save_text):
    """Load, verify, decrypt, and return a save payload from text."""
    try:
        container = json.loads(save_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SaveError("The save data could not be opened as a save.") from exc
    return _decrypt_payload(container)


def load_game(path):
    """Load, verify, decrypt, and return a save payload."""
    path = Path(path)
    try:
        save_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SaveError(f"No save file exists at {path}.") from exc
    except OSError as exc:
        raise SaveError("The save file could not be opened as a save.") from exc
    return load_game_text(save_text)
