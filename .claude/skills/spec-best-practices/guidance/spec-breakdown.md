# Spec Breakdown Guidance

Use when decomposing a feature's user stories into implementable specs. Deliver a high-confidence recommendation — clear rationale, explicit dependencies, implementation order.

## Grouping Principles

**Technical cohesion** — group stories that touch the same components, services, or data models.

**Dependency types:**
- Technical: Story B needs infrastructure created by Story A
- Data: Story B needs models created by Story A
- User flow: Story B follows Story A in the user journey

**Implementation order:** Foundation → independent parallel work → integration last.

**Size balance:** Aim for S or M specs. Split any L spec unless the work is genuinely inseparable.

## Recommendation Format

### Spec Breakdown Table

| Spec | Name | Stories | Effort | Depends on |
|------|------|---------|--------|------------|
| NNN | [Descriptive name] | STORY-NNN, STORY-NNN | S/M/L | NNN or None |

### For Each Spec, Provide

- **Grouping logic** — why these stories belong together
- **Technical cohesion** — what layer or concern they share
- **Dependencies** — what this spec needs and what depends on it
- **Parallelization** — can this be built while another spec is in flight?

### Implementation Phases

Present the recommended build sequence:
1. **Phase 1** — foundation specs (block others)
2. **Phase 2** — parallel independent specs
3. **Phase 3** — integration specs (depend on Phase 1 + 2)

## Quality Check

Before presenting the breakdown, verify:

- [ ] Every user story assigned to exactly one spec
- [ ] All dependencies identified
- [ ] Spec sizes are balanced (no one giant spec)
- [ ] Implementation order is logical
- [ ] Each spec has a clear, descriptive name
- [ ] Rationale provided for every grouping decision
