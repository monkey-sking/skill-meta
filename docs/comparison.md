# Alternatives and improvement plan

Checked 2026-11-11. Repository README and API metadata inspected; alternatives were not installed or benchmarked in this round.

| Project | Role and verified features | License / maintenance evidence | Implication |
|---|---|---|---|
| [OpenSkills](https://github.com/numman-ali/openskills) | TypeScript CLI; install/sync/read/update; puts minimal skill catalog into AGENTS.md; read output supplies resource base directory | README says Apache-2.0; API reports NOASSERTION, so inspect LICENSE before reuse. pushed_at 2026-01-18T13:09:50Z | Strong substitute for installation and cross-agent distribution; do not rebuild these features |
| [Vercel skills](https://github.com/vercel-labs/skills) | Node CLI; find/add/use/check/update; many host adapters; content hash lockfile; use without installation | MIT; pushed_at 2026-11-10T23:59:16Z | Prefer existing installer and locking over writing a marketplace or host manager |
| [Anthropic skills](https://github.com/anthropics/skills) | Examples and SKILL.md conventions, scripts/references/assets adjacent to instructions; links to agentskills.io | README says many skills Apache-2.0; root API license null, verify per skill. pushed_at 2026-11-06T22:32:32Z | Follow format and resource locality; this is a reference catalog rather than a replacement search service |

## Decision

Preserve the small local loader as a project because it offers a standard-library CLI and MCP interface over existing directories. Do not build a new installer, marketplace, or automatic cross-host writer. Evaluate OpenSkills/Vercel skills if distribution becomes necessary. No third-party code has been copied.

## Priorities before wider use

1. **Correctness first:** parse folded/literal YAML descriptions; currently agent-desktop yields `>` and egm-review yields `>-`. Choose a maintained YAML parser versus a deliberately limited parser before implementation. Add regression cases for quoted colons, multiline descriptions and malformed metadata.
2. **Protocol reliability:** validate query/limit/name types; bound limits; omit responses to notifications; return isError on failed loads; ensure a bad request cannot kill the server. Test a valid request immediately after a malformed call.
3. **Discovery quality:** label search as keyword search, show duplicate source precedence, add refresh and configurable roots. Measure Chinese and English retrieval on a small labeled real-task set before buying an embedding dependency.
4. **Bounded resources:** return base directory and offer safe reference reads/pagination if host tools cannot read adjacent resources. Keep full instructions recoverable.
5. **Measure end-to-end:** compare task completion, total model input, discovery turns and failure recovery against native DSH skills. Three small schemas alone do not establish token savings. DSH still injects its native catalog; this standalone program does not suppress that catalog.

These are proposed changes, not shipped behavior. Live installation and observation settings remain unchanged.
