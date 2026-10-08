# Notes Chief of Staff

**Never forget a follow-up again.**

Notes Chief of Staff (`notescos`) is a free, open-source assistant for [Claude Code](https://claude.com/claude-code) that turns your notes into a personal chief of staff. Capture notes from any session, see your top priorities the moment you open Claude Code, and ask questions over everything you've written. Everything stays on your machine.

> **Status:** early development. The core store and `notescos add/list/done` CLI exist; Claude Code skills and hooks are next.

## Why

Notes pile up and nobody looks at them again. Promises, deadlines and "waiting on Sara" get buried. Notes Chief of Staff pushes the right note in front of you at the right time, without leaving the terminal where you already work.

## Planned features

- **Fast capture:** `/note call Sara Friday 3pm about the quote`, or start any prompt with `#note`.
- **Session briefing:** a short banner when Claude Code starts, such as "2 overdue · 3 due today · waiting on Sara (4d)".
- **Priority ranking:** `/notes-top` orders your notes with a transparent score and tells you why.
- **Follow-up tracking:** notice promises you made and replies you're waiting for.
- **Ask your notes:** `/notes-ask what did I decide about the database?` answers with cited notes.
- **Clarifying questions:** ambiguous notes are confirmed with you before they trigger alerts.
- **Money tracking (v0.3):** who owes you, and what you owe.
- **Local-first and private:** one SQLite file, no network calls, no API keys.

## Commands (planned)

| Command | What it does |
|---|---|
| `/note <text>` | Add a note |
| `/notes-today` | Due today, overdue, waiting on others |
| `/notes-top [N]` | Top N notes by priority |
| `/notes-check` | Full manual check of everything that needs attention |
| `/notes-ask <question>` | Answer a question from your notes |
| `/notes-list` | Browse and filter notes |
| `/notes-done <id>` · `/notes-snooze <id> <when>` · `/notes-edit <id>` | Manage a note |
| `/notes-sync` | Find commitments in past sessions (opt-in) |
| `/notes-settings` | Alert level and scan permissions |
| `/notes-forget` | Delete notes |
| `/notes-help` · `/notes-tour` | Built-in guide |

## Install

Manual install only for now. An `install.sh` will ship with v0.1.

## Contributing

Ideas and feedback are welcome once the first release lands.

## License

[MIT](LICENSE)
