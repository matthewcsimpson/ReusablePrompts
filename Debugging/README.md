# Debugging

Prompts for active-loop debugging work — different shape from the
audit / fix / write prompts elsewhere in this repo. These prompts
drive a workflow that converges on an answer rather than producing
a one-shot report.

| Prompt | What it does |
|---|---|
| `regression-bisect.prompt.md` | Given last-known-good, symptom, and a reproduction, drives `git bisect` to the first bad commit, reads the diff, and proposes a fix or surfaces an intentional break. |

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns and the assumed tool capabilities. This prompt
needs file read, shell execution, and git (specifically `git
bisect`).
