"""Optional cloud save API client.

The game always keeps local .tasave files. This module only syncs those same
encrypted save strings to the Adventure Game web API.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import urllib.error
import urllib.parse
import urllib.request

from .save_system import sanitize_slot_name


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_DIR = PROJECT_ROOT / "settings"
SETTINGS_PATH = SETTINGS_DIR / "cloud.json"
DEFAULT_API_URL = "https://lordfunion.dev/adventure-api"
DEFAULT_TIMEOUT = 6


class CloudSaveError(Exception):
    """Raised when the cloud save API cannot complete a request."""


def _load_settings():
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_settings(settings):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


def normalize_api_url(api_url):
    """Return a clean API URL or raise CloudSaveError."""
    api_url = " ".join(api_url.strip().split())
    if not api_url:
        raise CloudSaveError("Cloud save API URL cannot be empty.")
    if "://" not in api_url:
        api_url = f"https://{api_url}"

    parsed = urllib.parse.urlparse(api_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise CloudSaveError("Cloud save API URL must look like https://example.com/adventure-api.")
    return api_url.rstrip("/")


def current_api_url():
    """Return the cloud API URL, with an environment override for testing."""
    env_url = os.getenv("ADVENTURE_API_URL", "").strip()
    if env_url:
        return normalize_api_url(env_url)
    return DEFAULT_API_URL


def current_username():
    """Return the signed-in username, if one is saved."""
    return _load_settings().get("username", "").strip()


def is_signed_in():
    """Return True when a local cloud session token is available."""
    settings = _load_settings()
    return bool(settings.get("token") and settings.get("username"))


def sign_out():
    """Forget the local cloud session token."""
    settings = _load_settings()
    settings.pop("token", None)
    settings.pop("username", None)
    _save_settings(settings)


def normalize_slot_name(value):
    """Return a server-safe cloud save slot name."""
    slot_name = sanitize_slot_name(value)[:64].strip()
    return slot_name or "autosave"


def _endpoint(api_url, action):
    parsed = urllib.parse.urlparse(api_url)
    path = parsed.path
    if not path.endswith(".php"):
        path = f"{path.rstrip('/')}/index.php"
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query["action"] = action
    return urllib.parse.urlunparse(
        parsed._replace(path=path, query=urllib.parse.urlencode(query))
    )


def _read_error_body(error):
    try:
        body = error.read().decode("utf-8")
    except OSError:
        return ""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()
    if isinstance(data, dict):
        return str(data.get("error") or data.get("message") or "").strip()
    return ""


def _decode_json_response(raw_body):
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CloudSaveError("Cloud save server returned a response the game could not read.") from exc

    if not isinstance(data, dict):
        raise CloudSaveError("Cloud save server returned an invalid response.")
    if not data.get("ok"):
        raise CloudSaveError(str(data.get("error") or "Cloud save request failed."))
    return data


def _request(action, data=None, token=None, timeout=DEFAULT_TIMEOUT):
    api_url = current_api_url()

    payload = dict(data or {})
    payload["action"] = action
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "AdventureGame/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        payload["token"] = token

    request = urllib.request.Request(
        _endpoint(api_url, action),
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _decode_json_response(response.read())
    except urllib.error.HTTPError as exc:
        message = _read_error_body(exc)
        if not message:
            message = f"Cloud save server returned HTTP {exc.code}."
        raise CloudSaveError(message) from exc
    except (TimeoutError, socket.timeout, urllib.error.URLError, OSError) as exc:
        raise CloudSaveError("Cloud save server is unavailable. Local saves still work.") from exc


def _session_token():
    token = _load_settings().get("token", "").strip()
    if not token:
        raise CloudSaveError("You are not signed in to cloud saves.")
    return token


def _save_session(username, token):
    settings = _load_settings()
    settings["username"] = username
    settings["token"] = token
    _save_settings(settings)


def register(username, password):
    """Create a cloud save account and remember the session token."""
    response = _request("register", {"username": username, "password": password})
    _save_session(response["username"], response["token"])
    return response


def login(username, password):
    """Sign in to cloud saves and remember the session token."""
    response = _request("login", {"username": username, "password": password})
    _save_session(response["username"], response["token"])
    return response


def list_saves():
    """Return cloud save slots for the signed-in player."""
    return _request("list", token=_session_token()).get("saves", [])


def upload_save(slot_name, save_text, timeout=DEFAULT_TIMEOUT):
    """Upload encrypted save text to a cloud slot."""
    slot_name = normalize_slot_name(slot_name)
    return _request(
        "upload",
        {"slot_name": slot_name, "save_data": save_text},
        token=_session_token(),
        timeout=timeout,
    )


def download_save(slot_name):
    """Download encrypted save text from a cloud slot."""
    slot_name = normalize_slot_name(slot_name)
    response = _request("download", {"slot_name": slot_name}, token=_session_token())
    save_text = response.get("save_data")
    if not isinstance(save_text, str) or not save_text:
        raise CloudSaveError("Cloud save server did not return save data.")
    return response


def check_health():
    """Ask the API whether it is reachable."""
    return _request("health")
