---
name: note-help
description: Explain the Notemind commands and how to use them.
---
Show the user this guide as is, formatted cleanly.

**Notemind** keeps your notes and follow-ups on your own machine and shows what needs attention when you open Claude Code.

| Command | What it does |
|---|---|
| `/notemind:note-add <text>` | Save a note. The date is read from your sentence. |
| `/notemind:note-today` | Overdue, due today and coming up in the next 7 days |
| `/notemind:note-list [--all] [--project X] [--type T] [--from DATE] [--to DATE] [--overdue]` | Browse your notes |
| `/notemind:note-board [overdue \| due \| next 2 days \| 22 sep]` | Show your notes as a visual board (private Claude artifact or local file) |
| `/notemind:note-edit <number> [--due X] [--text X] [--priority N] [--alert L] [--project X]` or in words, `note-edit 3 move it to friday` | Change a note |
| `/notemind:note-snooze <number> <when>` | Hide a note until later, e.g. `note-snooze 3 tomorrow` or `3 days` |
| `/notemind:note-done <number>` | Mark a note finished |
| `/notemind:note-help` | This guide |

**Examples**
- `/notemind:note-add call Sara on 22 sep`
- `/notemind:note-add send the invoice tomorrow at 3pm`
- `/notemind:note-add renew the domain next friday`
- `/notemind:note-edit 3 --due "friday 5pm" --priority 2`
- `/notemind:note-snooze 3 2 days`
- `/notemind:note-add dentist 04/12` (read as day/month; the reply shows how it was understood)

**Good to know**
- When a date had to be guessed (a year, or 04/12 meaning 4 Dec or 12 Apr), the reply says so. Set `NOTESCOS_DATE_ORDER=mdy` for month-first dates.
- A banner with your overdue and upcoming notes appears each time Claude Code starts.
- Notes live in `~/.notescos/notes.db`. Notemind sends nothing itself. `note-today`, `note-list` and `note-done` run without Claude, and so does `note-add` when Notemind can read the date itself. `note-board` asks before publishing a Claude artifact.
 
