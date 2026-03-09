# plurity-audit-mcp

MCP server for the [Plurity GEO Audit API](https://audit.plurity.ai). Lets any MCP-compatible AI client (Claude Desktop, Cursor, etc.) submit websites for AI-readiness audits and retrieve the full analysis — score, structured Q&A pairs, token-waste insights — directly inside the conversation.

---

## Setup

### 1. Get an API key

Sign up at [audit.plurity.ai](https://audit.plurity.ai), then go to **Settings → API Keys** and create a key. Copy the `plt_...` key — it is only shown once.

### 2. Add to your MCP client

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
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
}
```

Restart Claude Desktop after saving.

#### Other MCP clients

Same config shape — set `PLURITY_API_KEY` in the `env` block and use `uvx plurity-audit-mcp` as the command.

> **Requires [`uv`](https://docs.astral.sh/uv/)** — install with `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.

---

## Available tools

| Tool | Description |
|---|---|
| `submit_scan(url)` | Queue a URL for GEO audit. Returns scan ID and initial status immediately. |
| `get_scan(scan_id)` | Get the current status and results of a scan by ID. |
| `get_scan_by_url(url)` | Look up the latest scan result for a URL without knowing the scan ID. |
| `audit(url, timeout_seconds?)` | Submit and **block until complete** (polls every 5 s, default 5 min timeout). Returns full results. |

Scan statuses: `pending` → `crawling` → `analyzing` → `complete` (or `failed`).

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `PLURITY_API_KEY` | Yes | Your Plurity API key (`plt_...`) |
| `PLURITY_BASE_URL` | No | Override API base URL (default: `https://audit.plurity.ai`) |
