#!/usr/bin/env python3
"""skill-meta: Unified lazy tool and CLI for Agent Skills across DSH, Codex, and Claude.

Provides:
- CLI:
    skill-meta list [--json]
    skill-meta search <query> [--limit N]
    skill-meta show <name>
    skill-meta serve (Runs stdio MCP server for mcp-meta / Magpie)
- MCP Tools exposed when running as MCP:
    - skill_search({ query: string, limit?: number })
    - skill_load({ name: string })
    - skill_list({ pattern?: string })
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

SKILL_DIRS = [
    os.path.expanduser("~/.config/magpie/library/skills"),
    os.path.expanduser("~/.dsh/skills"),
    os.path.expanduser("~/.claude/skills"),
    os.path.expanduser("~/.codex/skills"),
    os.path.expanduser("~/.agents/skills"),
]


def extract_frontmatter(content: str) -> tuple[Dict[str, str], str]:
    meta: Dict[str, str] = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1]
            body = parts[2].strip()
            for line in raw_meta.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    meta[k] = v
    return meta, body


class SkillCatalog:
    def __init__(self, dirs: Optional[List[str]] = None):
        self.dirs = dirs or SKILL_DIRS
        self._skills: Optional[Dict[str, Dict[str, Any]]] = None

    def load(self, force: bool = False) -> Dict[str, Dict[str, Any]]:
        if self._skills is not None and not force:
            return self._skills

        skills: Dict[str, Dict[str, Any]] = {}
        for d in self.dirs:
            if not os.path.isdir(d):
                continue
            try:
                entries = sorted(os.listdir(d))
            except Exception:
                continue

            for name in entries:
                if name.startswith(".") or name in skills:
                    continue
                skill_dir = os.path.join(d, name)
                skill_file = os.path.join(skill_dir, "SKILL.md")
                if not os.path.isfile(skill_file):
                    continue

                try:
                    with open(skill_file, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    continue

                meta, _ = extract_frontmatter(text)
                desc = meta.get("description", "")
                if not desc:
                    lines = [ln.strip() for ln in text.split("\n") if ln.strip() and not ln.startswith("#") and not ln.startswith("---")]
                    desc = lines[0] if lines else ""

                skills[name] = {
                    "name": name,
                    "description": desc,
                    "path": skill_file,
                    "dir": skill_dir,
                    "size_bytes": len(text),
                }

        self._skills = skills
        return skills

    def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        catalog = self.load()
        q_tokens = [tok.lower() for tok in re.split(r"\s+", query) if tok]
        if not q_tokens:
            return list(catalog.values())[:limit]

        scored = []
        for name, item in catalog.items():
            name_lower = name.lower()
            desc_lower = item["description"].lower()
            score = 0

            for tok in q_tokens:
                if tok == name_lower:
                    score += 100
                elif tok in name_lower:
                    score += 40
                if tok in desc_lower:
                    score += 15

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def get_skill_content(self, name: str) -> Optional[Dict[str, Any]]:
        catalog = self.load()
        if name not in catalog:
            return None
        item = catalog[name]
        try:
            with open(item["path"], "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Failed to read skill {name}: {str(e)}"}

        meta, body = extract_frontmatter(content)
        return {
            "name": name,
            "description": item["description"],
            "path": item["path"],
            "meta": meta,
            "content": content,
        }


# --- MCP Server JSON-RPC Protocol (Stdio) ---

MCP_TOOLS = [
    {
        "name": "skill_search",
        "description": "Search local Agent Skills catalog by natural language keywords or task description. Returns matched skill names and concise summaries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or task description (e.g. 'iOS release', 'animation', 'lark')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of matched skills to return (default: 8)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "skill_load",
        "description": "Load full instructions and specification of a specific Agent Skill on demand. Use after identifying the relevant skill via skill_search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Exact name of the skill (e.g. 'ios-design', 'delivery-gates')",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "skill_list",
        "description": "List all registered agent skills with their concise one-line descriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Optional substring pattern to filter names",
                },
            },
        },
    },
]


def run_mcp_server():
    catalog = SkillCatalog()
    catalog.load()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "skill-meta", "version": "1.0.0"},
                },
            }
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": MCP_TOOLS},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})

            if tool_name == "skill_search":
                q = args.get("query", "")
                limit = int(args.get("limit", 8))
                results = catalog.search(q, limit=limit)
                out = [f"Found {len(results)} skills matching '{q}':\n"]
                for r in results:
                    out.append(f"- **{r['name']}**: {r['description']}")
                text_res = "\n".join(out)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": text_res}]},
                }
            elif tool_name == "skill_load":
                name = args.get("name", "")
                res = catalog.get_skill_content(name)
                if not res:
                    text_res = f"Error: Skill '{name}' not found."
                elif "error" in res:
                    text_res = res["error"]
                else:
                    text_res = f"# Skill: {name}\nPath: {res['path']}\n\n{res['content']}"
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": text_res}]},
                }
            elif tool_name == "skill_list":
                pattern = args.get("pattern", "").lower()
                all_s = catalog.load()
                matched = [v for k, v in all_s.items() if not pattern or pattern in k.lower() or pattern in v["description"].lower()]
                out = [f"Total {len(matched)} skills available on machine:\n"]
                for m in matched:
                    out.append(f"- `{m['name']}`: {m['description'][:100]}")
                text_res = "\n".join(out)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": text_res}]},
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {tool_name}"},
                }
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unsupported method: {method}"},
            }

        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(prog="skill-meta", description="Unified Skill Lazy Loading & Discovery Engine")
    subparsers = parser.add_subparsers(dest="command")

    # list
    p_list = subparsers.add_parser("list", help="List all discovered skills across hosts")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")

    # search
    p_search = subparsers.add_parser("search", help="Search skills by query")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=8, help="Max results")

    # show
    p_show = subparsers.add_parser("show", help="Show full content of a skill")
    p_show.add_argument("name", help="Skill name")

    # serve
    p_serve = subparsers.add_parser("serve", help="Run stdio MCP server")

    args = parser.parse_args()

    catalog = SkillCatalog()

    if args.command == "serve":
        run_mcp_server()
    elif args.command == "search":
        res = catalog.search(args.query, limit=args.limit)
        print(f"Matched {len(res)} skills for '{args.query}':\n")
        for r in res:
            print(f"- {r['name']}")
            print(f"    {r['description']}\n")
    elif args.command == "show":
        res = catalog.get_skill_content(args.name)
        if not res:
            print(f"Error: Skill '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
        print(res["content"])
    elif args.command == "list":
        res = catalog.load()
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"Unified Skills Catalog ({len(res)} skills found):")
            for k, v in sorted(res.items()):
                print(f"  • {k:<30} {v['description'][:70]}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
