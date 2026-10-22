---
name: note-edit
description: Change one of the user's notes: its text, due date, priority, alert level, type, person, project or tags (for example "/notemind:note-edit 3 move it to friday" or "/notemind:note-edit change time to 10am for my meeting with sara").
argument-hint: "[note number] <what to change> [which note]"
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Edit a note.

What the user typed:

$ARGUMENTS

Current date and time on the user's machine (use it to resolve dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. Work out which note. If the first word is a whole number, that is the note number and the rest is the change. Otherwise the user described the note in words (for example "change time to 10am for my meeting with sara": the change is the time, the note is the meeting with Sara). Find it as described below, and use its `id` as `<number>`. If the request does not say what to change, ask what they want to change and stop.

Finding the note (when the user describes it instead of giving a number): pick the few words that would appear in that note (names, projects, things; drop filler and the words that describe the change) and run, putting the words between the markers exactly:

   ```
   "${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact --json search --open - <<'NOTESCOS_EOF'
   <words here>
   NOTESCOS_EOF
   ```

   The result is a JSON list of open notes, best first. Use a note only if it clearly is the one meant. If several could be, or none match, list the candidates as `#<id> <text>` (suggest `/notemind:note-list` if there are none), ask which one, and stop. Never guess.
   When the note was found by description, tell the user which one you changed (`#<id> <text>`).
2. Turn the request into options for the tool. Use only what the user asked for and change nothing else:
   - new text: `--text -` with the text on stdin (see below), exactly as the user wrote it
   - due date: `--due <YYYY-MM-DD or YYYY-MM-DDTHH:MM>` worked out from the current date and time above, or `--due none` to remove the date. Never invent a date the request does not imply.
   - `--priority 0|1|2|3`, `--alert normal|urgent|silent`, `--type task|followup|waiting_on|decision|idea|reference`
   - `--confirm` when the user accepts a note that was waiting for their input as it is (giving a new `--due` also confirms it)
   - `--person NAME`, `--project NAME` (`none` removes them), `--tag TAG` (repeat for several; this replaces all tags, `--tag none` clears them)
3. Run it. Changing the text does not change the due date; to move the date too, add `--due`.

Without new text (the new text, if any, never includes the words that only identify the note):

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact edit <number> <options>
```

With new text, put it between the marker lines exactly as the user wrote it (the quoted marker keeps quotes and symbols from breaking the shell):

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact edit <number> --text - <other options> <<'NOTESCOS_EOF'
<new text here>
NOTESCOS_EOF
```

4. The tool prints a Markdown summary of what changed. Reply with it exactly as it is. If it reports an error, say so plainly and stop.
