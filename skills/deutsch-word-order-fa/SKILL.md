---
name: deutsch-word-order-fa
description: German sentence structure (Satzbau) for Persian speakers — check any German sentence for word-order errors (verb-second V2, verb-final in subordinate clauses, TeKaMoLo adverbial order, sentence bracket, question inversion, "nicht" placement, object-pronoun order) with a deterministic zero-dependency tool, auto-fix the error, drill with scrambled-sentence quizzes, and export Anki cards. Use when writing or correcting German for Persian-speaking learners, when an agent must not guess word order, or when building German-learning features. Never guess the order — check it.
---

# German word order for Persian speakers — check it, never guess it

Persian word order is SOV and flexible; German is not. In a German
statement the finite verb is **always second** — no matter what stands
first. In a subordinate clause it jumps to the **end**. Adverbials run
**time → manner → place**. The second half of the verb (participle,
infinitive, separable prefix) closes the **sentence bracket** at the
end. None of this exists in Persian, so Persian-speaking learners get
it wrong in exactly the same ten ways, over and over — and agents
answering from memory "correct" those sentences wrong just as often.
A wrong order memorized once is hard to unlearn.

This skill makes word order **deterministic**: a zero-dependency engine
plus 48 hand-checked A1–B1 sentence pairs (correct + the typical wrong
version, each with a Persian translation), with every explanation in
Persian. It is the third pillar after
[`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
(der/die/das + 4 cases) and
[`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa)
(conjugation): nouns, then verbs, now the sentence itself.

## The contract

1. **Never guess word order.** When German text is on the table, run
   the bundled tool (pure stdlib, no downloads, no API):

   ```bash
   python3 scripts/deutsch_word_order.py check "Ich jeden Tag gehe zur Schule" [--json]
   ```

   It reports the rule code (DWO-01 … DWO-10), the error in Persian,
   and the correct sentence. Exit codes: `0` = clean · `1` = findings
   or unknown verb · `2` = usage error.

2. **Fix deterministically, then re-check.** The fixer reorders tokens
   by rule and re-runs the checker until the sentence is clean:

   ```bash
   python3 scripts/deutsch_word_order.py fix "Ich jeden Tag gehe zur Schule"
   # → Ich gehe jeden Tag zur Schule.   (اصلاح شد: DWO-01)
   ```

   If the tool reports remaining findings, say so — do not hand-fix
   around it and claim clean.

3. **Explain the rule in Persian.** Every rule has a Persian
   explanation with a correct and a wrong example:

   ```bash
   python3 scripts/deutsch_word_order.py explain DWO-03
   python3 scripts/deutsch_word_order.py rules   # all ten rules
   ```

   See `references/word-order-rules.md` for the full rule tables and
   `references/clause-guide.md` for Hauptsatz / Nebensatz / Fragen.

4. **Check conservatively.** The checker only flags what it can
   decide from its curated A1–B1 lexicon (73 verbs, their participles,
   separable prefixes, and the common time/manner/place adverbials).
   A sentence with no known finite verb is reported as **unknown** —
   never guessed, never flagged. Known limits (documented, not hidden):
   relative clauses, Ersatzinfinitiv (`habe gehen müssen`), and
   fronted objects with pronoun objects are not judged.

## The ten rules

| Code | Rule | Wrong → Right |
|---|---|---|
| DWO-01 | Verb-second (V2) | *Ich jeden Tag gehe* → *Ich **gehe** jeden Tag* |
| DWO-02 | Verb-final in subordinate clauses | *weil ich bin krank* → *weil ich krank **bin*** |
| DWO-03 | TeKaMoLo: time → manner → place | *nach Berlin mit dem Zug morgen* → *morgen mit dem Zug nach Berlin* |
| DWO-04 | Sentence bracket at the end | *Ich stehe auf um 7 Uhr* → *Ich stehe um 7 Uhr **auf*** |
| DWO-04 | Separable verb splits | *Ich ankomme* → *Ich komme **an*** |
| DWO-05 | Yes/no question verb-first | *Du gehst ins Kino?* → ***Gehst** du ins Kino?* |
| DWO-06 | W-word first | *Du gehst wohin?* → ***Wohin** gehst du?* |
| DWO-07 | No V1 statement | *Gehe ich zur Schule.* → ***Ich gehe** zur Schule.* |
| DWO-08 | V2 after und/aber/oder/denn/sondern | *und spreche ich* → *und **ich spreche*** |
| DWO-09 | "nicht" never before the verb | *Ich nicht gehe* → *Ich gehe **nicht*** |
| DWO-10 | Pronoun objects before noun objects; Akk before Dat | *Ich gebe ihm es* → *Ich gebe **es ihm*** |

## Drill and export

```bash
python3 scripts/deutsch_word_order.py quiz [--n 5] [--level A2] [--seed 7]
python3 scripts/deutsch_word_order.py quiz --answers "Ich gehe ...|..."   # non-interactive scoring
python3 scripts/deutsch_word_order.py anki [--level A1] [--out cards.tsv]
python3 scripts/deutsch_word_order.py list [--level B1]
```

The quiz scrambles a correct sentence; the learner reorders it. Anki
cards carry the scrambled sentence on the front and the correct
sentence + Persian meaning + rule on the back.

## When to use this skill

- A Persian-speaking learner writes a German sentence and asks "is
  this right?" — run `check`, never answer from memory.
- An agent drafts German example sentences, exercises, or dialogues
  for learners — run `check` on every sentence before showing it.
- Building a German-learning feature (quiz, chatbot, corrector) — use
  the engine as the source of truth, or the MCP server in
  `mcp-server/` for any MCP client.
- Teaching: use `explain DWO-0X` + the quiz; the rule tables in
  `references/` are written for learners, in Persian first.

## What this skill is not

- Not a full parser: it checks the ten rules above on A1–B1 sentences
  with known verbs. It does not judge style, case, or verb forms —
  that is [`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
  and [`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa).
- Not a translator: Persian glosses explain the rule; they do not
  translate arbitrary German.
