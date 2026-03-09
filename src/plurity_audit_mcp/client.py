"""Synchronous httpx client for the Plurity GEO Audit API.

All methods return plain dicts on success and raise :class:`PlurityAPIError`
on HTTP or network errors. The MCP tool layer catches those and converts them
to user-friendly strings.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

_DEFAULT_TIMEOUT = 30.0  # seconds


class PlurityAPIError(Exception):
    """Raised when the Plurity API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class PlurityClient:
    """Thin synchronous wrapper around the Plurity Audit REST API.

    Args:
        api_key: Bearer token for authentication.
        base_url: Root URL of the API (no trailing slash).
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://audit.plurity.ai",
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Convert non-2xx responses into :class:`PlurityAPIError`."""
        if response.is_success:
            return
        try:
            body = response.json()
            detail = body.get("error") or body.get("message") or body.get("detail", "")
        except Exception:
            detail = response.text or "(no body)"
        raise PlurityAPIError(
            f"API error {response.status_code}: {detail}",
            status_code=response.status_code,
        )

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        response = self._client.get(path, params={k: v for k, v in params.items() if v is not None})
        self._raise_for_status(response)
        return response.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(path, json=body)
        self._raise_for_status(response)
        return response.json()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def submit_scan(
        self, url: str, webhook_url: str = ""
    ) -> dict[str, Any]:
        """Submit a URL for GEO audit scanning.

        Args:
            url: The website URL to scan.
            webhook_url: Optional callback URL notified when the scan completes.

        Returns:
            Dict with keys ``id``, ``scan_result_id``, ``status``, ``cached``.
        """
        body: dict[str, Any] = {"url": url}
        if webhook_url:
            body["webhook_url"] = webhook_url
        return self._post("/api/v1/scans", body)

    def get_scan(self, scan_id: str) -> dict[str, Any]:
        """Fetch the current status and results for a scan by its ID.

        Args:
            scan_id: The agency-scan ID returned by :meth:`submit_scan`.

        Returns:
            Dict with keys ``id``, ``scan_result_id``, ``url``, ``status``,
            ``overall_score``, ``analysis``, ``error``, ``submitted_at``,
            ``updated_at``.
        """
        return self._get(f"/api/v1/scans/{scan_id}")

    def get_scan_by_url(self, url: str) -> dict[str, Any]:
        """Look up the latest scan for a given URL.

        Args:
            url: The website URL to look up.

        Returns:
            Same shape as :meth:`get_scan`.
        """
        return self._get("/api/v1/scans", url=url)

    def wait_for_scan(
        self,
        scan_id: str,
        timeout_seconds: int = 300,
        poll_interval: float = 5.0,
    ) -> dict[str, Any]:
        """Poll until the scan reaches a terminal state or the timeout expires.

        Terminal states are ``complete`` and ``failed``.

        Args:
            scan_id: The agency-scan ID to poll.
            timeout_seconds: Maximum wall-clock seconds to wait.
            poll_interval: Seconds between polling requests.

        Returns:
            The last scan dict returned by the API.
        """
        _TERMINAL = {"complete", "failed"}
        deadline = time.monotonic() + timeout_seconds
        last: dict[str, Any] = {}

        while time.monotonic() < deadline:
            last = self.get_scan(scan_id)
            if last.get("status") in _TERMINAL:
                return last
            remaining = deadline - time.monotonic()
            time.sleep(min(poll_interval, max(remaining, 0)))

        return last

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "PlurityClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
