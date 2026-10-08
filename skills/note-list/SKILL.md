---
name: note-list
description: List the user's notes, optionally including finished ones or filtering by project or type.
argument-hint: "[--all] [--project NAME] [--type TYPE]"
allowed-tools: Bash(*/scripts/notescos *)
---
List the user's notes.

Requested filters: $ARGUMENTS

Run `${CLAUDE_PLUGIN_ROOT}/scripts/notescos list` and add only these options when the user asked for them:
- `--all` to include finished notes
- `--project NAME` to show one project
- `--type TYPE`, where TYPE is one of task, followup, waiting_on, decision, idea, reference

Quote any value that contains spaces and ignore anything else in the filters. Show the output as is. If it says "No notes.", say so and suggest `/note`.
