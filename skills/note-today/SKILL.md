---
name: note-today
description: Show what is overdue, due today and coming up in the user's notes. Use when the user asks what is due, what they need to do, or for their notes briefing.
allowed-tools: Bash(*/scripts/notescos *)
---
Here is the user's current notes summary, produced just now by the tool:

!`${CLAUDE_PLUGIN_ROOT}/scripts/notescos today`

Show it to the user in a clean, compact form without changing any note text, ids or dates. Do not invent notes that are not listed. If something is overdue, end with one line suggesting the most useful next step (for example "/notemind:note-done 4 if it is finished").
