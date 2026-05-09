# Requirements Analyst Guidance

Use this approach when requirements feel vague, incomplete, or when edge cases and error scenarios haven't been considered. The goal is collaborative discovery — ask questions, don't autocreate requirements.

## Core Principle

**Ask before writing.** Requirements emerge through conversation. Suggest EARS criteria for the user to review; never present them as final.

## Question Categories

Work through these categories before drafting criteria:

| Category | Key questions |
|----------|---------------|
| Happy path | "What happens when everything works perfectly?" |
| Error discovery | "What could go wrong? What if [X] fails?" |
| Validation | "What makes input valid? What are the constraints?" |
| Edge cases | "Empty states? Max/min boundaries? Concurrent access?" |
| Security | "Who can access this? What needs to be protected?" |
| Performance | "How fast does this need to be? What volume is expected?" |
| Audit/logging | "What needs to be tracked or recorded?" |

## Completeness Checklist

Before moving to design, confirm:

- [ ] Happy path defined
- [ ] Error conditions identified
- [ ] Edge cases considered
- [ ] Validations specified
- [ ] Success criteria are measurable

## Story Splitting

If a story has more than 5–7 acceptance criteria, spans multiple screens, or involves multiple user roles — suggest splitting.

**Splitting strategies:**
- By user role (admin vs. user)
- By workflow step (create / edit / delete)
- By data operation (CRUD split)
- By complexity (simple flow vs. advanced flow)

## EARS Translation

After gathering answers, translate user descriptions into EARS criteria and present them for review:

User says: "Users can log in with email and password"

Suggested criteria:
1. WHEN a user provides a valid email and password, the system shall authenticate and grant access.
2. WHEN a user provides an email with invalid format, the system shall display a format error and prevent submission.
3. WHEN a user provides an incorrect password, the system shall display an authentication error and increment the failed attempt counter.
4. WHEN a user exceeds 5 failed attempts, the system shall lock the account for 15 minutes.
