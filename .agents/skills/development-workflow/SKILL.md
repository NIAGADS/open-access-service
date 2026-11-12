---
name: development-workflow
description: Manage development plans, progress tracking, checkpoints, handoffs, and architectural decisions in a multi-project monorepo. Use when planning, implementing, resuming, reviewing progress, or handing off development work.
---

# Development Workflow

## Purpose

Maintain a reliable, chronological record of development activity across projects. Preserve implementation history, track progress, support session continuity, and prevent outdated or abandoned requests from being treated as active work.

## 1. Project Organization

Store development documentation under `developer-notes/<project>/`.

Use the established repository project name. Do not create alternate names or duplicate project directories.

```text
developer-notes/
├── <project>/
│   ├── README.md
│   ├── plans/
│   ├── checkpoints/
│   │   └── <task>/
│   ├── handoffs/
│   │   └── <task>/
│   └── decisions/
└── shared/
    ├── README.md
    ├── plans/
    ├── checkpoints/
    ├── handoffs/
    └── decisions/
```

Use `shared/` for cross-project work. Create only the directories needed.

## 2. Naming Conventions

- Use lowercase, descriptive, kebab-case names for projects, tasks, and documents.
- Name tasks by feature, component, or objective.
- Use consistent task names across plans, checkpoints, and handoffs.
- Name checkpoints and handoffs using `YYYY-MM-DD-HHMM.md`, based on local time.
- Do not use generic names such as `latest.md`, `notes.md`, or `handoff-final.md`.
- Do not create numbered versions such as `plan-v2.md` or `handoff-3.md`.
- Avoid duplicating documents when an existing task record applies.

## 3. Starting or Resuming Work

Before beginning a task:

1. Identify the relevant project and task.
2. Read the project's `README.md` progress index.
3. Locate any existing plan and the most recent relevant checkpoint and handoff.
4. Review older records only when necessary to understand decisions or unresolved issues.
5. Verify the recorded implementation state against the current codebase.
6. Identify any conflicts between historical notes, current code, and the user's latest instructions.

**Current user instructions and verified repository state take precedence over historical development notes.**

Do not automatically resume unfinished work, revive abandoned requests, or implement previously proposed changes without confirming they remain relevant to the current task.

## 4. Implementation Plans

Store plans in:

`developer-notes/<project>/plans/<task>.md`

Plans should include:

- Objective and scope.
- Proposed implementation approach.
- Relevant components and dependencies.
- Implementation steps or milestones.
- Validation strategy.
- Open questions or decisions requiring guidance.

Before creating a plan, check whether one already exists.

Maintain the original plan as a record of intended work. Do not silently rewrite plans to reflect subsequent implementation changes.

When requirements or scope change:

- Record the change and rationale in the next checkpoint or handoff.
- Update the plan when explicitly requested or when the user approves a revised approach.
- Identify superseded sections rather than silently removing historical context.

Do not create a formal plan for trivial changes unless requested.

## 5. Development Checkpoints

Store checkpoints in:

`developer-notes/<project>/checkpoints/<task>/YYYY-MM-DD-HHMM.md`

Checkpoints are lightweight, chronological snapshots of implementation progress.

Create checkpoints after:

- Significant implementation milestones.
- Architectural or design changes.
- Important validation results.
- Changes in scope or direction.
- Blockers that materially affect implementation.
- Substantial work that should be preserved before continuing.

Do not create checkpoints after every minor code change.

Each checkpoint should contain:

```markdown
# Checkpoint: <task>

**Timestamp:** YYYY-MM-DD HH:MM
**Status:** in-progress | blocked | completed

## Completed

- ...

## Current State

- ...

## Validation

- ...

## Decisions or Changes

- ...

## Blockers

- ...

## Next Steps

- ...
```

Checkpoint rules:

