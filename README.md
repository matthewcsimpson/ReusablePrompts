# ReusablePrompts

A collection of prompts for agentic coding tools (Claude Code, Codex,
and similar) that have filesystem access, shell execution, and git.

Prompts are grouped into folders by purpose. Each folder has its own
README explaining what's inside and how the prompts there fit together.

## Invocation

These are plain markdown files — no tool-specific format. Pick whichever
pattern fits how you work:

1. **Clone and reference.** Clone this repo somewhere local and point
   your agent at the file:

   ```
   git clone https://github.com/matthewcsimpson/ReusablePrompts.git ~/code/ReusablePrompts
   # then in your agent:
   #   follow ~/code/ReusablePrompts/AuditTesting/audit-test-coverage.prompt.md
   ```

   Best when you'll use the prompts across many projects and want a
   single source of truth you can `git pull` to update.

2. **Copy into the target project.** Copy the prompt file into the repo
   you're working on (e.g. `prompts/audit-test-coverage.prompt.md` or
   `.claude/commands/audit-test-coverage.md` for Claude Code slash
   commands). Commit it alongside the project's other tooling.

   Best when the project's contributors should be able to run the same
   prompt without cloning anything extra, or when you want the prompt
   versioned with the project it audits.

3. **Paste into chat.** Open the prompt file, copy its contents, paste
   into the agent chat, add your target / context underneath.

   Best for one-off use or for tools without filesystem access to this
   repo.

## Target tools

These prompts assume an agentic CLI with file read, shell execution,
and git (branch + commit). Designed against Claude Code and Codex CLI;
anything with the same capability set should work.

## Current contents

### `AuditTesting/`

A pair of prompts for working on a repo's test suite.

- `audit-test-coverage.prompt.md` — read-only survey that ranks the
  most important coverage gaps and suggests cases for each.
- `add-missing-tests.prompt.md` — takes one target from the audit (or
  one you name directly) and writes tests for it, matching the
  project's existing conventions.

See [`AuditTesting/README.md`](AuditTesting/README.md) for the full
workflow.

## Status

Work in progress. More prompt collections will be added over time.
