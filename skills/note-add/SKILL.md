---
name: note-add
description: Save a note or follow-up, with the due date read from your sentence (for example "call Sara on 22 sep at 3pm").
argument-hint: <note text, with a date if it has one>
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *)
---
Save a note with Notemind.

The note text is everything the user typed after the command:

$ARGUMENTS

Current date and time on the user's machine (use it to resolve relative dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. If the text above is empty, ask the user what they want to note, then stop.
2. Work out the due date and time the user meant, using the current date and time above. Understand any phrasing: "in the next 2 hours", "end of next month", "the 3rd Friday of May", "two weeks from Monday", "tonight", dates in other styles, and so on. Write it as `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM` when a time of day is given or implied (for example "in 2 hours" is the current time plus two hours). If the note contains no date or time, use `none`. If a date is truly ambiguous (for example 04/12), prefer day/month unless the user clearly writes month/day, and say so in step 4. Never invent a date the text does not imply.
3. Save it by running the command below. Put the note text between the two marker lines exactly as the user wrote it (do not fix, shorten or reword it) and put your date after `--due`. The quoted marker keeps quotes and symbols from breaking the shell.

```
${CLAUDE_PLUGIN_ROOT}/scripts/notescos add --due <YYYY-MM-DD or YYYY-MM-DDTHH:MM or none> - <<'NOTESCOS_EOF'
<note text here>
NOTESCOS_EOF
```

4. Reply with the tool's output. If you found a date, add one short line saying how you read it, for example: Read "in the next 2 hours" as Fri 9 Oct, 16:00. If you had to guess, say so and tell the user to run the command again with the date written out, because editing notes is not available yet. If the output has a line starting with `!` or `⚠`, include it. Say nothing else.
5. Do not save the note anywhere else and do not create tasks or files.
