---
name: note-snooze
description: Hide one of the user's notes until later, for example "/notemind:note-snooze 3 tomorrow" or "/notemind:note-snooze 3 friday 9am".
argument-hint: <note number> <when it should come back>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Snooze a note: hide it from the startup banner and `note-today` until the time the user gives.

What the user typed:

$ARGUMENTS

Current date and time on the user's machine (use it to resolve dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. The first word must be a note number. If it is missing or not a whole number, ask which note they mean (suggest `/notemind:note-list`) and stop.
2. If the rest says to bring the note back now (for example "clear" or "unsnooze"), run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact snooze <number> --clear`.
3. Otherwise work out when the note should come back, using the current date and time above. Understand any phrasing ("end of next month", "after the weekend", "in a couple of days"). Write it as `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM` when a time of day is given or implied. A date without a time returns at the start of that day. If no time can be worked out, ask the user and stop. Never invent one. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact snooze <number> <that date>`.
4. The tool prints a short Markdown confirmation. Reply with it exactly as it is. If it reports an error (unknown note, or a time that has passed), say so plainly and stop.
