# MCP server

fourdmem speaks [Model Context Protocol](https://modelcontextprotocol.io) over **stdio**, the same way:

- `@modelcontextprotocol/server-memory` exposes a knowledge graph
- `agent-memory-mcp` / `mcp-memory-service` expose store / recall / stats locally
- Headroom’s CCR retrieves by hash and **does not rewrite the chat prefix**

Difference: this server has **two kinds**. Default recall is the **plan (good)**. Bad is kept, not tied, not injected.

## Connect (Grok / Claude Desktop / Cursor)

Install the package, then add [examples/mcp.json](../examples/mcp.json):

```json
{
  "mcpServers": {
    "fourdmem": {
      "command": "python",
      "args": ["-m", "fourdmem.agent.mcp"],
      "env": { "FOURDMEM_STORE": ".fourdmem" }
    }
  }
}
```

Windows: use the venv python, e.g. `C:\\Users\\you\\Projects\\4d-memory\\.venv\\Scripts\\python.exe`.

CLI equivalent: `fourdmem mcp` (same stdio server).

## Tools (always registered — never toggled)

| Tool | Role |
| --- | --- |
| `fourdmem_goal` | Set the creating plan |
| `fourdmem_store` | Store a note; auto good/bad vs that plan |
| `fourdmem_judge` | Retie good onto the plan / untie bad |
| `fourdmem_recall` | Default **good only**. `kind=bad` is explicit |
| `fourdmem_cas` | Lossless bytes by oid |
| `fourdmem_status` | Counts |
| `fourdmem_math_verify` | HuggingFace Math-Verify |
| `fourdmem_lean` | Lean 4 REPL |

`tools/listChanged` is **false**. Empty recall does not drop tools.

## Resources

- `fourdmem://status` — JSON status
- `fourdmem://plan` — current good recall (unclouded)

## Prompt

- `work_loop` — set goal, store, recall good, do not rewrite earlier turns

## Live zone

Recall is a **tool result**. The server does not edit system prompts or old turns. See `fourdmem.agent.live_zone`.
