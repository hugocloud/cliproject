# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

Requires `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` set in `.env`.

```bash
# With uv (recommended)
uv run main.py

# With plain Python
python main.py
```

Pass additional MCP server scripts as positional arguments to connect extra clients:

```bash
uv run main.py my_other_server.py
```

## Setup

```bash
uv venv
.venv\Scripts\activate   # Windows
uv pip install -e .
```

## Architecture

The app is an async CLI chat client that connects Claude to one or more MCP servers over stdio.

**Startup flow (`main.py`):**
1. Instantiates `Claude` (wraps the Anthropic SDK).
2. Spawns `mcp_server.py` as a subprocess and wraps it in an `MCPClient` (the "doc client").
3. Any additional server scripts passed as CLI args each get their own `MCPClient`.
4. Builds `CliChat` (the agent logic) and `CliApp` (the prompt-toolkit UI), then runs the REPL.

**Layer responsibilities:**

| File | Role |
|---|---|
| `mcp_server.py` | FastMCP server — owns the `docs` dict, exposes tools, resources, and prompts over stdio |
| `mcp_client.py` | Async context manager that connects to an MCP server via stdio and exposes typed methods (`list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `read_resource`) |
| `core/claude.py` | Thin wrapper around `anthropic.Anthropic` — stateless, handles `chat()` with optional tools/thinking |
| `core/chat.py` | Base `Chat` class — holds the `messages` list, drives the tool-use loop (send → check `stop_reason` → execute tools → repeat) |
| `core/cli_chat.py` | `CliChat(Chat)` — overrides `_process_query` to handle `@doc` resource injection and `/command` prompt dispatch before calling Claude |
| `core/tools.py` | `ToolManager` — aggregates tools from all connected clients, routes `tool_use` blocks to the right client |
| `core/cli.py` | `CliApp` — prompt-toolkit REPL with tab-completion for `/commands` and `@resources`, driven by `CliChat` |

**Key data flows:**

- `@mention` in input → `CliChat._extract_resources` fetches doc content via `docs://documents/{doc_id}` resource → injected as `<document>` XML in the user message.
- `/command arg` in input → `CliChat._process_command` calls `get_prompt(command, {doc_id: arg})` on the doc client → resulting `PromptMessage` list appended to `self.messages` (no immediate Claude call; the next `chat()` in `Chat.run` sends them).
- Tool use → `ToolManager.execute_tool_requests` searches all connected clients for the matching tool name and calls it.

**Adding documents:** Edit the `docs` dict in `mcp_server.py`.

**Adding MCP features:** Add tools/resources/prompts in `mcp_server.py` using the `@mcp.tool`, `@mcp.resource`, and `@mcp.prompt` decorators.

**Adding a new MCP server:** Pass its script path as a CLI argument to `main.py`; it will be auto-connected and its tools made available to Claude.

## Business Rules
- Car insurance quote flow is restricted to car queries only (no home/life)
- All MCP prompts must sanitize user input with XML tags
