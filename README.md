# skill-meta

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange?style=flat-square)](#)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](#verify)
[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

**Discover and load local Agent Skills on demand** — a zero-dependency Python CLI + MCP server that unifies skill catalogs from DSH, Claude, Codex, and Magpie behind one lazy-loading facade. No skill summaries baked into your system prompt; search when needed, load what you use.

Part of the meta-tool family: pair it with [mcp-meta](https://github.com/monkey-sking/mcp-meta) (MCP lazy facade, 2 tools for N servers) — skill-meta does the same for **skills** (3 tools for N skill directories).

## Why

Agent harnesses inject full skill catalogs into every turn. With 70+ skills that is thousands of tokens of descriptions repeated in every request, whether or not any skill is used. skill-meta collapses that to three small tool schemas (~1.1K chars) and loads full instructions only when a task actually needs them.

| | Full catalog injection | skill-meta facade |
|---|---|---|
| System-prompt cost | grows with skill count (74 skills on this machine) | 3 tool schemas, constant |
| Loading | preloaded | `skill_search` → `skill_load`, on demand |
| Sources | one host per catalog | DSH + Claude + Codex + Magpie + shared agents, deduplicated |

## Install

Requires Python 3.9+ (standard library only).

```sh
git clone https://github.com/monkey-sking/skill-meta.git
cd skill-meta
python3 -m pip install .
```

Or without installing:

```sh
PYTHONPATH=src python3 -m skill_meta list
```

## CLI

```sh
skill-meta list                 # unified catalog across all host skill dirs
skill-meta list --json          # machine-readable
skill-meta search "ios design"  # keyword search, top 8
skill-meta search "lark 会议" --limit 3
skill-meta show ios-design      # print full SKILL.md content
skill-meta serve                # run the stdio MCP server
```

## MCP

Register `skill-meta serve` as a stdio server in any MCP-capable host:

| Tool | Params | Returns |
|---|---|---|
| `skill_search` | `query` (required), `limit` (default 8) | matched skill names + one-line summaries |
| `skill_load` | `name` (required) | full SKILL.md content + local path (for adjacent resources) |
| `skill_list` | `pattern` (optional) | all skills, filtered by name/description substring |

### DSH (cordis patch)

```yaml
- id: magpie-mcp-skill-meta
  command: python3
  args: [/path/to/skill-meta/venv/bin/skill-meta, serve]
  agents: [dsh]
```

### Claude Code (~/.claude.json) / Codex (~/.codex/config.toml)

```json
{ "mcpServers": { "skill-meta": { "command": "skill-meta", "args": ["serve"] } } }
```

```toml
[mcp_servers.skill-meta]
command = "skill-meta"
args = ["serve"]
```

## How discovery works

The catalog scans these directories in order (first hit wins on duplicate folder names):

1. `~/.config/magpie/library/skills` — Magpie shared library
2. `~/.dsh/skills` — DeepSeek Harness
3. `~/.claude/skills` — Claude Code
4. `~/.codex/skills` — Codex CLI
5. `~/.agents/skills` — cross-agent shared

Each skill is a directory containing `SKILL.md` with `name`/`description` frontmatter. `skill_load` returns the local path so agents can resolve bundled `references/`, `scripts/`, and `assets/` next to the skill. No skills, personal content, credentials, or machine-specific paths are bundled in this repo.

## Current limitations

- **Search is keyword matching, not semantic retrieval.** Whitespace-token scoring over name + description; Chinese phrase recall can be poor.
- **Frontmatter parser is minimal.** Simple one-line values only; YAML folded/literal descriptions can surface as `>` or `>-`.
- **Catalog is cached until server restart**; newly installed skills need a restart (or CLI re-run) to appear.
- **JSON-RPC handling is minimal.** Notifications, invalid arguments, and missing skills need stronger protocol handling; missing skills return text without `isError`.
- **No measured end-to-end token-savings claim.** Small schemas do not by themselves prove lower total task cost.
- `serverInfo` reports legacy version `1.0.0`; the package starts at `0.1.0` (kept for compatibility review).

## Verify

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Roadmap

1. Correct YAML frontmatter parsing (folded/literal blocks, quoted colons) — highest priority
2. Protocol hardening: argument validation, `isError` on failures, notification handling
3. Catalog refresh + configurable roots
4. Retrieval-quality measurement (zh/en) before considering an embedding dependency
5. Optional: adopt [OpenSkills](https://github.com/numman-ali/openskills) / [Vercel skills](https://github.com/vercel-labs/skills) for install/update/distribution instead of building our own

See [docs/comparison.md](docs/comparison.md) for the full alternatives analysis and proposed improvements.

## License

MIT — see [LICENSE](LICENSE).

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)
