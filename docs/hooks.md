# What the hook does

Notemind registers exactly **two** Claude Code hooks: `SessionStart` and `UserPromptSubmit`. This page says what it runs, what it reads, and what it can and cannot do, so you can decide whether to trust it.

## What gets installed

Installing the plugin adds these, all inside the plugin folder Claude Code manages:

| What | Where |
|---|---|
| The `/notemind:note-add`, `note-today`, `note-list`, `note-edit`, `note-snooze`, `note-done`, `note-board` and `note-help` commands | `skills/` |
| One `SessionStart` hook and one `UserPromptSubmit` hook | `hooks/hooks.json` |
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

It does **not**: make network calls (this hook and the other one never do), write anything except a one-time `~/.notescos/welcomed` marker and an error log, read your code or transcripts, or run any other program.

### When it stays quiet
- Nothing is overdue, due today or due in the next 2 days: no output at all.
- The session event is `compact` (context was just trimmed): no banner.
- Notes set to `--alert silent` are never included.

### It cannot break your session
Any error (for example a damaged database) is caught. The hook exits with code 0, prints nothing, and appends the details to `~/.notescos/log`. Typical run time is about 85 ms.

## The UserPromptSubmit hook

Registered command:

```
"${CLAUDE_PLUGIN_ROOT}"/scripts/notescos hook prompt-submit      (timeout: 10 s)
```

Its job is to keep your notes out of the model whenever Notemind can do the work itself. Claude Code runs it before each prompt you send, and it:

1. Reads the JSON message on stdin and looks only at the `prompt` field.
2. Does nothing unless the prompt starts with `/note-add`, `/note-today`, `/note-list`, `/note-done`, `/note-edit` or `/note-snooze` (with or without the `notemind:` prefix). Every other prompt is ignored, not stored and not logged.
3. Handles the command itself and **blocks the prompt**, so Claude never sees it and no model call is made:
   - `note-today`, `note-list` and `note-done` always run locally. They only read or update your notes, so they need no interpretation. Bad arguments get a short error shown to you.
   - `note-edit` and `note-snooze` run locally when written with options (`note-edit 3 --due "friday 5pm"`) or a date the built-in rules can read (`note-snooze 3 tomorrow`, `3 days`).
   - `note-add` reads the date with the built-in rules (`parse.py`, no AI). A clear date, or no date-like words at all, is saved locally.
4. Lets the prompt through to Claude only for a `note-add` the rules cannot be sure of, a `note-edit` or `note-snooze` written in plain words or with a date the rules cannot read: words like "end of next month" or "next month at 3pm" left unread, or two different dates in one note. Claude then reads the note and works out the date, as `/notemind:note-add` always has.

Limits to know about:
- A hook cannot rewrite your prompt, so when the rules cannot read a note, **the whole note text goes to Claude**, not just the date words.
- The hook runs on every prompt you send (about 85 ms), though it acts only on the four commands above.
- If the hook fails for any reason it exits quietly and the prompt carries on to the command as usual.

## Sensitive data masking

`core/notescos/redact.py` finds passwords, API keys and tokens, private keys, card numbers, IBANs, US social security numbers, email addresses, international phone numbers and passwords in links, using patterns and checksums only (no AI, no network). Wherever note text is handed to Claude or sent to claude.ai, matches are replaced with `*****`:

- the `additionalContext` of the SessionStart hook (the banner you see on screen is not masked),
- the skills' tool output, because the skills call `notescos --redact …`,
- the Claude artifact board (`board --artifact` always masks).

Your stored notes are not changed. The prompt hook also refuses to pass a `note-add` that contains sensitive data to Claude just so it can read a date: it tells you and saves nothing.

Detection is not exhaustive. See the README for what it covers and what it cannot catch.

## What still goes through Claude

Notes are stored only on your computer and Notemind makes no network calls of its own. Claude still sees note text in these cases, like anything else in a Claude Code session:
- a `note-add`, `note-edit` or `note-snooze` whose date the rules could not read, or a `note-edit` written in plain words;
- the startup banner, because your overdue notes are given to Claude as context;
- `note-board`, which Claude runs. Its Claude artifact option asks first, then publishes a private copy of your notes to claude.ai.

## The commands (skills)

- `/notemind:note-add`, `note-edit`, `note-snooze`, `note-done` and `note-board` can only be run by you (`disable-model-invocation: true`), so Claude never saves or closes a note on its own.
- `/notemind:note-today`, `/notemind:note-list` and `/notemind:note-help` can also be used by Claude when you ask things like "what's due?". When you type the slash command yourself, the hook above answers it without Claude.
- `/notemind:note-board` is the one command that can send notes off your machine. Before publishing a Claude artifact it asks you to confirm, tells you the notes go to claude.ai, and publishes the artifact as private. The Python tool itself never makes a network call: it only writes an HTML file, and Claude's Artifact tool does the upload only after you choose it. Choosing the local file writes `~/.notescos/board.html` and nothing else.
- Every skill is limited to running this tool (`allowed-tools: Bash(notescos *)`).
- `/notemind:note-add` passes your text to the tool on stdin through a quoted here-document, so quotes, `$(...)` and backticks in a note are never executed.

## Checking it yourself

```bash
# What would the hook print right now?
echo '{"source":"startup"}' | ./scripts/notescos hook session-start

# Try the plugin without installing it
claude --plugin-dir .
```
