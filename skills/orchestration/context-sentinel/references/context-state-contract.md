# Context State Contract

Use exactly one top-level state:

| State | Definition |
|---|---|
| `known` | The active context explicitly establishes the reference. |
| `correlated` | Two or more supplied facts support the same interpretation. |
| `novel` | No relevant prior context was established in the inspected material; earlier context may exist elsewhere. |
| `ambiguous` | Multiple interpretations remain plausible and consequential. |
| `conflicting` | New material or a correction contradicts the prior interpretation. |

Each resolved reference records `reference`, `meaning`, and
`supporting_context`. Each unresolved reference records `reference`,
`plausible_meanings`, and `decision_needed`. A correction records
`superseded_interpretation`, `replacement`, and `user_language`.

Do not convert a correlation into certainty. When several local states exist,
choose the top-level state with the greatest routing consequence in this order:
`conflicting`, `ambiguous`, `novel`, `correlated`, `known`.

Reference identity and claim verification are separate. A project name can be
`known` while its current release status remains unverified. Use
`supporting_context` and the recovery record to preserve that distinction.

## Recovery record

Add `recovery` when history was needed, queried, unavailable, or its
completeness was questioned. Preserve the existing fields above for consumers
that do not use this additive record. Include:

1. `requested_scope`: the project, subject, relevant identifiers, and any time
   window the task requires. Preserve uncertainty in identity or dates.
2. `retrieval_status`: one of `not_needed`, `not_attempted`, `retrieved`,
   `partial`, `no_match`, `unavailable`, or `error`.
3. `sources_checked`: sources actually inspected, with returned references
   when available. Planned checks belong in `next_action`, not here.
4. `coverage_gaps`: missing or inaccessible sources and unresolved parts of
   the request. State that completeness is unknown when no inventory proves it.
5. `claims`: only the context claims needed for the next decision.
6. `next_action`: the supported continuation, source check, or focused question.

Use `retrieved` for sufficient relevant evidence for this task, never as a
claim that every project or conversation was searched. Use `partial` when a
search produced relevant evidence but material gaps remain. Use `no_match`
only after an actual search yielded no relevant evidence. Use `unavailable`
when the needed capability or source cannot be accessed, and `error` when a
call failed. Use `not_attempted` for a proposed check that has not run.

For each claim, record:

| Field | Meaning |
|---|---|
| `claim` | The relevant statement or decision. |
| `source_class` | `current_user`, `source_document`, `tool_observation`, `retrieved_summary`, `assistant_analysis`, or `unknown`. |
| `source_ref` | An actual source locator returned or supplied, or `null`. |
| `source_date` | The source's supported date, or `null`; do not infer it from result order. |
| `effective_date` | When the statement applies, if established; otherwise `null`. |
| `status` | `current`, `historical`, `hypothetical`, `proposed`, `rejected`, `superseded`, `unresolved`, `action_reported`, or `action_verified`. |
| `verification_note` | Why it is usable, uncertain, or in need of a current source check. |

A summary that attributes a statement to the user is still a
`retrieved_summary` until the original source is inspected. Preserve attributed
speaker and date in the note without upgrading the source class. A retrieval
timestamp is not the original statement's date. Leave absent metadata `null`.

Record only relevant corrections. Supersession applies to the same claim and
scope; a hypothetical scenario does not overwrite a real fact, and a newer
assistant summary does not overrule an applicable direct user instruction.
