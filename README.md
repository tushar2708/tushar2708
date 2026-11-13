<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/banner-light.svg">
  <img src="./assets/banner-light.svg" width="100%" alt="Portrait banner for Tushar Dwivedi, founder and hands-on staff engineer.">
</picture>

## GitHub field notes

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/stats-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/stats-light.svg">
  <img src="./assets/stats-light.svg" width="100%" alt="GitHub statistics and repository language mix for Tushar Dwivedi.">
</picture>

<sub>Refreshed daily from GitHub’s API. Metrics requiring organisation-level access remain visibly unavailable until the profile statistics token is configured.</sub>

## Relationship tree

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/topology-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/topology-light.svg">
  <img src="./assets/topology-light.svg" width="100%" alt="A theme-first relationship tree connecting Tushar Dwivedi to AI memory, runtime systems, and developer tooling.">
</picture>

## Find me

- **Essays, experiments, and direct contact** —
  **[tushardwivedi.com](https://tushardwivedi.com/)**
- **Professional history and engineering network** —
  **[LinkedIn](https://www.linkedin.com/in/tushar-dwivedi/)**
- **Systems software from the workbench** —
  **[bytonomics.com](https://bytonomics.com/)**
- **Deep dives into durable memory** —
  **[Smritea Blog](https://blog.smritea.ai/)**
- **Developer essays in the open** —
  **[DEV Community](https://dev.to/tushar_bytonomics)**

## Systems behind the tree

### AI memory

- **Memory APIs across five languages** —
  **[SmrutAI/smritea-sdk](https://github.com/SmrutAI/smritea-sdk)** gives applications one SDK surface for durable AI memory in Python, TypeScript, Go, Java, and C# to be used with Smritea.ai.


### Utility libraries:

- **Typed validation for structured outputs** —
  **[SmrutAI/pedantigo](https://github.com/SmrutAI/pedantigo)** brings Go validation and JSON Schema generation to APIs, tools, and streamed LLM output.
- **Caching with explicit failure semantics (Takes care of many caching gotchas)** —
  **[Bytonomics/smartcache](https://github.com/Bytonomics/smartcache)** provides stampede protection, negative caching, telemetry, and pluggable Go backends.
- **Concurrent pipelines with a bunch of plumbing** —
  **[tushar2708/conveyor](https://github.com/tushar2708/conveyor)** is a Go pipeline library for coordinated nodes, joints, and execution paths.
  - **Incremental pipelines for messy knowledge** (WIP) —
  **[SmrutAI/databridge](https://github.com/SmrutAI/databridge)** parses, deduplicates, chunks, and embeds data across local and cloud sources.

### Developer tooling I have created to make my life easier:

- **A task board inside Claude Code** —
  **[Bytonomics/kangaroo](https://github.com/Bytonomics/kangaroo)** turns agent work into a usable, local project board. Look into the soul of Claude Code tasks.
- **Conversation state behind compatible APIs** —
  **[Bytonomics/cld-gateway](https://github.com/Bytonomics/cld-gateway)** is an Anthropic-compatible gateway for Codex-backed development workflows. Free your Claude Code workflows of the Anthropic subscription lock-in.
- **Moving agent workflows into OpenCode** —
  **[SmrutAI/opencode-migration](https://github.com/SmrutAI/opencode-migration)** carries a deliberate migration path for tools, context, and habits.
- **Portable workflows for coding agents** —
  **[tushar2708/claude-assets](https://github.com/tushar2708/claude-assets)** packages reusable skills, plugins, and workflows for Claude Code and Codex.

## What I am upto?

### Build

<!-- PROFILE:BUILD:START -->
<table>
  <tr>
    <td width="180" valign="top"><strong>Bytonomics/cld-gateway</strong><br><sub>Released 2026-09-05</sub></td>
    <td valign="top"><a href="https://github.com/Bytonomics/cld-gateway/releases/tag/cld-gateway-v1.1.5"><strong>cld-gateway-v1.1.5</strong></a><br><sub>Latest stable public release</sub></td>
  </tr>
  <tr>
    <td width="180" valign="top"><strong>SmrutAI/pedantigo</strong><br><sub>Released 2026-09-03</sub></td>
    <td valign="top"><a href="https://github.com/SmrutAI/pedantigo/releases/tag/v2.1.3"><strong>v2.1.3</strong></a><br><sub>Latest stable public release</sub></td>
  </tr>
</table>
<!-- PROFILE:BUILD:END -->

### Write

<!-- PROFILE:WRITE:START -->
<table>
  <tr>
    <td width="190" valign="top"><a href="https://blog.smritea.ai/claude-code-and-cursor-plugin"><img src="https://blog.smritea.ai/claude-code-and-cursor-plugin/og.png" width="180" alt="The Smritea plugin: persistent memory for Claude Code and Cursor"></a></td>
    <td valign="top"><a href="https://blog.smritea.ai/claude-code-and-cursor-plugin"><strong>The Smritea plugin: persistent memory for Claude Code and Cursor</strong></a><br><sub>Smritea Blog · 2026-10-23</sub><br><br>Install the Smritea plugin to give Claude Code and Cursor memory that lasts across sessions. It adds slash commands, a session hook and MCP tools.</td>
  </tr>
  <tr>
    <td width="190" valign="top"><a href="https://blog.smritea.ai/mcp-server"><img src="https://blog.smritea.ai/mcp-server/og.png" width="180" alt="Give any MCP client memory with the Smritea MCP server"></a></td>
    <td valign="top"><a href="https://blog.smritea.ai/mcp-server"><strong>Give any MCP client memory with the Smritea MCP server</strong></a><br><sub>Smritea Blog · 2026-10-20</sub><br><br>The smritea-mcp server gives an AI client tools to store, search and delete memories. Set it up for Claude Code or Cursor in a few steps.</td>
  </tr>
  <tr>
    <td width="190" valign="top"><a href="https://blog.smritea.ai/search-methods-and-rerankers"><img src="https://blog.smritea.ai/search-methods-and-rerankers/og.png" width="180" alt="Smritea search methods and rerankers: which to pick"></a></td>
    <td valign="top"><a href="https://blog.smritea.ai/search-methods-and-rerankers"><strong>Smritea search methods and rerankers: which to pick</strong></a><br><sub>Smritea Blog · 2026-10-15</sub><br><br>Smritea has three search methods and six rerankers. Learn what each does, what it costs in credits, and which limits apply.</td>
  </tr>
</table>
<!-- PROFILE:WRITE:END -->

<sub>Generated from published GitHub releases, the Smritea/DEV RSS feeds, and the
[profile updater](./scripts/update_activity.py). ·
[View refresh runs](https://github.com/tushar2708/tushar2708/actions/workflows/update-profile.yml)</sub>
