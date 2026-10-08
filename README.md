<div align="center">

# 📌 Notes Chief of Staff

### Your notes, finally working for you.

**A Claude Code plugin that remembers your follow-ups, reads the dates in your sentences, and tells you what needs attention the moment you open Claude.**

[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757?style=for-the-badge)](#install)
[![Local first](https://img.shields.io/badge/100%25-local-2ea44f?style=for-the-badge)](#privacy)
[![No dependencies](https://img.shields.io/badge/dependencies-none-blue?style=for-the-badge)](#install)
[![MIT](https://img.shields.io/badge/license-MIT-lightgrey?style=for-the-badge)](LICENSE)

Works in the **Claude Code desktop app**, the **VS Code extension** and the **terminal**.

</div>

---

## The problem

Notes pile up and nobody opens them again. *"Call Sara Friday."* *"Waiting on the invoice."* *"Renew the domain."* They sit in a file until the deadline is already behind you.

## The fix

Type a note the way you'd say it. Notes Chief of Staff understands the date, stores it, and brings it back **right when it matters**.

```text
> /cos:notes-add call Sara tomorrow at 3pm about the quote
✓ Added #1 call Sara tomorrow at 3pm about the quote (due 2026-10-10 15:00)
```

Next time you open Claude Code:

```text
📌 Notes: 1 overdue · 1 due today
  ! #4 send the invoice (overdue)
  • #1 call Sara about the quote (today 15:00)
  /cos:notes-today for details
```

No app to open. No inbox to check. It shows up where you already work.

## What you get

| | |
|---|---|
| ⚡ **Capture in a sentence** | `/cos:notes-add renew the domain next friday`. No forms, no date pickers. |
| 🗓️ **Dates understood** | "tomorrow at 3pm", "22 sep", "next friday". If it had to guess, it tells you. |
| 🔔 **Startup briefing** | Overdue, due today and next two days, shown when a session starts. Silent when there's nothing to say. |
| 🔒 **Private by design** | Everything lives in one file on your machine. No account, no cloud, no network calls. |
| 🪶 **Zero dependencies** | Pure Python standard library. Nothing to install but the plugin. |

## Install

You need Claude Code and Python 3.9+. Then run this inside Claude Code:

```text
/plugin marketplace add <you>/notes-chief-of-staff
/plugin install cos@notes-chief-of-staff
```

Start a new session and try `/cos:notes-help`.

<details>
<summary>Prefer the terminal, or want to try it from a local clone first?</summary>

```bash
claude plugin marketplace add <you>/notes-chief-of-staff
claude plugin install cos@notes-chief-of-staff

# or test a clone without installing anything
git clone https://github.com/<you>/notes-chief-of-staff.git
claude --plugin-dir ./notes-chief-of-staff
```

To remove it: `/plugin uninstall cos@notes-chief-of-staff`. Your notes stay in `~/.notescos/` until you delete that folder.

</details>

## Commands

| Command | What it does | Status |
|---|---|---|
| `/cos:notes-add <text>` | Save a note, with the date read from your sentence | ✅ |
| `/cos:notes-today` | Overdue, due today and coming up | ✅ |
| `/cos:notes-list` | Browse notes, filter by `--project`, `--type`, `--all` | ✅ |
| `/cos:notes-done <id>` | Mark a note finished | ✅ |
| `/cos:notes-help` | Built-in guide | ✅ |
| `/cos:notes-top` | Rank notes by priority, with the reason | 🔜 |
| `/cos:notes-ask <question>` | Ask questions over your notes, with citations | 🔜 |
| `/cos:notes-snooze` · `/cos:notes-edit` | Move or change a note | 🔜 |
| Money tracking | Who owes you, and what you owe | 🔜 |

## Privacy

- Notes are stored in a single SQLite file: `~/.notescos/notes.db`.
- The plugin makes **no network calls** and needs **no API keys**.
- It registers exactly **one** hook, and [docs/hooks.md](docs/hooks.md) lists what it reads and what it can't do.
- `/cos:notes-add` and `/cos:notes-done` can only be run by you. Claude never saves or closes a note on its own.

## Good to know

- Alerts appear when Claude Code is open. There's no background process in this version.
- Dates like `04/12` are read day-first. Set `NOTESCOS_DATE_ORDER=mdy` for month-first.

## Contributing

Ideas and feedback are welcome. Run the tests with `cd core && python3 -m unittest discover -s tests -t .`

## License

[MIT](LICENSE)
