# Mode: validate

Validate specification completeness, consistency, and traceability.

## Arguments

- `--name` — spec or feature name to validate (optional — omit to validate everything)

## What to Validate

### Spec-level checks (run for each spec in scope)

**Completeness**
- [ ] requirements.md exists and has at least one user story
- [ ] requirements.md has a Context section with parent feature reference
- [ ] design.md exists
- [ ] tasks.md exists

**EARS compliance** — load `spec-best-practices/rules/ears-notation.md`
- [ ] All acceptance criteria use "shall"
- [ ] No vague language ("appropriate", "user-friendly", "as needed")
- [ ] Criteria are numbered prose, not checkboxes

**Three-file separation** — load `spec-best-practices/rules/three-file-separation.md`
- [ ] requirements.md contains no file paths, code snippets, or checkboxes
- [ ] tasks.md is the only file with checkboxes
- [ ] design.md contains no acceptance criteria

**Traceability**
- [ ] Each acceptance criterion is addressed by at least one design component
- [ ] Each design component is covered by at least one task
- [ ] Each task references the AC(s) it fulfills

**Scoping** — load `spec-best-practices/rules/spec-scoping.md`
- [ ] Spec is story-level (not feature or epic sized)
- [ ] Tasks are < 1 day each

### Feature-level checks (when validating a feature or all)

- [ ] Feature document exists in `.docs/planning/features/`
- [ ] All user stories have a linked spec (or are explicitly marked as out of scope)
- [ ] Parent epic reference is valid (if present)

## Output Format

Report findings grouped by severity:

**Errors** (must fix before implementation)
- Missing required files
- Broken parent references
- Requirements with no design coverage

**Warnings** (should fix, won't block)
- EARS violations
- Three-file separation issues
- Tasks missing AC references

**Suggestions** (consider fixing)
- Spec scope appears too broad
- Stories without effort estimates

## Notes

- Run validate before starting implementation on a spec
- Run validate after refining requirements to catch regressions
- A clean validate report does not guarantee good design — it guarantees structural correctness
