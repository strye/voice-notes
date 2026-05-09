# spec-best-practices

Passive skill for spec-driven development conventions. Loads automatically when Claude detects spec-related work — no invocation needed.

## Activates when...

- Creating or editing epics, features, or specs
- Writing or reviewing acceptance criteria
- Working in `.docs/planning/` or `.docs/specs/` directories
- Mentions of EARS notation, user stories, or requirements

## What it provides

Once loaded, Claude will proactively:
- Flag acceptance criteria that use "should" instead of "shall"
- Suggest splitting specs that look too broad
- Point out implementation details that belong in design.md, not requirements.md
- Offer EARS rewrites when requirements are vague
- Recommend `/indez validate` before implementation begins

## Structure

```
spec-best-practices/
├── SKILL.md                         ← hierarchy, paths, routing table (always loaded)
├── rules/
│   ├── ears-notation.md             ← EARS patterns, rules, and examples
│   ├── spec-scoping.md              ← story-level scoping rules and effort sizing
│   └── three-file-separation.md     ← what belongs in requirements/design/tasks
├── guidance/
│   ├── requirements-analyst.md      ← probing questions and EARS translation patterns
│   └── spec-breakdown.md            ← grouping stories into implementable specs
└── templates/
    ├── epic-template.md
    ├── feature-template.md
    └── spec/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

Resource files are loaded on demand — only the routing table in `SKILL.md` is always in context.

## See Also

Full workflow guide: `../../docs/user-guide.md`
