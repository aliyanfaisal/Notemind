---
name: note-settings
description: Show or change how much the startup banner tells the user (alert level quiet, normal or loud).
argument-hint: "[alert quiet|normal|loud]"
disable-model-invocation: true
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
What the user typed (empty means show the settings): $ARGUMENTS

If it is empty, run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" settings`. If it says to change the alert level, run `"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" settings alert <quiet|normal|loud>`, mapping the user's words to one of those three (for example "less noisy" is `quiet`, "tell me more" is `loud`). If you cannot tell which level they want, ask and stop. Reply with the tool's Markdown exactly as it is.
