# Mode: sync

Report project status and propagate it bottom-up through the hierarchy.

## Arguments

- `--scope` — `all` | `specs` | `features` | `epics` (default: `all`)
- `--dry-run` — show what would change without writing files (optional)

## Status Rules

### Spec status — derived from tasks.md

| Status | Condition |
|--------|-----------|
| Draft | No tasks.md, or tasks.md has no checkboxes |
| Ready | tasks.md exists with unchecked tasks, none started |
| In Progress | At least one `[x]`, but not all |
| Done | All tasks are `[x]` |
| Blocked | tasks.md contains `BLOCKED` marker |

### Feature status — derived from its linked specs

| Status | Condition |
|--------|-----------|
| Draft | No specs linked, or all specs are Draft |
| Ready | All specs Ready or Done, none In Progress |
| In Progress | At least one spec In Progress |
| Done | All specs Done |
| Blocked | Any spec is Blocked |

### Epic status — derived from its linked features

Same pattern as Feature status, applied one level up.

## Steps

1. **Scan the hierarchy** based on `--scope`:
   - Read all spec `tasks.md` files → compute spec statuses
   - Read all feature documents → derive feature statuses from spec statuses
   - Read all epic documents → derive epic statuses from feature statuses

2. **Report current state** — show a summary table of all items and their computed status. Flag anything Blocked or overdue.

3. **Show proposed changes** — list any status fields that differ from what's currently written in the documents.

4. **Confirm and write** (unless `--dry-run`) — update the Status field in each affected document.

5. **Highlight attention items**:
   - Blocked specs or features
   - Features with no specs yet (prepare not run)
   - Specs with no tasks.md (design not run)

## Notes

- Status is always derived from actual file state, never assumed
- dry-run is useful in CI or before a review — it shows drift without making changes