- Treat checkpoints as immutable historical snapshots.
- Never overwrite or retrospectively rewrite previous checkpoints.
- Record corrections or changes in subsequent checkpoints.
- Keep checkpoints concise and factual.
- Distinguish completed implementation from proposed or unverified work.
- Do not claim validation was performed unless it actually ran.

## 6. Session Handoffs

Store handoffs in:

`developer-notes/<project>/handoffs/<task>/YYYY-MM-DD-HHMM.md`

Create a handoff at the end of a substantive development session or when explicitly requested.

A handoff should enable another Codex session or developer to resume the task without reconstructing its history.

Each handoff should contain:

```markdown
# Handoff: <task>

**Timestamp:** YYYY-MM-DD HH:MM
**Status:** planned | in-progress | blocked | completed | abandoned | superseded

## Objective

- ...

## Work Completed

- ...

## Files or Components Changed

- ...

## Current Implementation State

- ...

## Validation

- ...

## Decisions

- ...

## Outstanding Issues

- ...

## Next Steps

- ...

## References

- Plan:
- Latest checkpoint:
- Relevant decisions:
```

Handoff rules:

- Create a new timestamped handoff for each substantive session.
- Never replace an earlier handoff with an updated summary.
- Summarize the current state rather than duplicating every checkpoint.
- Reference relevant checkpoints, plans, and decisions.
- Clearly distinguish completed, incomplete, blocked, and proposed work.
- Identify abandoned or superseded approaches explicitly.
- Do not carry forward outdated action items as current instructions.
- Do not imply that a task is complete solely because the session ended.

## 7. Architectural Decisions

Store significant architectural decisions in:

`developer-notes/<project>/decisions/<decision-name>.md`

Each decision should document:

- Context and problem.
- Decision made.
- Rationale.
- Alternatives considered, when relevant.
- Consequences or trade-offs.
- Status: proposed, accepted, or superseded.

Create decision records only for choices with meaningful architectural or long-term maintenance implications.

Do not create decision records for routine implementation details.

When a decision changes, preserve the original record and link to the superseding decision.

## 8. Progress Index

Maintain:

`developer-notes/<project>/README.md`

The index provides a concise overview of development activity.

Use the following format:

| Task     | Status      | Last Updated | Plan | Latest Checkpoint | Latest Handoff |
| -------- | ----------- | ------------ | ---- | ----------------- | -------------- |
| `<task>` | in-progress | YYYY-MM-DD   | Link | Link              | Link           |

Allowed statuses:

- `planned` — Work defined but not started.
- `in-progress` — Implementation underway.
- `blocked` — Progress requires resolving an issue or dependency.
- `completed` — Implementation and required validation finished.
- `abandoned` — Work intentionally discontinued.
- `superseded` — Replaced by another approach or task.

Update the index whenever creating a checkpoint or handoff, changing task status, or superseding a plan.

Keep the index brief. Detailed implementation history belongs in the individual records.

Never mark work as completed without verifying the implementation and required validation.

## 9. Historical Integrity and Scope Control

Development notes are historical records, not an accumulating list of instructions.

- Preserve the chronology of implementation decisions and progress.
- Do not overwrite earlier checkpoints or handoffs.
- Do not combine unrelated requests into an existing task merely because they affect the same component.
- Distinguish active work from abandoned, superseded, or deferred requests.
- Do not infer that an unfinished action item remains authorized.
- Do not silently resurrect old requirements.
- Document changes in direction and identify which previous assumptions or approaches are no longer applicable.
- When historical notes conflict with current instructions, follow the current instructions and document the discrepancy when relevant.

## 10. Workflow Completion

At the end of a substantive development session:

1. Verify the actual implementation state.
2. Run relevant validation where feasible.
3. Create a final checkpoint if a significant milestone warrants one.
4. Create a timestamped session handoff.
5. Update the project progress index.
6. Report completed work, validation results, unresolved issues, and next steps to the user.

Avoid unnecessary documentation for trivial changes. Documentation should support continuity and traceability without becoming an additional development burden.
