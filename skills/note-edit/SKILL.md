---
name: note-edit
description: Change one of the user's notes: its text, due date, priority, alert level, type, person, project or tags (for example "/notemind:note-edit 3 move it to friday").
argument-hint: <note number> <what to change>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Edit a note.

What the user typed:

$ARGUMENTS

Current date and time on the user's machine (use it to resolve dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. The first word must be a note number. If it is missing or not a whole number, ask which note they mean (suggest `/notemind:note-list`) and stop. If the rest does not say what to change, ask what they want to change and stop.
2. Turn the request into options for the tool. Use only what the user asked for and change nothing else:
   - new text: `--text -` with the text on stdin (see below), exactly as the user wrote it
   - due date: `--due <YYYY-MM-DD or YYYY-MM-DDTHH:MM>` worked out from the current date and time above, or `--due none` to remove the date. Never invent a date the request does not imply.
   - `--priority 0|1|2|3`, `--alert normal|urgent|silent`, `--type task|followup|waiting_on|decision|idea|reference`
   - `--person NAME`, `--project NAME` (`none` removes them), `--tag TAG` (repeat for several; this replaces all tags, `--tag none` clears them)
3. Run it. Changing the text does not change the due date; to move the date too, add `--due`.

Without new text:

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
