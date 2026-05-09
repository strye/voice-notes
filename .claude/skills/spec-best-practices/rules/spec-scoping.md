# Spec Scoping Rules

Scope specs at the **story level** — one user story, or at most 3-5 tightly related stories.

## Well-Scoped Spec

- Completes in 1–5 days of development
- Touches no more than 5–10 files significantly
- Has clear, testable acceptance criteria
- Requires no more than 3–5 implementation tasks

If a spec exceeds these limits, split it.

## Examples

✅ Good: "As a user, I can reset my password via email"
❌ Too broad: "User authentication system" — this is a feature, not a spec
❌ Too broad: "Chat interface redesign" — this spans multiple stories

## Effort Sizing

| Size | Duration | Notes |
|------|----------|-------|
| S | 1–3 days | Single developer, clear scope |
| M | 4–7 days | Single developer or short pair |
| L | 8–15 days | Consider splitting unless genuinely inseparable |

## Anti-Patterns

| ❌ Don't | ✅ Do instead |
|----------|--------------|
| Epic-sized specs | Scope to a single story |
| Vague stories: "Improve UX" | Specific: "As a user, I can reset my password within 30 seconds" |
| Specs without feature/epic context | Always include Context section in requirements.md |
| Orphan specs | Every spec references its parent feature |
