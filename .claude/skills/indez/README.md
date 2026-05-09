# indez

Active skill for spec-driven development workflows. Invoked with `/indez [mode]`.

## Modes

| Mode | Purpose |
|------|---------|
| `init` | Bootstrap a new SDD project — creates directory structure and CLAUDE.md |
| `plan` | Create or refine an epic or feature through collaborative conversation |
| `design` | Generate design.md and tasks.md from a spec's requirements.md |
| `prepare` | Analyze a feature's user stories and recommend spec breakdown |
| `implement` | Execute a spec's implementation tasks |
| `sync` | Report project status and propagate it bottom-up through the hierarchy |
| `validate` | Check traceability, EARS compliance, and spec completeness |

## Usage

```
/indez init "project description"
/indez plan --type feature --text "Users can reset their password via email"
/indez prepare --name FEAT-003
/indez design --name 007-password-reset-email
/indez implement --spec 007-password-reset-email
/indez sync --dry-run
/indez validate
```

## Structure

```
indez/
├── SKILL.md          ← routing table (always loaded)
└── modes/
    ├── init.md
    ├── plan.md
    ├── design.md
    ├── prepare.md
    ├── implement.md
    ├── sync.md
    └── validate.md
```

Each mode file is loaded only when that mode is invoked. This skill references `spec-best-practices` for shared conventions, EARS rules, and document templates.

## See Also

Full workflow guide: `../../docs/user-guide.md`
