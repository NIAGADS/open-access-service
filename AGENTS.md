# AI Agent Code Change Policy

## 1. Repository Context

### Project Overview

`open-access-service` is a Python monorepo of packages, utilities, and services supporting NIAGADS genomics projects. It uses the [Polylith architecture](https://polylith.gitbook.io/polylith), with reusable components, service bases, and deployable projects, managed with [Poetry](https://python-poetry.org/) and the [Python Polylith toolkit](https://davidvujic.github.io/python-polylith-docs/).

### Key Directories

- `components/niagads/` — Reusable modules, including `utils`, `database`, and `csv_parser`.
- `bases/niagads/` — Service entry points and tools.
- `bases/niagads/genomicsdb_service/etl/plugins/` — GenomicsDB ETL plugins (path listed in the existing project guidance; verify against the repository).
- `projects/` — Applications, schema managers, and API services.
- `development/` — Experimental and test code.
- `developer-notes/` — Project development notes.

### Architecture and Integration

- Bases provide service entry points; components are reusable Polylith bricks.
- Manage external dependencies through Poetry in `pyproject.toml` (`[tool.poetry.dependencies]`).
- Project scripts are encapsulated classes, following patterns such as `bases/niagads/sql_runner/core.py`, and inherit from `ComponentBaseMixin`.
- `ComponentBaseMixin` initializes component loggers.
- See `components/niagads/utils/` for utility patterns and `projects/` for integration examples.
- For ETL plugin guidance, consult `bases/niagads/genomicsdb_etl/README.md` and example plugins in `bases/niagads/genomicsdb_etl/plugins/`.

## 2. Git and Workspace Rules

### Branch Naming

Use `<type>/<short-description>` with a lowercase, hyphen-separated description:

- `feature/` — New functionality or capabilities.
- `refactor/` — Internal restructuring without changing external behavior.
- `fix/` — Bug fixes or corrections to existing behavior.
- `patch/` — Small, targeted maintenance changes or database patches that are not bug fixes.
- `docs/` — Documentation-only changes.
- `test/` — Adding or improving tests without changing functionality.
- `chore/` — Routine maintenance, dependencies, tooling, or configuration.
- `perf/` — Performance optimizations without intended behavioral changes.
- `ci/` — CI/CD workflows and automation.
- `build/` — Build systems, packaging, and distribution.
- `hotfix/` — Urgent fixes to production or release branches.

Choose the prefix based on the purpose of the change, not its size. Follow existing repository conventions when applicable.

### Workspace and Worktrees

- Keep all task work inside the current project workspace.
- When separate Git worktrees are requested, create them under `<repository-root>/.worktrees/<task-name>`.
- Never place worktrees in `/tmp` or outside the workspace.
- Preserve the original checkout and all local changes.
- If the required location is blocked or cannot be safely ignored, ask before selecting another location.

### Development Notes

Store plans, checkpoints, handoffs, and architectural decisions under `developer-notes/<project>/`. Use `shared/` for cross-project work. Follow the `development-workflow` skill for directory structure, naming, progress tracking, session continuity, and historical integrity. Never overwrite historical checkpoints or handoffs or treat superseded or abandoned requests as current instructions.

## 3. Implementation Requirements

### Before Making Changes

- Review relevant nearby code, parent directories, and applicable project components to understand existing architecture, formatting, style, and conventions before implementing new files or behavior.
- Search for existing utilities, components, Pydantic models, base classes, and mixins. Reuse applicable implementations rather than duplicating functionality.
- If project instructions, configuration, and existing patterns conflict, follow the explicit instruction or configuration applicable to the task; do not copy a conflicting nearby pattern.
- Ask for clarification when context is unclear or multiple implementation approaches require a decision.

### Scope and Structure

- Implement only the requested behavior. Do not introduce abstractions, extra use cases, or fallback defaults that conceal missing, invalid, or failed data. Follow established error-handling behavior.
- Avoid redundant code and helper functions that merely wrap single statements.
- Avoid duplicate imports and code blocks.
- Place new code where it logically belongs, not simply at the current cursor position.
- Keep imports, constants, and docstrings in logical order.
- Avoid inline imports except where needed to prevent circular imports.
- Avoid nested function definitions unless necessary.
- Do not modify comments unless requested or needed to document core code changes.
- Never take credit for changes made by the user.

### Classes, Mixins, and Models

- Before adding a class or class behavior, inspect nearby code and search for applicable base classes and mixins.
- Reuse existing project mixins, combining them with `ComponentBaseMixin` as required; do not duplicate behavior already supplied by a mixin.
- Create a new mixin only when behavior is reusable across multiple classes and no existing mixin provides it. Otherwise, keep the behavior in the class.
- All classes must inherit from `ComponentBaseMixin` (`components/niagads/common/core.py`). Enums, Pydantic models, SQLAlchemy declarative bases, mapped ORM models (including materialized views), and ORM mixins are exempt. When modifying legacy classes, add the mixin if compatible with their existing design; do not perform unrelated migrations solely to add it.
- Use Pydantic v2+ when required by the task or existing project design. Do not replace established Pydantic models with dictionaries or duplicate existing validation.
- Pydantic models used for serialized output, APIs, logging, or conversion to SQLAlchemy data models during ETL must inherit from `CustomBaseModel` (`components/niagads/common/models/base.py`).
- Preserve SQLAlchemy model inheritance. Do not add `ComponentBaseMixin` when modifying ORM models or ORM mixins; use their existing database bases and applicable ORM mixins.
- Define `__repr__` or `__str__` only when useful and consistent with existing project patterns.

### Performance

This project handles enterprise-scale data. Account for performance when implementing changes.

- Add checks and defensive handling only for conditions that can arise in the requested use case or are required by project conventions.
- Avoid repeated iteration over data structures when a single pass or existing utility suffices.
- Consider parallelization when iterating over large datasets.

## 4. Python Coding Conventions

- Follow Python best practices, PEP 8, and the project's established formatting and line-length conventions, including Black and isort.
- Treat deviations from these requirements as bugs and correct them.
- Review AI-generated code for style, formatting, logical placement, and correctness before submission.
- Use additional blank lines between large code blocks where they improve readability.
- Use `snake_case` for files, directories, functions, and variables; `UpperCamelCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- Use type hints and enums for controlled vocabularies. For string enums, use `CaseInsensitiveEnum` from `components/niagads/enums/core.py`.
- Prefer encapsulation using protected (`_var`) and private (`__var`) class members.
- Write concise, relevant, professional docstrings and comments that explain behavior and rationale, not trivial details or visibility.
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#docstrings).
- Credit third-party code with source URLs in docstrings.

## 5. Testing and Validation

- In local environments, environment variables are usually in `../.env` relative to the repository root. Load that file into the test process without exposing its values.
- **Run tests only when explicitly requested.**
- After editing, review the diff and perform relevant focused non-test checks. Report any checks that could not be run.
- Run targeted checks first; repeat checks only after relevant changes or when investigating a failure.

## 6. Agent Conduct and Resource Use

### Communication and Scope

- Focus on the explicit task; do not lecture or offer unsolicited suggestions.
- Keep progress updates and final reports concise.
- Do not launch subagents unless explicitly requested.

### Efficient Tool Use

- Stay within the requested scope. Avoid repeated file reads, broad searches, redundant checks, and verbose tool output.
- Read only relevant files or sections, and reuse previously gathered information unless changes require another read.

### Usage Limits and Pausing

- Do not invent remaining token counts, usage percentages, or reset times. Use usage information only when provided by the platform or user.
- If an explicit usage warning appears, finish the current small, coherent step when possible, then record a checkpoint and stop.
- If a usage limit blocks progress, do not repeatedly retry or switch models to bypass it.
- Before stopping, record completed work and changed files, checks and results, remaining work and the exact next step, and any known usage reset time in a checkpoint under `developer-notes/<project>/`, following the `development-workflow` skill.
- Resume from that checkpoint when the user returns after the reset.

For unclear conventions or missing documentation, ask maintainers for clarification. Update this file as new project patterns emerge.
