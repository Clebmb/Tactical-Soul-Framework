# REA skill and MCP for framework agents

The user explicitly requests that the handoff direct successor agents to use the
**reverse-engineer-anything (REA) skill and REA MCP** for reverse engineering.
This complements the framework's source, format tests and native mGBA harnesses.

## Verified host status

At the v0.25 handoff, the skill exists locally at:

`%USERPROFILE%/.agents/skills/reverse-engineer-anything/SKILL.md`

It is an agent-level installation, not a skill shipped inside this source
project. It may be absent on another computer. Read the installed skill before
using REA and locate its current version through the receiving agent's skill
catalog; do not assume this absolute path is portable.

At the v0.25 handoff, no REA MCP tools were exposed to that session. A read-only
inspection of the host's Codex config found MCP servers named `node_repl` and
`melty`, with no REA server. No credentials or server arguments were copied. The
skill's diagnostic command, `npx -y rea-agents@latest doctor --client codex
--json`, failed because the package registry hostname could not resolve. That
failure does not prove provider availability or the status of another
client/computer.

At the v0.26 turn, a `reverse-engineer-anything` MCP server **was** connected:
`binary_session` answered `{"open": false}` and its tool list was discoverable.
However, `open_binary` on the exact private GBA ROM failed with
`unsupported binary format`, so no GBA analysis session, decompilation or
Evidence IDs exist. Per the skill, ordinary complete-source-repository work uses
normal repository tools and does not need REA; no host configuration was changed
and no doctor/setup command was run. GBA/ARM-ROM targets remain outside the
connected REA server's supported formats here. Do not label static byte scans or
local mGBA evidence as REA MCP/decompiler evidence.

No REA configuration, provider or host software was installed or changed.
The user requested handoff instructions, not installation. Native evidence for
the current sprite writer comes from direct ROM bytes and the existing local
mGBA harness; do not label it as REA MCP/decompiler evidence.

## Successor workflow

1. Read the REA skill. Use it when investigating the shipped ROM, native routines,
   code/data bindings, runtime behavior or another binary target. Ordinary edits
   to this complete Python source repository use normal repository tools.
2. Prefer connected **REA MCP tools** for binary analysis. Discover their actual
   advertised names/schemas. Use `open_binary` to bind the exact private host for
   active-target operations, then focused references/functions/bytes/evidence.
   Check an existing session with `binary_session` when available; reuse matching
   sessions rather than opening duplicate analysis databases.
3. Tie findings to exact ROM hashes, addresses, search bounds and retained REA
   Evidence IDs when provided. Separate static observations, inferred semantics,
   native execution and unknowns. Never invent tool calls or Evidence IDs.
4. Keep private ROMs, analysis databases, extracted art and native screenshots
   under private locations; never include them in source releases or upload them.
   Use local emulation to verify engine-visible claims before registering writers.
5. If REA MCP is absent, say so in the handoff. Follow the installed skill's
   read-only diagnostics. For a different agent client, use its correct client
   identifier rather than blindly configuring Codex. A configured but disconnected
   server may need reconnection/restart, which cannot be established by a config
   file alone.
6. Configuration repair or provider installation follows the skill's dry-run and
   approval procedure. Do not silently install unrelated software, change user
   configuration or send a private ROM to an external service. Continue independent
   source work and supported local evidence collection while access is unresolved.

REA does not replace the framework's immutable-host gate, conflict ledger,
transactions, resource budgets or native acceptance checks. A recovered function
or pointer does not by itself establish ABI safety or unused runtime resources.

## Current observation and successor tool use (2026-10-12)

REA MCP currently advertises170 tools; binary_session answered open:false.
The Ghidra provider reports GHIDRA_INSTALL_DIR unset and Java runtime missing.
Historical unsupported-GBA admission remains a separate documented boundary;
no new ROM-open attempt or decompiler evidence was produced. No setup changes.
Use all applicable tools by hypothesis and availability, not an indiscriminate
catalog sweep. See handoff.md for Muse Spark1.3 execution expectations, tool
commands and the prioritized tear-projectile/SFX work. Summarize session output
before returning it: the full availability/catalog response is very large.
