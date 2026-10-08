---
name: notes-add
description: Save a note or follow-up, with the due date read from your sentence (for example "call Sara on 22 sep at 3pm").
argument-hint: <note text, with a date if it has one>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *)
---
Save a note with Notes Chief of Staff.

The note text is everything the user typed after the command:

$ARGUMENTS

1. If the text above is empty, ask the user what they want to note, then stop.
2. Save it by running the command below, putting the note text between the two marker lines exactly as the user wrote it (do not fix, shorten or reword it, and do not work out dates yourself, the tool reads them). The quoted marker keeps quotes and symbols from breaking the shell.

```
${CLAUDE_PLUGIN_ROOT}/scripts/notescos add - <<'NOTESCOS_EOF'
<note text here>
NOTESCOS_EOF
```

3. Reply with the tool's output, nothing more. If the output has a line starting with `!`, add one short sentence asking whether that reading is right. If it is wrong, tell the user to run /note again with the month spelled out (for example "22 sep"), because editing notes is not available yet.
4. Do not save the note anywhere else and do not create tasks or files.
