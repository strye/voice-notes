# Mode: prepare

Analyze a feature's user stories and recommend how to break them into implementable specs.

## Arguments

- `--name` — feature identifier (e.g. `FEAT-003`) (required)

## Dependencies

- The feature document must exist in `.docs/planning/features/` — stop with a clear error if not found

## Steps

1. **Load the feature** — read the feature document. Extract all user stories from the User Stories table.

2. **Analyze for breakdown** — load `spec-best-practices/guidance/spec-breakdown.md` and apply its principles:
   - Group stories by technical cohesion (same component, service, or data model)
   - Identify dependency relationships between stories
   - Balance spec sizes (aim for S or M)
   - Isolate high-risk or uncertain work

3. **Present recommendation** — show the breakdown table with rationale:
   - Proposed spec name and number for each group
   - Which stories are grouped and why
   - Effort estimate (S/M/L)
   - Dependencies between specs
   - Suggested implementation phases (what can be parallelized)

4. **Confirm with user** — ask if the breakdown looks right. Allow adjustments before proceeding.

5. **Create spec shells** — for each confirmed spec, create a folder in `.docs/specs/backlog/` with a stub `requirements.md`:
   - Use `spec-best-practices/templates/spec/requirements.md`
   - Fill in the Context section (parent feature, story IDs, complexity)
   - Leave acceptance criteria as placeholders — that's for `/indez design` to flesh out

6. **Update the feature document** — add spec links to the User Stories table.

7. **Suggest next step** — `/indez design --name [first-spec]` to begin the first spec.

## Notes

- Present the breakdown once with confidence — don't offer three alternatives
- Make rationale explicit so the user can make informed adjustments
- Spec numbers should reflect proposed implementation order within the project (check existing specs to find the next available numbers)
