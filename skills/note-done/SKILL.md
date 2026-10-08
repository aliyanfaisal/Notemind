---
name: note-done
description: Mark one of the user's notes as done by its number (for example "/notemind:note-done 3").
argument-hint: <note number>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Mark a note as done.

Requested note number: $ARGUMENTS

If the request is not a single whole number, ask the user which note they mean (suggest `/notemind:note-list`) and stop. Otherwise run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" done <number>` and show the output. If the tool reports that no such note exists, say so and suggest `/notemind:note-list`.
