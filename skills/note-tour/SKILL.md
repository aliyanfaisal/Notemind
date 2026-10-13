---
name: note-tour
description: A 2-minute guided tour of Notemind: save a sample note, find it, ask about it, finish it, and clean up.
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *) Bash(date *)
---
Walk the user through Notemind with one sample note. Keep every message to a few lines. Do each step, show its result, then ask them to say "next" before the following step. Use `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos"` (written `notescos` below) and reply with its Markdown exactly as printed.

1. **Save.** Say you will save a sample note whose date is read from the sentence. Run:
```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact add --due <tomorrow 15:00 as YYYY-MM-DDTHH:MM> - <<'NOTESCOS_EOF'
Tour sample: Sara owes me 500 USD, call her tomorrow at 3pm
NOTESCOS_EOF
```
Work out tomorrow's date from `date "+%Y-%m-%d %A"`. Note the id in the reply.
2. **See it.** Run `notescos --redact today` and point out the Money table. Mention `note-top` ranks notes and `note-check` finds what needs attention.
3. **Ask.** Run `notescos --redact --json search Sara` and answer "who is Sara in my notes?" citing the note as `#<id>`. Mention `note-ask`.
4. **Finish.** Run `notescos done <id>`. Mention `note-edit` and `note-snooze` for changes.
5. **Clean up.** Run `notescos forget <id>` so the sample is not left behind.
6. **Wrap up.** Give a five-line cheat sheet: `note-add` (save), `note-today` (what is due), `note-ask` (questions), `note-edit` and `note-snooze` (change), `note-help` (everything). Say that starting a prompt with `#note` also saves one quickly.

If the user wants to stop at any point, run step 5 first and stop.
