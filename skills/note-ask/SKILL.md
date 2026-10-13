---
name: note-ask
description: Answer a question about the user's notes, citing note numbers (for example "what did I note about the invoice?" or "who do I owe a reply?").
argument-hint: <your question>
allowed-tools: Bash(*/scripts/notescos *) Bash(*/scripts/notescos" *)
---
Answer a question using only the user's saved notes.

The question:

$ARGUMENTS

1. If the question is empty, ask what they want to know about their notes, then stop.
2. Pick the few words that would appear in the relevant notes: names, projects, things (for example "invoice", "Sara", "quote"). Drop filler such as "what", "did", "I". Include a likely synonym or two if it helps. Do not search for the whole sentence.
3. Run the search. Put the words between the markers exactly (the quoted marker keeps quotes and symbols from breaking the shell):

```
"${CLAUDE_PLUGIN_ROOT}/scripts/notescos" --redact --json search - <<'NOTESCOS_EOF'
<words here>
NOTESCOS_EOF
```
4. The tool returns a JSON list of matching notes (best first), each with its `id`, `text`, `status`, `due_at`, `person` and `project`. Answer the question from those notes only:
   - Cite every note you rely on as `#<id>`, for example "The invoice for Ali is due 20 Oct (#4)."
   - Say whether a note is done or still open when it matters.
   - If the list is empty, or the notes do not answer the question, say "No matching notes" and stop. Do not guess, and do not use anything that is not in the notes. You may try one more search with different words before giving up.
5. Keep the answer short. Do not save, edit or create anything.
