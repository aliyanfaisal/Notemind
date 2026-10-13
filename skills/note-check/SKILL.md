---
name: note-check
description: Run a full check of the user's notes: overdue, due today, due in the next 2 days, and follow-ups waiting too long for a reply.
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Here is the user's full notes check, produced just now by the tool as Markdown:

!`"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact check`

Reply with that Markdown exactly as it is, without rewording, adding or removing notes. Do not add an introduction, apart from the question below.

If the Markdown ends with a line saying notes "need your input", add one short question after it asking, for each such note, what date they meant (or whether to keep it as it is). When they answer, run `/notemind:note-edit` for that note with `--due <date>` or `--confirm`. Never guess the date for them.
