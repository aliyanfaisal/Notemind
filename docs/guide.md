# Notemind guide

Detailed behaviour of each feature. For install and the command list, see the [README](../README.md).

## Quick capture with `#note`

Start a prompt with `#note` and the rest is saved as a note straight away, with no model call to read it:

```text
#note call Sara tomorrow at 3pm
```

Notemind reads the date with its own rules. If it cannot read a date phrase, it saves the note **without a date** and tells you, rather than guessing. Add one later with `note-edit`. A prompt that only mentions `#note` in the middle of a sentence is left alone and goes to Claude as usual.

**Privacy catch.** Claude Code names each session with a small model from your first message, even when a hook blocks that message. If a `#note` is the first thing you type in a session, its text reaches that naming model, and Notemind cannot mask sensitive data before it does. Slash commands such as `/notemind:note-add` do not have this problem. So use `#note` for harmless quick notes, and `/note-add` for anything private.

## Money

Write who owes whom in your sentence and Notemind records the amount, currency and person:

```text
/notemind:note-add Ali owes me 15k PKR, due Friday      (money owed to you)
/notemind:note-add I owe Sara $200 next week            (money you owe)
```

It understands `15k`, `15,000`, `2.5 lakh`, `$200`, `Rs 5,000` and `500 USD`. A plain number counts as money only when the sentence clearly says someone owes or pays, so `call Sara at 3pm` or `invoice 1500 for Ali` stay ordinary notes. If the currency is not written, the amount is saved without one. Set or fix details with `note-edit 3 --amount 800 --currency PKR` (or `--type money_owed` / `money_due`).

`note-today` and `note-check` show a **Money** table with your open money notes and totals per currency. Bigger amounts rank higher in `note-top`. Marking a note done removes it from the totals.

## Asking your notes

`/notemind:note-ask what is pending for Ali?` searches your notes by the words in the question (text, person, project and tags, including finished notes) and answers from the matches only, citing them like `#4`. If nothing matches, it says so rather than guessing. Plurals work (`invoices` finds `invoice`).

The search runs on your machine. Claude then reads **the matching notes only**, with sensitive data masked, to write the answer, so those notes do go to the model. From a terminal you can run `notescos search invoice Ali` to get a plain table with no AI involved.

## Notes that need your input

If Notemind had to **guess** a date (for example `call Sara at 9am` after 9am has passed, so it picked tomorrow), or a follow-up has no date at all, the note is saved as *needs your input*. It does not alert until you confirm it, and the startup banner, `note-today` and `note-check` say "N need your input". Claude then asks what you meant. Answer with `note-edit 3 --due friday`, or accept it as it is with `note-edit 3 --confirm`. A date you write out in full (`--due`) is never questioned.

## Notes without a date

Not every note has a deadline, such as "waiting on the invoice from Sara". Notemind saves these too. They show up in `note-today` under "No date" and in `note-list`, but they never appear in the startup banner and never become overdue. If you want a reminder, add a date to the note.

## What to work on first

`/notemind:note-top` ranks your open notes with a simple, explainable score and shows why each one is where it is (for example `overdue 3d · priority 2`). The score adds up how late or soon the note is, its priority (`note-edit 3 --priority 2`), whether it is marked urgent, and how long a follow-up (`--type followup` or `waiting_on`) has gone without a change. Snoozed, finished and silent notes are left out. `/notemind:note-check` lists everything that needs attention: overdue, due today, due in the next 2 days, and follow-ups waiting 3 days or more.

## Startup banner levels

`/notemind:note-settings alert <level>` sets how much the banner shows. It never shows snoozed notes or notes marked silent, and it lists at most four notes with a "…and N more" line.

| Level | The banner shows |
|---|---|
| `quiet` | overdue notes and notes marked urgent |
| `normal` (default) | overdue, due today, due in the next 2 days, and follow-ups waiting 3+ days |
| `loud` | the same, looking 7 days ahead |

Per note, `/notemind:note-edit 3 --alert silent` keeps a note out of alerts, and `--alert urgent` makes it show up at every level and rank higher.

## The notes board

`/notemind:note-board` shows your notes grouped by day, with overdue first. Give it a range in plain words: `overdue`, `due` (today), `next 2 days`, `friday`, `22 sep`, `this month`. With no range it shows all open notes.

It asks where to build the board:

- **Private Claude artifact.** The page is hosted on claude.ai, so your notes are **sent to claude.ai**. Make sure they hold nothing sensitive. The artifact is always private to you.
- **Local file.** Nothing leaves your computer. The board is written to `~/.notescos/board.html`.

This is the only part of Notemind that can send notes anywhere, and only if you say yes. The board is a snapshot: make it again to see later changes.

## Finding commitments in past sessions (opt-in)

`/notemind:note-sync enable` turns on scanning for the current project folder. It is off everywhere until you do this. `/notemind:note-sync` then reads **only the messages you typed** in that project's earlier sessions (never Claude's replies or tool output), masks keys, passwords and card numbers first, and shows them to Claude, which proposes notes for promises and follow-ups. **Nothing is saved until you approve it.** Approved notes remember the session they came from, and the same messages are not offered twice. `note-sync disable` turns it off again.

## Deleting notes

`/notemind:note-forget 3` deletes note 3 at once. `note-forget --project shop` and `note-forget --all` first **show what would be deleted** and delete nothing; run the same command again with `--yes` to confirm. Deleted notes cannot be brought back. It runs on your machine, so Claude never sees it. To remove everything Notemind has stored, you can also delete the `~/.notescos/` folder.

## Guided tour

`/notemind:note-tour` walks you through Notemind in about two minutes with one sample note: it saves it, shows it in `note-today`, finds it with `note-ask`, marks it done, then deletes it. It is offered on first run. Claude runs the tour, so the sample note (nothing private) goes through the model.

## Good to know

- **Use a local Code session.** Chat and Cowork run in a cloud sandbox, where notes cannot be saved to your computer.
- **Startup banner:** the terminal shows it above the prompt. In the Claude app, Claude opens its first reply with it.
- **Snoozed notes** leave the startup banner and `note-today` until their time, then come back on their own. `note-list` shows them with a 💤. A snooze without a time returns at the start of that day.
- **Editing:** changing the text does not move the due date. Add `--due` to change both.

To remove it: `/plugin uninstall notemind@notemind`. Your notes stay in `~/.notescos/` until you delete that folder.
