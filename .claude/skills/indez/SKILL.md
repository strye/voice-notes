---
name: indez
description: Spec-driven development workflow tool. Use when asked to initialize a project, create or refine epics and features, generate system design, prepare a feature for development, implement a spec, sync project status, or validate specification completeness. Invoked with /indez [mode].
---

# Indez

Spec-driven development workflows for Claude Code. Each mode handles one phase of the planning and implementation lifecycle.

## Usage

```
/indez [mode] [arguments]
```

## Modes

| Mode | Purpose | Arguments |
|------|---------|-----------|
| `init` | Bootstrap a new SDD project | `"project description"` |
| `plan` | Create or refine an epic or feature | `--type epic\|feature`, `--name`, `--text`, `--epic` |
| `design` | Generate design.md + tasks.md from requirements | `--name feature-name` |
| `prepare` | Analyze a feature and recommend spec breakdown | `--name FEAT-NNN` |
| `implement` | Execute a spec's tasks | `--spec NNN-spec-name` |
| `sync` | Report status and propagate it bottom-up | `--scope all\|specs\|features\|epics`, `--dry-run` |
| `validate` | Validate traceability and spec completeness | `--name feature-name` (optional) |

## Mode Routing

Load the corresponding mode file when a mode is invoked. Do not load mode files upfront.

| Mode invoked | Load |
|--------------|------|
| `init` | `modes/init.md` |
| `plan` | `modes/plan.md` |
| `design` | `modes/design.md` |
| `prepare` | `modes/prepare.md` |
| `implement` | `modes/implement.md` |
| `sync` | `modes/sync.md` |
| `validate` | `modes/validate.md` |

## Always Apply

- Directory paths and naming conventions are defined in the `spec-best-practices` passive skill — load it if not already in context
- Stop after completing the requested mode. Offer a logical next step but do not auto-proceed
