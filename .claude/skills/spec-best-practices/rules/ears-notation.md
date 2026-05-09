# EARS Notation

All acceptance criteria in `requirements.md` MUST use EARS (Easy Approach to Requirements Syntax). Use "shall" for all mandatory requirements — never "should", "may", or "might".

## Patterns

| Pattern | Template | When to use |
|---------|----------|-------------|
| Ubiquitous | The system shall {behavior}. | Always-active behavior |
| Event-driven | WHEN {event}, the system shall {behavior}. | Triggered by a specific event |
| State-driven | WHILE {state}, the system shall {behavior}. | Active during a specific state |
| Optional feature | WHERE {feature is enabled}, the system shall {behavior}. | Configurable features |
| Unwanted | The system shall not {behavior}. | Behavior that must never occur |

## Rules

1. Each criterion must be independently testable by observing system behavior
2. No vague language: "appropriate", "user-friendly", "as needed", "when it makes sense"
3. Requirements describe WHAT and WHEN — never HOW it's built
4. Criteria are numbered prose — never checkboxes

## Examples

❌ "The system should validate input appropriately."
✅ "WHEN a user submits a form with empty required fields, the system shall display a specific error message for each missing field and prevent submission."

❌ "Handle errors gracefully."
✅ "WHEN an API request fails due to network timeout, the system shall retry up to 3 times with exponential backoff and display an error message after all retries fail."
