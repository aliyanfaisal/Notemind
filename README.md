<p align="center">
  <img src="assets/notemind-logo.png" alt="Notemind" width="480">
</p>

**A Claude Code plugin that saves your notes and reminds you when they are due.**

Type a note in plain words, like `call Sara tomorrow at 3pm`. Notemind works out the date, saves it on your computer, and shows what is overdue or due soon each time you start a session.

## What it does

- Saves notes and follow-ups from a single sentence
- Understands dates and times written in plain words
- Shows overdue and upcoming notes when a session starts
- Lists what needs attention today
- Edits notes and snoozes them until later
- Shows your notes on a visual board, filtered by day or range
- Marks notes as done
- Keeps everything in one file on your computer (`~/.notescos/notes.db`), with no account and no network calls of its own. Notes whose date Notemind reads itself never reach Claude; see [Privacy](#privacy)

## Commands

| What it does | Terminal and VS Code | Claude app (Code tab) |
|---|---|---|
| Save a note | `/notemind:note-add <text>` | `/note-add <text>` |
| See what needs attention | `/notemind:note-today` | `/note-today` |
| Browse notes | `/notemind:note-list` | `/note-list` |
| See notes on a board | `/notemind:note-board [overdue\|due\|next 2 days\|22 sep]` | `/note-board` |
| Change a note | `/notemind:note-edit <number> …` | `/note-edit <number> …` |
| Hide a note until later | `/notemind:note-snooze <number> <when>` | `/note-snooze <number> <when>` |
| Mark a note done | `/notemind:note-done <number>` | `/note-done <number>` |
| Help | `/notemind:note-help` | `/note-help` |

```text
/notemind:note-add send the invoice tomorrow at 3pm
/notemind:note-add dentist in the next 2 hours
/notemind:note-edit 3 --due "friday 5pm" --priority 2
/notemind:note-edit 3 move it to friday
/notemind:note-snooze 3 tomorrow
/notemind:note-done 3
```

## The notes board

`/notemind:note-board` shows your notes grouped by day, with overdue first. Give it a range in plain words: `overdue`, `due` (today), `next 2 days`, `friday`, `22 sep`, `this month`. With no range it shows all open notes.

It asks where to build the board:

- **Private Claude artifact.** The page is hosted on claude.ai, so your notes are **sent to claude.ai**. Make sure they hold nothing sensitive. The artifact is always private to you.
- **Local file.** Nothing leaves your computer. The board is written to `~/.notescos/board.html`.

This is the only part of Notemind that can send notes anywhere, and only if you say yes. The board is a snapshot: make it again to see later changes.

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

> ⚠️ **Install it in Claude Code mode, not Cowork or Chat.**
> Cowork and Chat run in a cloud sandbox. A plugin installed there cannot save notes on your computer, so your notes would be lost. Always switch to the **Code** tab first.

**Option 1: commands.** In a **Code** tab session, run:

```text
/plugin marketplace add aliyanfaisal/notemind
/plugin install notemind@notemind
```

**Option 2: zip file (manual).**

1. Download `notemind-v<version>.zip` from the [Releases page](https://github.com/aliyanfaisal/notemind/releases/latest).
2. Switch to the **Code** tab.
3. Open **Plugins**, choose **Add**, and select the zip file.

Then start a new **Code** session in a local folder and run `/note-help`.

## Good to know

- **Use a local Code session.** Chat and Cowork run in a cloud sandbox, where notes cannot be saved to your computer.
- **Startup banner:** the terminal shows it above the prompt. In the Claude app, Claude opens its first reply with it.
- **Snoozed notes** leave the startup banner and `note-today` until their time, then come back on their own. `note-list` shows them with a 💤. A snooze without a time returns at the start of that day.
- **Editing:** changing the text does not move the due date. Add `--due` to change both.

To remove it: `/plugin uninstall notemind@notemind`. Your notes stay in `~/.notescos/` until you delete that folder.

## Privacy

- Your notes are stored only on your computer. Notemind has no server and makes no network calls.
- **Typing a command:** `note-today`, `note-list`, `note-done`, `note-edit` and `note-snooze` run on your machine, and Claude never sees them. The exceptions are a date Notemind cannot read (such as `end of next month`) and `note-edit` written in plain words (`note-edit 3 move it to friday`). Those go to Claude, which turns them into exact changes.
- **Adding a note:** Notemind first reads the date with its own rules. If that works (for example `tomorrow at 3pm`, `22 sep`, `in 2 hours`) or the note has no date at all, it saves the note and Claude never sees it. Only when it cannot read a date phrase, such as `end of next month`, is the note passed to Claude to work out the date. That note's full text then goes to Claude, like anything else you type in a session.
- **Startup banner:** your overdue notes are given to Claude as context so it can help you act on them.
- **A small hook runs before every prompt you send** (about 85 ms) to catch Notemind commands. It reads each prompt but acts only on `/note-…` commands, and it stores and logs nothing else. Without it, those commands would reach Claude first. See [What the hook does](docs/hooks.md).
- **The notes board** asks before sending anything to claude.ai (see above).
- **Sensitive data is masked** whenever note text goes to Claude or claude.ai. See below.

### Sensitive data protection

Before note text is given to Claude or sent to claude.ai, Notemind looks for sensitive data and replaces it with `*****`. This applies to:

- the startup banner context Claude receives,
- the output of `note-today`, `note-list`, `note-done` and `note-add` when Claude runs them,
- the **Claude artifact** version of the notes board (the board says how many items were masked).

It looks for:

| Kind | Examples |
|---|---|
| Passwords, PINs and codes | `password is hunter2`, `pin: 4821`, `otp 482913`, `cvv 123` |
| API keys and tokens | `sk-…`, `ghp_…`, `AKIA…`, `xoxb-…`, JWTs, `Bearer …` tokens |
| Private keys | `-----BEGIN RSA PRIVATE KEY-----` blocks |
| Card numbers | 13 to 19 digits that pass the card checksum |
| Bank accounts | IBANs that pass the IBAN checksum |
| Government IDs | US social security numbers (`123-45-6789`) |
| Contact details | email addresses and international phone numbers (`+92 300 1234567`) |
| Passwords in links | `postgres://user:password@host` |

Your saved notes are **never changed**: masking is applied to the copy that leaves, so your own views (`note-list` typed by you, the startup banner on your screen, the local board file) still show everything.

If you type a note that contains sensitive data and Notemind cannot read its date itself, it **does not send the note to Claude**. It tells you so and saves nothing. Rewrite the date simply (`tomorrow at 3pm`) or leave it out.

**What this cannot do.** Detection is pattern based, so it catches common formats, not everything: it does not recognise names, addresses, local phone numbers without a `+` country code, or a secret written as ordinary words. A note you type as a Claude prompt is seen by Claude as typed before Notemind can mask it, unless Notemind handles the command itself as described above. Do not put secrets in notes you do not need to keep.

Details are in [What the hook does](docs/hooks.md).

## More

- [Notemind overview page](https://aliyanfaisal.com/open-source/notemind)
- [What the hook does](docs/hooks.md)

## License

[MIT](LICENSE)
