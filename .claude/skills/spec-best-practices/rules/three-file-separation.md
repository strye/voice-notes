# Three-File Separation

Each spec folder contains exactly three files with strict boundaries on what belongs where.

## requirements.md — WHAT and WHEN

- User story statement
- Numbered EARS acceptance criteria
- Context section (epic, feature, story IDs, complexity, status, dependencies)

**Never in requirements.md:**
- File paths or directory structures → design.md
- Code snippets or interfaces → design.md
- Implementation steps → tasks.md
- Checkboxes → tasks.md

## design.md — HOW

- Architecture and component design
- Data models and interfaces
- File change map (what files change and how)
- Error handling strategy
- Test strategy

**Never in design.md:**
- Acceptance criteria → requirements.md
- Checkbox task lists → tasks.md

## tasks.md — ORDERED STEPS

- Checkboxes only — this is the **only** file with checkboxes
- Each task completable in < 1 day
- Tasks reference which acceptance criteria they fulfill
- Ordered by dependency — earlier tasks unblock later ones

**Never in tasks.md:**
- Prose requirements → requirements.md
- Architecture decisions → design.md
