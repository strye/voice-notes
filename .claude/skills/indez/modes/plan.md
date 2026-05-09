# Mode: plan

Create or refine an epic or feature document through collaborative conversation.

## Arguments

- `--type` — `epic` or `feature` (required)
- `--name` — identifier or title (e.g. `EPIC-001`, `FEAT-003`, or a descriptive name for new documents)
- `--text` — description or refinement instruction (optional)
- `--epic` — parent epic ID to link a feature to (optional, features only)

## Determining the Operation

- If `--name` matches an existing file → **refine** mode: load the file and apply `--text` as refinement guidance
- If `--name` is new or omitted → **create** mode: start a new document with the next available ID

## Create Flow

### Epic

1. Ask for a title and problem statement if not provided in `--text`
2. Ask: what features do you expect this epic to contain? (rough list, not final)
3. Ask: what does success look like for this epic?
4. Generate the epic document using `spec-best-practices/templates/epic-template.md`
5. Show a preview and confirm before writing to `.docs/planning/epics/`

### Feature

1. Ask for an overview and problem statement if not provided in `--text`
2. **Collaborative story building** — ask probing questions to surface user stories:
   - "Who are the users of this feature?"
   - "Walk me through the happy path — what does success look like?"
   - "What could go wrong? What error states need handling?"
   - "Are there any edge cases or boundary conditions?"
3. Suggest user stories based on answers — present them for review, not as final
4. For each story, suggest EARS acceptance criteria — ask the user to refine
   - Load `spec-best-practices/rules/ears-notation.md` at this step
5. If requirements feel thin, load `spec-best-practices/guidance/requirements-analyst.md` for deeper probing patterns
6. Assign the next FEAT-NNN identifier
7. Generate the feature document using `spec-best-practices/templates/feature-template.md`
8. Show a preview and confirm before writing to `.docs/planning/features/`
9. If `--epic` was provided, update the parent epic's Features table

## Refine Flow

1. Read the existing document
2. Apply `--text` as guidance — update the relevant sections
3. If refining acceptance criteria, load `spec-best-practices/rules/ears-notation.md`
4. Show a diff-style summary of changes and confirm before writing

## Notes

- Always suggest, never mandate — present stories and criteria as drafts for the user to accept, edit, or reject
- Epics are optional — do not push users to create one if they have a single feature or small project
