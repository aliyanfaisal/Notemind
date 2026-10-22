---
name: note-snooze
description: Hide one of the user's notes until later, for example "/notemind:note-snooze 3 tomorrow" or "/notemind:note-snooze tomorrow 9am for the sara meeting".
argument-hint: "[note number] <when it should come back> [which note]"
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Snooze a note: hide it from the startup banner and `note-today` until the time the user gives.

What the user typed:

$ARGUMENTS

Current date and time on the user's machine (use it to resolve dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. Work out which note. If the first word is a whole number, that is the note number and the rest says when. Otherwise the user described the note in words (for example "friday for the sara meeting"): separate the time from the description and find the note as described below, using its `id` as `<number>`. If no note can be told, ask which one they mean (suggest `/notemind:note-list`) and stop.

Finding the note (when the user describes it instead of giving a number): pick the few words that would appear in that note (names, projects, things; drop filler and the words that describe the change) and run, putting the words between the markers exactly:

   ```
   "${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact --json search --open - <<'NOTESCOS_EOF'
   <words here>
   NOTESCOS_EOF
   ```

   The result is a JSON list of open notes, best first. Use a note only if it clearly is the one meant. If several could be, or none match, list the candidates as `#<id> <text>` (suggest `/notemind:note-list` if there are none), ask which one, and stop. Never guess.
   When the note was found by description, tell the user which one you snoozed (`#<id> <text>`).
2. If the rest says to bring the note back now (for example "clear" or "unsnooze"), run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact snooze <number> --clear`.
3. Otherwise work out when the note should come back, using the current date and time above. Understand any phrasing ("end of next month", "after the weekend", "in a couple of days"). Write it as `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM` when a time of day is given or implied. A date without a time returns at the start of that day. If no time can be worked out, ask the user and stop. Never invent one. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact snooze <number> <that date>`.
4. The tool prints a short Markdown confirmation. Reply with it exactly as it is. If it reports an error (unknown note, or a time that has passed), say so plainly and stop.
