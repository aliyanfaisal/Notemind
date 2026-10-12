---
name: note-top
description: Show the notes that matter most right now, ranked by due date, priority and how long a follow-up has waited. Use when the user asks what to work on first.
argument-hint: "[how many, default 5]"
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
How many notes the user asked for (empty means 5): $ARGUMENTS

Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact top` and, if the user gave a number, add it after `top` (for example `top 3`). Ignore anything that is not a whole number. The tool prints Markdown with a short reason for each note. Reply with it exactly as it is, with nothing added.
