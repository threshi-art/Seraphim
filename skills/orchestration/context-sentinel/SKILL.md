---
name: context-sentinel
description: Use when a request depends on prior conversation, project canon, unresolved references, corrections, missing project history, or distinguishing established context from novel, ambiguous, or conflicting material. Also use for questions about the completeness of available personal or project context.
---

# Context Sentinel

## Overview

Resolve continuity before analysis. Establish the context needed for the next
decision, identify its evidence and limits, and preserve the user's objective
without performing the substantive investigation or judgment. A skill guides
retrieval; it does not grant access to conversations, files, or memory storage.

## Workflow

1. Extract references whose meaning depends on earlier context: pronouns,
   symbols, names, artifacts, prior decisions, and phrases such as "this" or
   "the earlier one."
2. Compare each reference with supplied conversation and project context. Apply
   the latest applicable direct user correction within its stated scope. If
   that resolves the task, continue without a redundant history search.
3. When missing history would change the next decision, read
   `references/personal-context-retrieval.md`. Discover available retrieval
   capabilities and their current instructions. Use the Personal Context skill
   for conversation recovery when available; use the owning source skill for a
   known file or live project record. Reuse an existing Project Memory Router
   packet rather than repeating its searches or creating a routing loop.
4. Separate source observations, retrieved summaries, assumptions, decisions,
   and reported actions. Verify changeable operational claims through an
   available authoritative source when the requested action depends on them.
5. Assign a state from `references/context-state-contract.md`. Record recovery
   coverage whenever history was needed, queried, unavailable, or its
   completeness was questioned. Missing results do not establish that no
   earlier work exists.
6. Return the smallest useful context packet, including material conflicts,
   correction history, and the next supported action.
7. Hand the context packet to the Semantic Priority Router. Do not select the
   final specialist or perform its analysis.

Novel context is a valid state, not a reason to stop. Ask a question only when
an unresolved ambiguity would materially change the requested operation or
primary object.

## Output Contract

Return:

- `context_state`;
- `resolved_references` with the supporting context;
- `unresolved_references` with plausible meanings;
- `conflicts` between new and established context;
- `correction_history` showing what was superseded;
- `continuity_note` for the next routing stage.

When the recovery condition in step 5 applies, also return `recovery` using
`references/context-state-contract.md`. Keep private context in the authorized
working environment. Do not copy personal records into a public skill package.

## Example

User: "Correction: by the earlier model I meant the legal framework, not the
diagram. Analyze its assumptions."

Return `context_state: conflicting`, bind "earlier model" to the legal
framework, record the diagram interpretation as superseded, and preserve
"analyze assumptions" for routing.

## Quick Reference

| Situation | Result |
|---|---|
| Explicitly established reference | `known` |
| Supported link across context | `correlated` |
| No relevant prior context established in inspected material | `novel` |
| Multiple plausible meanings | `ambiguous` |
| New information contradicts context | `conflicting` |

## Common Mistakes

- Treating `novel` as failure instead of continuing.
- Guessing a referent when alternatives would change the task.
- Retaining an old interpretation after a direct correction.
- Expanding context resolution into substantive analysis.
- Equating a failed search with absent history or complete account coverage.
- Treating an assistant's completion claim as a verified deployment or install.
- Claiming that retrieval changed durable memory or installed a skill.
