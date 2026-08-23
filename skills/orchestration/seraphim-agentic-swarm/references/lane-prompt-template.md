# Lane Task prompt skeleton

Copy and fill for each worker. Keep owned/forbidden lists concrete.

```text
Repo: <absolute-repo-path>
Lane: <lane-name>
Model: inherit (unless user specified otherwise)
Background: true

Owned files (exclusive write):
- <path/a>
- <path/b>

Forbidden files (do not edit):
- <path/c>
- <path/d>

Goal:
<one-paragraph objective for this lane only>

Acceptance criteria:
- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] No edits outside owned files

Verification:
Run: <e.g. pnpm check / targeted test / playtest command>
Pass means: <expected outcome>

Return format:
1. Lane name
2. Files changed (paths only)
3. What was implemented
4. Verification command + result
5. Blockers / follow-ups for next wave
6. Do not commit; preserve existing git WIP
```
