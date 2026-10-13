---
name: note-forget
description: Permanently delete a note, all notes in a project, or every note.
argument-hint: <note number> | --project NAME | --all
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Delete notes. This cannot be undone.

What the user typed:

$ARGUMENTS

1. Work out which of these they want, and use only that:
   - a note number: `forget <number>` deletes that note at once
   - a project: `forget --project NAME`
   - everything: `forget --all`
   If it is unclear, ask which one they mean and stop.
2. Run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact forget <options>`. For a project or everything, the tool only previews what would be deleted and says nothing was deleted.
3. Show that preview as it is. Delete nothing more until the user clearly says yes in their next message. Only then run the same command again with `--yes` added.
4. Reply with the tool's Markdown exactly as it is. Never add `--yes` on your own.
