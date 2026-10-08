<div align="center">

# 📌 Notemind

### Write notes in plain sentences. Get reminded when they matter.

A **Claude Code plugin** that reads the date in your sentence, stores the note on your own machine, and shows what is overdue or due soon each time you start a session.

[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757?style=for-the-badge)](#install)
[![Local only](https://img.shields.io/badge/data-stays%20local-2ea44f?style=for-the-badge)](#privacy)
[![No dependencies](https://img.shields.io/badge/dependencies-none-blue?style=for-the-badge)](#requirements)
[![MIT](https://img.shields.io/badge/license-MIT-lightgrey?style=for-the-badge)](LICENSE)

Runs in Claude Code: the terminal, the VS Code extension and the **Code** tab of the Claude desktop app.

</div>

---

## Overview

Follow-ups get lost because the place you write them down is not the place you look. Notemind keeps them inside Claude Code, where you already work:

```text
> /notemind:note-add call Sara tomorrow at 3pm about the quote
Added [ ] #1 call Sara tomorrow at 3pm about the quote (due 2026-10-10T15:00)
```

The next time a session starts:

```text
📌 Notes: 1 overdue · 1 due today
  ! #4 send the invoice (overdue 2d)
  • #1 call Sara about the quote (today 15:00)
  /notemind:note-today for details
```

## Features

| | |
|---|---|
| **Any date, in plain words** | Claude reads your sentence in the session and works out the exact date and time: "tomorrow at 3pm", "in the next 2 hours", "3rd Friday of next month". The reply tells you how it was read. |
| **Startup briefing** | Overdue, due today, and due in the next 2 days appear when a session starts. The banner is skipped when nothing needs attention. |
| **Daily view** | `/notemind:note-today` groups notes into overdue, due today, the next 7 days, and no date. |
| **Private** | One SQLite file on your disk. No account, no network calls, no API keys. |
| **Light** | Python standard library only. |

## Requirements

- Claude Code (CLI, VS Code extension, or the Code tab of the desktop app)
- Python 3.9 or newer (`python3` on your PATH)

## Install

In Claude Code:

```text
/plugin marketplace add <you>/notemind
/plugin install notemind@notemind
```

Start a new session and run `/notemind:note-help`.

<details>
<summary>Terminal install, local clone, or the desktop app's Add menu</summary>

**Terminal**

```bash
claude plugin marketplace add <you>/notemind
claude plugin install notemind@notemind
```

**Try a local clone without installing**

```bash
git clone https://github.com/<you>/notemind.git
claude --plugin-dir ./notemind
```

**Desktop app:** open Plugins, choose Add, and upload a zip of this repository (`.claude-plugin`, `skills`, `hooks`, `scripts`, `core`). Use Notemind from the **Code** tab. See [Where it runs](#where-it-runs).

**Uninstall:** `/plugin uninstall notemind@notemind`. Your notes remain in `~/.notescos/` until you delete that folder.

</details>

## Where it runs

Notemind stores notes in a file on your computer, so it only works where Claude Code runs on your computer.

| Where you use Claude | Works | Notes are saved |
|---|---|---|
| Terminal (`claude`) | Yes | `~/.notescos/notes.db` on your machine |
| VS Code extension | Yes | `~/.notescos/notes.db` on your machine |
| Desktop app, **Code** tab (a local session) | Yes | `~/.notescos/notes.db` on your machine |
| Desktop app, Chat or Cowork | **Not supported** | These run in an isolated sandbox. A note saved there stays in the sandbox and is not written to your computer. |
| claude.ai in the browser | **Not supported** | No access to your local files |

If a command runs from a path starting with `/mnt/`, you are in a sandbox. Switch to a Code session.

## Commands

Notemind has five commands. Claude Code and the Claude desktop app's Code tab list them slightly differently, so here is exactly what you will see in each.

### What you will see

| Command | Terminal (Claude Code CLI) | Claude desktop app (slash menu) |
|---|---|---|
| Save a note | `/notemind:note-add` | `note-add` |
| What needs attention | `/notemind:note-today` | `note-today` |
| Browse notes | `/notemind:note-list` | `note-list` |
| Finish a note | `/notemind:note-done` | `note-done` |
| Guide | `/notemind:note-help` | `note-help` |

- **Terminal:** commands carry the plugin name in front, `/notemind:` followed by the command. Typing `/note` narrows the menu to them.
- **Desktop app:** the menu shows the command name only (`note-add`), with "Notemind plugin" written under it. Type `/note-add` or pick it from the menu. This is why every command name starts with `note-`: it stays clear even without the prefix.

### What each command does

| Command | Arguments | What it does |
|---|---|---|
| `note-add` | `<text>` | Save a note. A date in the sentence becomes the due date. |
| `note-today` | none | Overdue, due today, the next 7 days, and notes without a date. |
| `note-list` | `[--all] [--project NAME] [--type TYPE]` | Browse notes. `--all` includes finished ones. |
| `note-done` | `<number>` | Mark a note as finished. |
| `note-help` | none | Show the built-in guide. |

### Examples

In the terminal:

```text
/notemind:note-add send the invoice tomorrow at 3pm
/notemind:note-add renew the domain next friday
/notemind:note-add dentist 04/12          read as day/month; the reply says how it was understood
/notemind:note-today
/notemind:note-done 3
```

In the desktop app, the same without the prefix:

```text
/note-add send the invoice tomorrow at 3pm
/note-today
/note-done 3
```

The rest of this README writes commands in their terminal form.

## How dates are read

When you run `/notemind:note-add`, Claude interprets your sentence with the current date and time from your machine and passes the exact result to Notemind, which stores it. Any phrasing Claude can understand works, and every reply includes a line such as:

```text
Added [ ] #1 pay the invoice on the 3rd friday of next month (due 2026-11-20)
Read "3rd Friday of next month" as Fri 20 Nov 2026.
```

- **No date in the sentence:** the note is saved without a due date (see below).
- **Ambiguous dates:** `04/12` is read day-first unless you write month-first clearly, and the reply says which way it went.
- **Wrong reading:** editing is not available yet. Run the command again with the date written out, for example `22 sep`.
- **Without Claude:** the bundled command line tool (`scripts/notescos add "text"`) falls back to built-in rules that understand common phrasings such as "tomorrow", "next friday", "22 sep" and "in 2 hours". It makes no network calls.

## How notes without a date behave

Not every note has a deadline: "waiting on the invoice from Sara" or "look into caching options". These are saved like any other note, with no due date. Today that means:

| | With a date | Without a date |
|---|---|---|
| Saved on your machine | Yes | Yes |
| Shown in `/notemind:note-today` | Under Overdue, Due today or Coming up | Under **No date** (first 5, then a count) |
| Shown in `/notemind:note-list` | Yes | Yes |
| In the startup banner | Yes, when due within 2 days or overdue | **No** |
| Becomes overdue | Yes | **No** |

So an undated note will not interrupt you. It waits until you open `/notemind:note-today` or `/notemind:note-list`. If you want it to surface, give it a date: `/notemind:note-add chase Sara about the invoice on friday`.

This version does not recognise "waiting on" as a follow-up, and it does not remind you as an undated note gets older. Both are on the roadmap.

## Privacy

- Notes are stored in `~/.notescos/notes.db`.
- The plugin makes no network calls and needs no credentials.
- It registers one hook (`SessionStart`). [docs/hooks.md](docs/hooks.md) lists what it reads and what it cannot do.
- `/notemind:note-add` and `/notemind:note-done` run only when you invoke them. Claude does not save or close notes on its own.

## Limitations

- Notes are local to one machine. There is no sync, and the plugin does not work in claude.ai or in the desktop app's Chat and Cowork modes (see [Where it runs](#where-it-runs)).
- Alerts appear only while Claude Code is open. There is no background process.
- Dates such as `04/12` are read day-first. Set `NOTESCOS_DATE_ORDER=mdy` for month-first.
- Editing a note is not available yet. Add a corrected note and mark the old one done.

## Roadmap

| Planned | Description |
|---|---|
| Follow-up awareness | Recognise "waiting on" and "remind me to ask" notes, and raise them as they age |
| Priority ranking | `note-top`, a ranked list with the reason for each position |
| Ask your notes | Questions over your notes, answered with the notes cited |
| Snooze and edit | Move a due date or change a note |
| Money tracking | Who owes you, and what you owe |

## Development

```bash
git clone https://github.com/<you>/notemind.git
cd notemind
claude --plugin-dir .                                  # run the plugin from source
claude plugin validate .                               # check the manifests
```

```text
.claude-plugin/   plugin and marketplace manifests
skills/           the /notemind:note-* commands
hooks/            SessionStart hook
scripts/          launcher for the Python core
core/             parser, store, briefing and CLI (notescos)
```

## License

[MIT](LICENSE)
