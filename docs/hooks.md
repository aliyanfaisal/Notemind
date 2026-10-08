# What the hook does

Notes Chief of Staff registers exactly **one** Claude Code hook. This page says what it runs, what it reads, and what it can and cannot do, so you can decide whether to trust it.

## What gets installed

Installing the plugin adds these, all inside the plugin folder Claude Code manages:

| What | Where |
|---|---|
| The `/cos:notes-add`, `/cos:notes-today`, `/cos:notes-list`, `/cos:notes-done`, `/cos:notes-help` commands | `skills/` |
| One `SessionStart` hook | `hooks/hooks.json` |
| A small launcher that runs the bundled Python code | `scripts/notescos` |

Your own `settings.json` is not edited. Your notes are stored in `~/.notescos/notes.db` (created on first use) and are **not** removed when you uninstall the plugin. Delete that folder to erase them.

## The SessionStart hook

Registered command:

```
"${CLAUDE_PLUGIN_ROOT}"/scripts/notescos hook session-start      (timeout: 10 s)
```

Each time Claude Code starts, resumes or clears a session, it:

1. Reads the small JSON message Claude Code sends on stdin (only the `source` field is used).
2. Opens `~/.notescos/notes.db` and reads your open notes.
3. Prints one JSON object to stdout:
   - `systemMessage`: the banner shown to you.
   - `hookSpecificOutput.additionalContext`: the same text given to Claude so it can help you act on it.

It does **not**: make network calls, write anything except a one-time `~/.notescos/welcomed` marker and an error log, read your code or transcripts, or run any other program.

### When it stays quiet
- Nothing is overdue, due today or due in the next 2 days: no output at all.
- The session event is `compact` (context was just trimmed): no banner.
- Notes set to `--alert silent` are never included.

### It cannot break your session
Any error (for example a damaged database) is caught. The hook exits with code 0, prints nothing, and appends the details to `~/.notescos/log`. Typical run time is about 85 ms.

## The commands (skills)

- `/cos:notes-add` and `/cos:notes-done` can only be run by you (`disable-model-invocation: true`), so Claude never saves or closes a note on its own.
- `/cos:notes-today`, `/cos:notes-list` and `/cos:notes-help` can also be used by Claude when you ask things like "what's due?".
- Every skill is limited to running this tool (`allowed-tools: Bash(notescos *)`).
- `/cos:notes-add` passes your text to the tool on stdin through a quoted here-document, so quotes, `$(...)` and backticks in a note are never executed.

## Checking it yourself

```bash
# What would the hook print right now?
echo '{"source":"startup"}' | ./scripts/notescos hook session-start

# Try the plugin without installing it
claude --plugin-dir .
```
