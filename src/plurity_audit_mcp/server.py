"""FastMCP server exposing the Plurity GEO Audit API as MCP tools."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import PlurityAPIError, PlurityClient
from .config import PlurityConfig, get_config

mcp = FastMCP("Plurity Audit")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client() -> PlurityClient:
    """Resolve config and return a configured :class:`PlurityClient`."""
    config: PlurityConfig = get_config()
    return PlurityClient(api_key=config.api_key, base_url=config.base_url)


def _ok(data: Any) -> str:
    """Serialise *data* to a compact JSON string."""
    return json.dumps(data, ensure_ascii=False)


def _err(message: str) -> str:
    """Wrap an error message as a JSON string so the caller gets useful text."""
    return json.dumps({"error": message}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def submit_scan(url: str, webhook_url: str = "") -> str:
    """Submit a URL for GEO audit scanning.

    Queues the URL for a full Playwright crawl followed by AI analysis. The
    scan runs asynchronously; use ``get_scan`` to poll for results or use
    ``audit`` to block until complete.

    Args:
        url: The website URL to audit (e.g. "https://example.com").
        webhook_url: Optional HTTPS URL to be called when the scan finishes.

    Returns:
        JSON string with ``id``, ``scan_result_id``, ``status``, and
        ``cached`` (true if results were already available).
    """
    try:
        with _get_client() as client:
            result = client.submit_scan(url=url, webhook_url=webhook_url)
        return _ok(result)
    except PlurityAPIError as exc:
        return _err(str(exc))
    except RuntimeError as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Unexpected error: {exc}")


@mcp.tool()
def get_scan(scan_id: str) -> str:
    """Get the current status and results of a scan by its ID.

    Args:
        scan_id: The scan ID returned by ``submit_scan`` (the ``id`` field).

    Returns:
        JSON string with ``id``, ``scan_result_id``, ``url``, ``status``,
        ``overall_score`` (0-100 or null), ``analysis`` (object or null),
        ``error`` (string or null), ``submitted_at``, and ``updated_at``.
        Status is one of: ``pending``, ``crawling``, ``analyzing``,
        ``complete``, ``failed``.
    """
    try:
        with _get_client() as client:
            result = client.get_scan(scan_id=scan_id)
        return _ok(result)
    except PlurityAPIError as exc:
        return _err(str(exc))
    except RuntimeError as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Unexpected error: {exc}")


@mcp.tool()
def get_scan_by_url(url: str) -> str:
    """Look up the latest scan result for a given URL.

    Useful for checking whether a site has been scanned before without
    knowing the scan ID.

    Args:
        url: The website URL to look up (e.g. "https://example.com").

    Returns:
        JSON string with the same shape as ``get_scan``, or an error object
        if no scan exists for the URL.
    """
    try:
        with _get_client() as client:
            result = client.get_scan_by_url(url=url)
        return _ok(result)
    except PlurityAPIError as exc:
        return _err(str(exc))
    except RuntimeError as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Unexpected error: {exc}")


@mcp.tool()
def audit(url: str, timeout_seconds: int = 300) -> str:
    """Submit a URL for a full GEO audit and wait until it is complete.

    Submits the URL for scanning and blocks, polling every 5 seconds until
    the scan reaches a terminal state (``complete`` or ``failed``) or the
    timeout is exceeded. If the URL was already scanned recently the cached
    result is returned immediately.

    Args:
        url: The website URL to audit (e.g. "https://example.com").
        timeout_seconds: Maximum time to wait in seconds (default 300 / 5 min).

    Returns:
        JSON string with the full scan result including ``overall_score`` and
        ``analysis`` when complete. If the timeout is exceeded the last known
        status is returned (check ``status`` field — it may not be
        ``complete``).
    """
    if timeout_seconds < 1:
        return _err("timeout_seconds must be at least 1.")
    if timeout_seconds > 900:
        return _err("timeout_seconds must not exceed 900 (15 minutes).")

    try:
        with _get_client() as client:
            submitted = client.submit_scan(url=url)

            # If the scan is already in a terminal state, return immediately.
            status = submitted.get("status", "")
            if status in {"complete", "failed"}:
                return _ok(submitted)

            scan_id: str = submitted.get("id", "")
            if not scan_id:
                return _err("API did not return a scan ID.")

            result = client.wait_for_scan(
                scan_id=scan_id,
                timeout_seconds=timeout_seconds,
            )

        return _ok(result)
    except PlurityAPIError as exc:
        return _err(str(exc))
    except RuntimeError as exc:
        return _err(str(exc))
    except Exception as exc:
        return _err(f"Unexpected error: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server (stdio transport by default)."""
    mcp.run()
