---
name: seraphim-agentic-swarm
description: Use when the user asks for swarm, multi-agent, parallel agents, Seraphim Agentic Swarm, non-linear multi-lane work, or autonomous continuous multi-agent execution with specialized lanes and coordinator-driven waves.
---

# Seraphim Agentic Swarm

Autonomous multi-agent development: parallel specialized lanes, coordinator
synthesizes, next wave launches without user gatekeeping.

## When to use

- User wants swarm / parallel agents / multi-aspect work / “no stopping” loops
- Distinct ownership areas that will not thrash the same files
- Skip when work is a single file, a pure design question, or lanes cannot be
  isolated without merge conflicts

## Coordinator protocol (parent)

1. Decompose into independent lanes with exclusive file ownership.
2. Prefer async background Task agents (`run_in_background: true`) with clear
   lane names and ownership in each prompt.
3. Selective parallelism only: launch independent workstreams together
   (e.g. biomes vs gameplay feel vs entity visuals). Do not parallelize writers
   that share files.
4. Do **not** linearize when the user asked for swarm.
5. After launching agents: **end the turn**. Do not AwaitShell/poll Task agents.
   Synthesize on completion notifications.
6. On completion: synthesize results, cite agents as `Name (agent-id)`, verify
   the wave, then launch the next wave without waiting for the user unless a
   blocking decision is required.
7. One verify/board lane after sibling writers finish — never concurrent with
   writers on the same files.

## Lane patterns

| Lane | Owns (typical) | Avoids |
|---|---|---|
| **Visual/biome** | EnvironmentRenderer (+ tiny wiring) | GameWorld, EntityRenderer |
| **Gameplay feel** | GameWorld / types / testApi | Renderer files |
| **Entity/VFX** | EntityRenderer / effects | EnvironmentRenderer, GameWorld core |
| **Verify/board** | `pnpm check` / playtest + TASKMASTER updates | Feature implementation in owned writer files |
| **Feature expansion** | types, missions, briefing wiring | Renderers unless explicitly owned |

Adapt paths to the repo. Keep the exclusivity rule even when names differ.

## Conflict rules

- Assign exclusive file ownership per lane in the Task prompt
- One verify lane after siblings complete; not concurrent with writers on shared files
- Preserve git WIP; no commit unless the user asks; no reset / destructive git

## Prompt contract (each worker)

Every Task prompt must include:

1. Repo path
2. Lane name
3. Owned files (exclusive write list)
4. Forbidden files (do not edit)
5. Acceptance criteria
6. Verification command
7. Return format (what to report back)

Copy-paste skeleton: [references/lane-prompt-template.md](references/lane-prompt-template.md)

## Swarm waves

```
Wave N:   parallel implementers (exclusive ownership)
          → end turn → synthesize on notifications
Wave N+1: merge-verify lane, then next implementers
```

- Keep `TASKMASTER` / `docs/TASKMASTER.md` updated when the project has one
- Do not start Wave N+1 writers until Wave N verify passes (or failures are
  assigned as fix lanes with ownership)

## Anti-patterns

- One giant serial agent when the user asked for swarm
- Three agents editing the same file
- Foreground parent re-doing delegated work
- Awaiting/polling Task agents instead of ending the turn
- Verify lane racing writers on the same files
- Committing or resetting without an explicit user request

## Reporting

When summarizing a wave, list each completed agent as `Lane Name (agent-id)`,
state what landed, verify outcome, and the next wave plan.
