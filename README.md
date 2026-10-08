# 📌 Notemind

**A Claude Code plugin that saves your notes and reminds you when they are due.**

Type a note in plain words, like `call Sara tomorrow at 3pm`. Notemind works out the date, saves it on your computer, and shows what is overdue or due soon each time you start a session.

## What it does

- Saves notes and follow-ups from a single sentence
- Understands dates and times written in plain words
- Shows overdue and upcoming notes when a session starts
- Lists what needs attention today
- Marks notes as done
- Keeps everything in one file on your computer (`~/.notescos/notes.db`), with no account and no network calls

## Commands

| What it does | Terminal and VS Code | Claude app (Code tab) |
|---|---|---|
| Save a note | `/notemind:note-add <text>` | `/note-add <text>` |
| See what needs attention | `/notemind:note-today` | `/note-today` |
| Browse notes | `/notemind:note-list` | `/note-list` |
| Mark a note done | `/notemind:note-done <number>` | `/note-done <number>` |
| Help | `/notemind:note-help` | `/note-help` |

```text
/notemind:note-add send the invoice tomorrow at 3pm
/notemind:note-add dentist in the next 2 hours
/notemind:note-done 3
```

## Notes without a date

Not every note has a deadline, such as "waiting on the invoice from Sara". Notemind saves these too. They show up in `note-today` under "No date" and in `note-list`, but they never appear in the startup banner and never become overdue. If you want a reminder, add a date to the note.

## Install

Requires [Claude Code](https://claude.com/claude-code) and Python 3.9 or newer.

### Terminal

```bash
claude plugin marketplace add aliyanfaisal/notemind
claude plugin install notemind@notemind
```

### VS Code

Open the Claude Code panel and run:

```text
/plugin marketplace add aliyanfaisal/notemind
/plugin install notemind@notemind
```

### Claude app

Install from the terminal (above), or run the same two `/plugin` commands in a **Code** tab session. Then use Notemind from the **Code** tab, not Chat or Cowork.

Start a new session after installing and run `/notemind:note-help`.

## Good to know

- **Use a local Code session.** Chat and Cowork run in a cloud sandbox, where notes cannot be saved to your computer.
- **Startup banner:** the terminal shows it above the prompt. In the Claude app, Claude opens its first reply with it.
- **Editing a note** is not available yet. Add a corrected note and mark the old one done.

To remove it: `/plugin uninstall notemind@notemind`. Your notes stay in `~/.notescos/` until you delete that folder.

## More

- [What the hook does](docs/hooks.md)

## License

[MIT](LICENSE)
