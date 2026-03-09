"""Configuration loading for the Plurity Audit MCP server.

Reads from (in priority order):
1. Environment variable ``PLURITY_API_KEY`` / ``PLURITY_BASE_URL``
2. ``~/.config/plurity/config.toml`` under the ``[audit]`` section
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass

_CONFIG_PATH = Path.home() / ".config" / "plurity" / "config.toml"
_DEFAULT_BASE_URL = "https://audit.plurity.ai"


@dataclass(frozen=True, slots=True)
class PlurityConfig:
    """Resolved configuration for the Plurity API client."""

    api_key: str
    base_url: str


def _load_toml() -> dict:
    """Load ``~/.config/plurity/config.toml`` if it exists."""
    if not _CONFIG_PATH.exists():
        return {}
    with _CONFIG_PATH.open("rb") as fh:
        return tomllib.load(fh)


def get_config() -> PlurityConfig:
    """Return resolved :class:`PlurityConfig`.

    Resolution order:
    - ``PLURITY_API_KEY`` env var (highest priority)
    - ``~/.config/plurity/config.toml`` ``[audit]`` section
    - Raises :class:`RuntimeError` if no API key is found.
    """
    import os

    env_key = os.environ.get("PLURITY_API_KEY", "").strip()
    env_url = os.environ.get("PLURITY_BASE_URL", "").strip()

    toml_data = _load_toml()
    audit_section: dict = toml_data.get("audit", {})

    api_key = env_key or audit_section.get("api_key", "").strip()
    base_url = (
        env_url
        or audit_section.get("base_url", "").strip()
        or _DEFAULT_BASE_URL
    ).rstrip("/")

    if not api_key:
        raise RuntimeError(
            "No Plurity API key found. Set the PLURITY_API_KEY environment variable "
            "or run 'plurity-audit-mcp-setup' to save a key to "
            f"{_CONFIG_PATH}."
        )

    return PlurityConfig(api_key=api_key, base_url=base_url)


def save_config(api_key: str, base_url: str = _DEFAULT_BASE_URL) -> None:
    """Persist ``api_key`` and ``base_url`` to ``~/.config/plurity/config.toml``."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read existing file so we do not clobber unrelated sections.
    existing: dict = {}
    if _CONFIG_PATH.exists():
        with _CONFIG_PATH.open("rb") as fh:
            existing = tomllib.load(fh)

    existing.setdefault("audit", {})
    existing["audit"]["api_key"] = api_key
    existing["audit"]["base_url"] = base_url

    # tomllib is read-only; write manually with a minimal TOML serialiser.
    lines: list[str] = []
    for section, values in existing.items():
        lines.append(f"[{section}]")
        for k, v in values.items():
            lines.append(f'{k} = "{v}"')
        lines.append("")

    _CONFIG_PATH.write_text("\n".join(lines), encoding="utf-8")
