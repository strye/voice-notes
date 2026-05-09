# Mode: implement

Execute the implementation tasks for a spec, working through tasks.md systematically.

## Arguments

- `--spec` — spec folder name (e.g. `007-password-reset-email`) (required)
- `--task` — specific task number to run (e.g. `2`, `2.1`) (optional — omit to run all incomplete tasks)

## Dependencies

- `requirements.md`, `design.md`, and `tasks.md` must all exist in the spec folder
- If any are missing, stop and suggest the appropriate prior step

## Steps

1. **Load spec context** — read all three spec files. Understand:
   - What is being built (requirements.md)
   - How it should be built (design.md)
   - What tasks remain (tasks.md — find all unchecked `[ ]` items)

2. **Determine scope**:
   - If `--task` provided: execute only that task (and its sub-tasks if a parent task number)
   - If no `--task`: execute all incomplete tasks in order

3. **Execute tasks** — for each task in scope:
   - Implement the work described
   - Follow the design — components, interfaces, file paths, error handling as specified in design.md
   - Ensure acceptance criteria from requirements.md are satisfied

4. **Update tasks.md** — mark each completed task `[x]` immediately after completion. Do not batch updates.

5. **Stop and report** — after completing the scoped tasks:
   - Show which tasks were completed
   - Show remaining tasks if any
   - Do not auto-proceed to the next task outside the requested scope

6. **Suggest next step** — if tasks remain: `/indez implement --spec [name]` to continue. If all tasks done: `/indez sync` to update project status.

## Notes

- Follow design.md precisely — do not improvise architecture during implementation
- If the design is ambiguous or wrong for a task, stop and flag it rather than guessing
- Test tasks are not optional — implement them in the same pass as their corresponding feature tasks
