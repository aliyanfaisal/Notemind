---
name: note-board
description: Show the user's notes as a visual board, either as a private Claude artifact or a local HTML file. Optionally limited to overdue, due today, or a date range such as "next 2 days" or "22 sep".
argument-hint: "[overdue | due | next 2 days | next week | friday | 22 sep | this month]"
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Build a visual board of the user's notes.

What the user asked to see (empty means all open notes):

$ARGUMENTS

Current date and time on the user's machine (use it to resolve dates):

!`date "+%Y-%m-%d %H:%M, %A, %Z"`

1. **Work out the range.** Turn the request into options for the tool, using the current date above:
   - empty: no range options
   - `overdue`: `--overdue`
   - `due` (due today): `--from <today> --to <today>`
   - any other period ("next 2 days", "next week", "friday", "22 sep", "this month", and so on): `--from <first day> --to <last day>` as `YYYY-MM-DD`. "Next 2 days" starts today. A single day uses the same date for both. Understand any phrasing, and never invent a range the user did not ask for.
   - `--label '<short name of the range>'`, for example `--label 'Next 2 days'`. Keep it short and use no quote marks or special characters.

2. **Ask where to build it.** Always ask, using AskUserQuestion, before anything leaves the machine. Show this text and two options:

   > A Claude artifact is hosted on claude.ai, so your notes will be **sent to claude.ai** to create it. Confirm your notes contain no sensitive data. The artifact is always **private**, visible only to you.

   - **Create a private Claude artifact**: sends the notes to claude.ai.
   - **Use a local file instead**: nothing leaves your computer.

   If AskUserQuestion is not available, ask the same question in plain text and wait for the answer. Do not choose for the user.

3. **If they chose the local file**, run:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" board <range options>
```

   The tool writes `~/.notescos/board.html` and prints Markdown with the path. Reply with it exactly as it is, and add one line telling the user to open that file in a browser.

4. **If they chose the artifact**, run the same command with `--artifact --out <file>`, where `<file>` is `notemind-board.html` inside your scratchpad directory (or the current folder if you have no scratchpad). Then publish that exact file with the Artifact tool, once, with `icon` set to `calendar` and a one-sentence `description`. The tool masks sensitive data (keys, passwords, card numbers and similar) as ***** in this file, because it is being sent to claude.ai; do not edit, rewrite or add to the file, so no note is invented or dropped. The page keeps its own title and has no private-sharing step, so leave it private. Reply with the link and the note count, and say the artifact is private. If the tool's output says some items were masked, mention that too.
   - If the Artifact tool is not available here (for example some terminal setups), say so and run step 3 instead.

5. If the range has no notes the board says so; still build it. Do not save notes anywhere else and do not create other files.
