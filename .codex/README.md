# Codex setup for this repo

This repo was set up to work with **OpenAI Codex** (the `codex` CLI agent) alongside Claude Code.
Nothing here is consumed by the deployed site — it's agent configuration only.

## What's here

- **`AGENTS.md`** (repo root) — Codex's project guide. Codex reads `AGENTS.md` automatically (root +
  nested dirs) the same way Claude Code reads `CLAUDE.md`. The two files mirror each other; keep them
  in sync when project facts change.
- **`.codex/prompts/`** — ports of the Claude Code skills as Codex custom prompts:
  - `new-case.md` → `/new-case`
  - `check-blob.md` → `/check-blob`

## One-time local setup (per machine)

1. **Install Codex:** `npm i -g @openai/codex` (or `brew install codex`), then run `codex` and sign
   in (ChatGPT login or API key).

2. **Enable the custom prompts** — Codex loads prompts from `~/.codex/prompts/`, so copy or symlink
   them from this repo:
   ```sh
   mkdir -p ~/.codex/prompts
   ln -sf "$PWD/.codex/prompts/new-case.md"   ~/.codex/prompts/new-case.md
   ln -sf "$PWD/.codex/prompts/check-blob.md" ~/.codex/prompts/check-blob.md
   ```
   Then `/new-case` and `/check-blob` are available inside Codex.

3. **MCP servers** (GitHub, etc.) — configure in `~/.codex/config.toml` under `[mcp_servers]`. Codex
   uses TOML, not Claude Code's JSON. Example:
   ```toml
   [mcp_servers.github]
   command = "npx"
   args = ["-y", "@modelcontextprotocol/server-github"]
   ```

## Not carried over from Claude Code

- **The pre-push guard.** Claude Code blocked pushes via a `.claude/settings.json` hook
  (`.claude/hooks/prepush-guard.mjs`). Codex has no hook system. Install it as a real git hook so it's
  agent-independent:
  ```sh
  printf '#!/bin/sh\nnode scripts/check-allowlists.mjs && node build-trainer.mjs --out && rm -f trainer.min.html clerk-auth.min.js\n' \
    > .git/hooks/pre-push && chmod +x .git/hooks/pre-push
  ```

Claude Code still works unchanged — `CLAUDE.md` and `.claude/` are untouched, and both agents can use
this repo.
