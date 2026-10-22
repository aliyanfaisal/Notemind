---
name: note-forget
description: Permanently delete a note, all notes in a project, or every note.
argument-hint: <note number or description> | --project NAME | --all
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Delete notes. This cannot be undone.

What the user typed:

$ARGUMENTS

1. Work out which of these they want, and use only that:
   - a note number: `forget <number>` deletes that note at once
   - a note described in words (for example "the meeting with sara"): find it as described below. Because this is a guess, do not delete yet: show `#<id> <text>`, ask the user to confirm, and only after a clear yes in their next message run `forget <id>`.
   - a project: `forget --project NAME`
   - everything: `forget --all`
   If it is unclear, ask which one they mean and stop.
2. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact forget <options>`. For a project or everything, the tool only previews what would be deleted and says nothing was deleted.
3. Show that preview as it is. Delete nothing more until the user clearly says yes in their next message. Only then run the same command again with `--yes` added.
4. Reply with the tool's Markdown exactly as it is. Never add `--yes` on your own.

Finding the note (when the user describes it instead of giving a number): pick the few words that would appear in that note (names, projects, things; drop filler and the words that describe the change) and run, putting the words between the markers exactly:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact --json search --open - <<'NOTESCOS_EOF'
<words here>
NOTESCOS_EOF
```

The result is a JSON list of open notes, best first. Use a note only if it clearly is the one meant. If several could be, or none match, list the candidates as `#<id> <text>` (suggest `/notemind:note-list` if there are none), ask which one, and stop. Never guess.

