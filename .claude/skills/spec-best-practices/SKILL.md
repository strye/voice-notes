---
name: spec-best-practices
description: Spec-driven development rules, EARS notation, three-tier planning hierarchy (Epic → Feature → Story → Spec), directory conventions, and document templates. Activate when creating or refining epics, features, specs, requirements, designs, or tasks — or when working in .indez/ or .docs/ planning directories.
---

# Spec Best Practices

Core conventions for spec-driven development. Always apply the hierarchy and paths below. Load additional rule files only when the relevant activity is underway.

---

## Hierarchy

```
EPIC          — Strategic initiative spanning multiple features (.docs/planning/epics/)
  └── FEATURE — Deliverable capability made of user stories (.docs/planning/features/)
        └── SPEC — Story-level implementation unit (.docs/specs/ready/)
              ├── requirements.md  — WHAT (EARS acceptance criteria)
              ├── design.md        — HOW (architecture, file changes)
              └── tasks.md         — ORDERED implementation steps (checkboxes only here)
```

Epics are **optional** — small projects and prototypes may only need features and specs.

---

## Directory Paths

| Document Type | Path |
|---------------|------|
| Epics | `.docs/planning/epics/` |
| Features | `.docs/planning/features/` |
| Specs (drafting) | `.docs/specs/backlog/` |
| Specs (implementation-ready) | `.docs/specs/ready/` |
| Specs (done/retired) | `.docs/specs/archived/` |

`.kiro/specs/` is a symlink to `.docs/specs/ready/`. Only create the symlink if the `.kiro/` folder already exists.

---

## Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Epic | `EPIC-NNN-kebab-title.md` | `EPIC-001-user-authentication.md` |
| Feature | `FEAT-NNN-kebab-title.md` | `FEAT-003-password-reset.md` |
| Spec folder | `NNN-kebab-title/` | `007-password-reset-email/` |

Spec numbers indicate proposed implementation order. Lower numbers first. Dependencies must have lower numbers than the specs that depend on them.

---

## Resource Routing

Load these files only when the described activity is underway. Do not load all of them upfront.

| Activity | Load |
|----------|------|
| Writing or reviewing acceptance criteria | `rules/ears-notation.md` |
| Creating, sizing, or splitting a spec | `rules/spec-scoping.md` |
| Creating or editing any spec file (requirements/design/tasks) | `rules/three-file-separation.md` |
| Requirements feel vague, incomplete, or edge cases are missing | `guidance/requirements-analyst.md` |
| Breaking a feature into specs for implementation | `guidance/spec-breakdown.md` |
| Creating a new epic, feature, or spec document | `templates/` (load the relevant template) |
