# Spec NNN: [Spec Title] — Design

## Overview

[High-level description of the technical approach. 2-4 sentences.]

## Components

### [Component Name] *(Type: Service | UI | Hook | Util | etc.)*

**Purpose**: [What this component does]

**Interface**:
```typescript
// Key interfaces, types, or function signatures
```

**Behavior**: [How it works, edge cases, error handling]

## Data Models

### [Model Name]

```typescript
interface ModelName {
  field: type;
}
```

## File Changes

| File | Change Type | Detail |
|------|-------------|--------|
| `path/to/file.ts` | Create | [What it contains] |
| `path/to/other.ts` | Modify | [What changes] |

## Error Handling

[How errors are surfaced to the user or calling code. What recoverable vs. fatal errors look like.]

## Testing Strategy

- **Unit**: [What to unit test]
- **Integration**: [What integration scenarios to cover]
