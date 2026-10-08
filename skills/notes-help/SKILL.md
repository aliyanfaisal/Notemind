---
name: notes-help
description: Explain the Notes Chief of Staff commands and how to use them.
---
Show the user this guide as is, formatted cleanly.

**Notes Chief of Staff** keeps your notes and follow-ups on your own machine and shows what needs attention when you open Claude Code.

| Command | What it does |
|---|---|
| `/cos:notes-add <text>` | Save a note. The date is read from your sentence. |
| `/cos:notes-today` | Overdue, due today and coming up in the next 7 days |
| `/cos:notes-list [--all] [--project X] [--type T]` | Browse your notes |
| `/cos:notes-done <number>` | Mark a note finished |
| `/cos:notes-help` | This guide |

**Examples**
- `/cos:notes-add call Sara on 22 sep`
- `/cos:notes-add send the invoice tomorrow at 3pm`
- `/cos:notes-add renew the domain next friday`
- `/cos:notes-add dentist 04/12` (read as day/month; the reply shows how it was understood)

**Good to know**
- When a date had to be guessed (a year, or 04/12 meaning 4 Dec or 12 Apr), the reply says so. Set `NOTESCOS_DATE_ORDER=mdy` for month-first dates.
- A banner with your overdue and upcoming notes appears each time Claude Code starts.
- Notes live in `~/.notescos/notes.db`. Nothing is sent anywhere.

**Coming soon:** priority ranking (`/notes-top`), asking questions over your notes (`/notes-ask`), snooze and edit.
