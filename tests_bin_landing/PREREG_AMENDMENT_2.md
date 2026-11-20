# Amendment 2: answer-file layout (parsing only)

CC0. Co-authored. Dated 2026-11-02. Status: PROPOSED.
Committed alone, after the first answer file landed (773dc3a) and before any result is reported.

## What happened

- **Layout.** The first answer file, `answers/deepseek_2026-11-02.txt`, puts each `run code:` line BELOW its reply. That is the packet's own footer position. The README asked for it ABOVE.
- **What the parser did.** It read only HEADER layout. It dropped the first reply and gave every later reply the run code of the packet before it, so it scored 192 of 216 answers against the wrong keys.
- **Status of that run.** VOID. Its numbers were seen, are not reported, and enter no result.

## Change

This amendment changes the parsing of answer files only. Bins, word lists, features, predictions, tests and denominators are unchanged from amendment 1.

```text
HEADER   no "Item N:" line before the first run code   -> items belong to the run code ABOVE them
FOOTER   no "Item N:" line after the last run code      -> items belong to the run code BELOW them
REFUSED  items both before the first and after the last run code -> the file is refused and listed
```

- **How the layout is chosen.** It depends only on where the lines sit in the file, never on the answers' content. A file with exactly one packet and items on both sides is refused.
- **Refusals.** A refused file is named in the output with the reason `AMBIGUOUS_LAYOUT`, and none of its answers are scored.
- **Selftest.** It checks that a FOOTER file and a HEADER file holding the same answers score identically, and that a mixed file is refused.

## Pin

`score.py` pins the sha256 of this file beside amendment 1's, and refuses to score if either changes.
