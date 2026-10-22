---
name: note-done
description: Mark one of the user's notes as done, by its number or by describing it (for example "/notemind:note-done 3" or "/notemind:note-done my meeting with sara").
argument-hint: <note number or a description of it>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Mark a note as done.

What the user typed:

$ARGUMENTS

1. If it is a single whole number, that is the note number. If it is empty, ask which note they mean (suggest `/notemind:note-list`) and stop. Otherwise it describes the note.

Finding the note (when the user describes it instead of giving a number): pick the few words that would appear in that note (names, projects, things; drop filler and the words that describe the change) and run, putting the words between the markers exactly:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact --json search --open - <<'NOTESCOS_EOF'
<words here>
NOTESCOS_EOF
```

The result is a JSON list of open notes, best first. Use a note only if it clearly is the one meant. If several could be, or none match, list the candidates as `#<id> <text>` (suggest `/notemind:note-list` if there are none), ask which one, and stop. Never guess.

2. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact done <number>` and reply with its Markdown output exactly as it is. If the tool reports that no such note exists, say so and suggest `/notemind:note-list`.
