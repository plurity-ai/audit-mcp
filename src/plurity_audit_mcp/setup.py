"""Interactive CLI for first-time setup of the Plurity Audit MCP server.

Run with:
    plurity-audit-mcp-setup
"""

from __future__ import annotations

import sys
import textwrap

from .config import _CONFIG_PATH, _DEFAULT_BASE_URL, save_config


_CLAUDE_DESKTOP_EXAMPLE = """\
{
  "mcpServers": {
    "plurity-audit": {
      "command": "uvx",
      "args": ["plurity-audit-mcp"],
      "env": {
        "PLURITY_API_KEY": "plt_your_key_here"
      }
    }
  }
}"""


def main() -> None:
    """Interactive setup wizard."""
    print(
        "\nPlurity GEO Audit MCP — setup\n"
        + "-" * 35
    )
    print(
        "\nStep 1  Go to https://audit.plurity.ai/dashboard/settings "
        "and create an API key.\n"
    )

    try:
        raw = input("Step 2  Paste your API key: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        sys.exit(1)

    if not raw:
        print("No key entered. Setup cancelled.")
        sys.exit(1)

    save_config(api_key=raw, base_url=_DEFAULT_BASE_URL)

    print(f"\nSaved to {_CONFIG_PATH}")
    print("\nStep 3  Add the server to your MCP client.\n")
    print("Claude Desktop — add to ~/Library/Application Support/Claude/claude_desktop_config.json:")
    print()
    for line in _CLAUDE_DESKTOP_EXAMPLE.splitlines():
        print(f"  {line}")
    print()
    print(
        "Alternatively, set the PLURITY_API_KEY environment variable in "
        "your MCP client config instead of using the config file.\n"
    )
    print("Done!")
