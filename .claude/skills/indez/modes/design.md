# Mode: design

Generate or refine `design.md` and `tasks.md` for a spec, derived from its `requirements.md`.

## Arguments

- `--name` — spec folder name (e.g. `007-password-reset-email`) (required)

## Dependencies

- `requirements.md` must exist in the spec folder — stop with a clear error if it does not

## Steps

1. **Load requirements** — read `requirements.md` from the spec folder. Extract:
   - All acceptance criteria (numbered items using EARS)
   - The user story statement
   - Any stated dependencies or constraints

2. **Check for existing design** — if `design.md` already exists, this is a refinement. Read it and note what already exists before generating updates.

3. **Generate design.md** — using `spec-best-practices/templates/spec/design.md`:
   - Load `spec-best-practices/rules/three-file-separation.md` to ensure correct placement of content
   - Design components that satisfy each acceptance criterion
   - Map each component back to the criteria it fulfills
   - Specify file changes (create/modify table)
   - Define error handling for each failure path in the criteria
   - Include a test strategy (unit + integration)

4. **Generate tasks.md** — using `spec-best-practices/templates/spec/tasks.md`:
   - Derive atomic tasks from the design components
   - Each task completable in < 1 day
   - Tasks reference the acceptance criteria they fulfill (e.g. `Fulfills: AC-2, AC-3`)
   - Order by dependency — foundation tasks first
   - Include test tasks alongside implementation tasks

5. **Confirm before writing** — show both files for review. Write only after confirmation.

6. **Suggest next step** — `/indez implement --spec [name]` to begin execution.

## Notes

- Do not put file paths, interfaces, or implementation details in requirements.md — if you spot them there, flag it to the user
- Tasks should be granular enough to track daily progress but not so fine-grained they describe keystrokes
