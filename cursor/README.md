# Cursor — deutsch-word-order-fa rule

`cursor/deutsch-word-order-fa.mdc` is the Cursor version of this skill. It carries
the same contract in condensed form: never guess German word order (check
with the tool), fix by rule, and state the limits.

## Install — Cursor

Copy `cursor/deutsch-word-order-fa.mdc` into your project's `.cursor/rules/`
directory (create it if needed). Cursor applies it automatically. The
rule points at the engine script — copy the whole
`skills/deutsch-word-order-fa/` directory into your project, or install the
engine where the rule's commands can find it.

## Install — Windsurf

Copy `cursor/deutsch-word-order-fa.mdc` to `.windsurf/rules/deutsch-word-order-fa.mdc`
in your project. Windsurf loads `.mdc` rules from that directory. Copy
`skills/deutsch-word-order-fa/` alongside it so the script paths resolve.

## Install — Cline / Continue

Cline and Continue use plain Markdown rules:

- **Cline:** copy the contents of `cursor/deutsch-word-order-fa.mdc` (without the
  frontmatter block) into `.clinerules/deutsch-word-order-fa.md`, and copy
  `skills/deutsch-word-order-fa/` into your project.
- **Continue:** copy the same Markdown body into
  `.continue/rules/deutsch-word-order-fa.md`, and copy `skills/deutsch-word-order-fa/`
  into your project.

In both cases the rule's commands assume the engine lives at
`skills/deutsch-word-order-fa/scripts/deutsch_word_order.py` relative to the project
root — keep that layout.

## What it covers

- The no-guessing contract (check with the tool, not from memory).
- The ten word-order rules (DWO-01 … DWO-10): V2, verb-final,
  TeKaMoLo, sentence bracket, questions, "nicht", object order.
- Deterministic fixing with re-check, Persian rule explanations,
  scrambled-sentence quizzes, Anki export.
- The stated limits: A1–B1 lexicon, simple clauses, no relative
  clauses or Ersatzinfinitiv.
