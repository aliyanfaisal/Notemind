---
name: note-sync
description: Look through the messages the user typed in earlier sessions of this project, propose notes for commitments and follow-ups, and save only the ones they approve.
argument-hint: enable | disable | status | (nothing to scan)
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Find commitments the user made in earlier sessions and offer to save them as notes.

What the user typed:

$ARGUMENTS

1. If it is `enable`, `disable` or `status`, run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" sync <that word>`, show the reply as it is, and stop. For `enable`, add one line: scanning reads only messages the user typed in this project's sessions, with keys, passwords and card numbers masked first, and those messages are shown to Claude.
2. Otherwise scan:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --json sync scan
```
   If it says scanning is off, tell the user to run `note-sync enable` first, and stop.
3. The result has `messages` (what the user typed, masked), `masked` (how many secrets were hidden) and `older_skipped`. Pick out only clear commitments, promises, follow-ups, things waiting on someone, and money owed or due. Ignore questions, instructions to Claude, and anything vague. If `masked` is above 0, tell the user "skipped N possible secret(s)".
4. If nothing qualifies, say so, run `sync mark`, and stop.
5. Show the proposals as a numbered list: the note text, the date if one was stated, and the session date it came from. Do not save anything yet. Ask which numbers to save. Never invent dates, people or amounts that are not in the messages.
6. After the user answers, save each approved one:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact add - --source transcript --source-ref <session> --branch <branch> <<'NOTESCOS_EOF'
<note text>
NOTESCOS_EOF
```
   Add `--due YYYY-MM-DD` only when the message gave an exact date. Show each reply as it is.
7. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" sync mark` so the same messages are not offered again, whether or not any were saved.
