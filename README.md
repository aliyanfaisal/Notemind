<p align="center">
  <img src="assets/notemind-logo.png" alt="Notemind" width="480">
</p>

<p align="center"><strong>Notes and follow-ups for Claude Code. Write them in plain words, get reminded when they are due.</strong></p>

Notemind is a Claude Code plugin. Type `call Sara tomorrow at 3pm`, and it works out the date, saves the note on your computer, and shows what is overdue or due soon every time you start a session.

- **Plain-language capture:** dates and times are read from your sentence.
- **Local by default:** one file on your machine (`~/.notescos/notes.db`), no account, no network calls of its own.
- **Startup briefing:** overdue and upcoming notes appear when a session starts.
- **Money and follow-ups:** track who owes you, what you owe, and what you are waiting on.
- **Ask your notes:** `note-ask what is pending for Ali?` answers with note numbers.

## Install

Requires [Claude Code](https://claude.com/claude-code) and Python 3.9+.

**Terminal**

```bash
claude plugin marketplace add aliyanfaisal/notemind
claude plugin install notemind@notemind
```

**VS Code or the Claude app (Code tab)**

```text
/plugin marketplace add aliyanfaisal/notemind
/plugin install notemind@notemind
```

> ⚠️ In the Claude app, install and use it from the **Code** tab, not Cowork or Chat. Those run in a cloud sandbox, so notes cannot be saved to your computer.

Prefer a file? Download `notemind-v<version>.zip` from [Releases](https://github.com/aliyanfaisal/notemind/releases/latest), open **Plugins → Add** in a Code tab, and select the zip.

Then start a new session and run `/notemind:note-tour` for a two-minute walkthrough.

## Quick start

```text
/notemind:note-add send the invoice tomorrow at 3pm
/notemind:note-add Ali owes me 15k PKR, due Friday
/notemind:note-today
/notemind:note-ask what is pending for Ali?
/notemind:note-done 1
```

You can also start any prompt with `#note` to save a note instantly (see the [privacy catch](docs/guide.md#quick-capture-with-note)).

## Commands

In the terminal and VS Code, commands are `/notemind:<name>`. In the Claude app's Code tab, use `/<name>`.

**Capture**

| Command | What it does |
|---|---|
| `note-add <text>` | Save a note. The date, amount and person are read from your sentence. |
| `#note <text>` | Save a note straight from a prompt, with no model call. |
| `note-sync [enable\|disable\|status]` | Find commitments in your past sessions and save the ones you approve. Off until enabled. |

**Review**

| Command | What it does |
|---|---|
| `note-today` | Overdue, due today, and the next 7 days. |
| `note-top [N]` | The notes that matter most right now, with the reason for each. |
| `note-check` | Everything needing attention, including follow-ups waiting too long. |
| `note-list [--all] [--project X] [--type T] [--from D] [--to D]` | Browse your notes. |
| `note-board [overdue\|due\|next 2 days\|22 sep]` | Show notes on a visual board. |
| `note-ask <question>` | Ask about your notes; answers cite note numbers. |

**Manage**

| Command | What it does |
|---|---|
| `note-edit <n> [--due X] [--text X] [--priority N] …` | Change a note. Plain words work too: `note-edit 3 move it to friday`. |
| `note-snooze <n> <when>` | Hide a note until later, e.g. `tomorrow` or `3 days`. |
| `note-done <n>` | Mark a note finished. |
| `note-forget <n> \| --project X \| --all` | Delete notes permanently. Projects and "all" are previewed first. |

**Setup**

| Command | What it does |
|---|---|
| `note-settings [alert quiet\|normal\|loud]` | Set how much the startup banner shows. |
| `note-tour` | Guided two-minute tour. |
| `note-help` | Show the command list. |

## Privacy

- Notes live only on your computer. Notemind has no server and makes no network calls.
- Most commands run locally and Claude never sees them. Claude sees note text only when it has to help (an unreadable date, `note-ask`, the startup banner, `note-sync`), and sensitive data is masked first.
- The notes board can publish to claude.ai, but only if you say yes each time.
- A small hook checks each prompt for `/note-…` commands and `#note`, and stores nothing else.

Details and the list of what gets masked: [docs/privacy.md](docs/privacy.md).

## Documentation

- [Guide](docs/guide.md): how each feature works (money, board, banner levels, ranking, sync)
- [Privacy](docs/privacy.md): what reaches Claude, and sensitive-data masking
- [What the hook does](docs/hooks.md)
- [Overview page](https://aliyanfaisal.com/open-source/notemind)

To uninstall: `/plugin uninstall notemind@notemind`. Your notes stay in `~/.notescos/` until you delete that folder.

## License

[MIT](LICENSE)
