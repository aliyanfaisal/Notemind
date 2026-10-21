# Privacy

Notemind stores your notes only on your computer and has no server. This page lists exactly when note text can reach Claude or claude.ai. For the hook's code-level behaviour, see [What the hook does](hooks.md).

- Your notes are stored only on your computer. Notemind has no server and makes no network calls.
- **Typing a command:** `note-today`, `note-top`, `note-check`, `note-list`, `note-done`, `note-edit`, `note-snooze`, `note-forget` and `note-settings` run on your machine, and Claude never sees them. The exceptions are a date Notemind cannot read (such as `end of next month`) and `note-edit` written in plain words (`note-edit 3 move it to friday`). Those go to Claude, which turns them into exact changes.
- **Adding a note:** Notemind first reads the date with its own rules. If that works (for example `tomorrow at 3pm`, `22 sep`, `in 2 hours`) or the note has no date at all, it saves the note and Claude never sees it. Only when it cannot read a date phrase, such as `end of next month`, is the note passed to Claude to work out the date. That note's full text then goes to Claude, like anything else you type in a session.
- **Asking your notes:** `note-ask` searches locally, but the notes that match your question are given to Claude (masked for sensitive data) so it can answer. See [the guide](guide.md#asking-your-notes).
- **Startup banner:** your overdue notes are given to Claude as context so it can help you act on them.
- **A small hook runs before every prompt you send** (about 85 ms) to catch Notemind commands. It reads each prompt but acts only on `/note-…` commands and prompts that start with `#note`, and it stores and logs nothing else. Without it, those commands would reach Claude first. See [What the hook does](hooks.md).
- **The notes board** asks before sending anything to claude.ai (see [the guide](guide.md#the-notes-board)).
- **Sensitive data is masked** whenever note text goes to Claude or claude.ai. See [Sensitive data protection](#sensitive-data-protection).

## Sensitive data protection

Before note text is given to Claude or sent to claude.ai, Notemind looks for sensitive data and replaces it with `*****`. This applies to:

- the startup banner context Claude receives,
- the output of `note-today`, `note-list`, `note-done`, `note-add` and `note-ask` when Claude runs them,
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

Details are in [What the hook does](hooks.md).
