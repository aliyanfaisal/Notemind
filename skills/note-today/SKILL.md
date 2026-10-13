---
name: note-today
description: Show what is overdue, due today and coming up in the user's notes. Use when the user asks what is due, what they need to do, or for their notes briefing.
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Here is the user's overdue and due-today notes, produced just now by the tool as Markdown:

!`"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact today`

Reply with that Markdown exactly as it is (same headings, tables and emoji), without rewording, adding or removing notes. Do not add an introduction, apart from the question below. If something is overdue, you may end with one short line suggesting `note-done <number>`.

If the Markdown ends with a line saying notes "need your input", add one short question after it asking, for each such note, what date they meant (or whether to keep it as it is). When they answer, run `/notemind:note-edit` for that note with `--due <date>` or `--confirm`. Never guess the date for them.
