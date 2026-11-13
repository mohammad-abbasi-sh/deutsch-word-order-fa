# deutsch-word-order-fa — German sentence structure (Satzbau) for Persian speakers

A deterministic **Agent Skill** for the third thing Persian-speaking
German learners trip over daily: word order. After
[`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
(der/die/das + 4 cases) and
[`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa)
(conjugation), this is the sequel — *where the verb goes*.

Persian word order is SOV and flexible; German is not. In a German
statement the finite verb is **always second**. In a subordinate clause
it jumps to the **end**. Adverbials run **time → manner → place**. The
second half of the verb (participle, infinitive, separable prefix)
closes the **sentence bracket** at the end. None of this exists in
Persian, so learners make the same ten mistakes over and over — and
agents answering from memory "correct" those sentences wrong just as
often. `deutsch-word-order-fa` makes word order **deterministic**: a
zero-dependency Python engine plus 48 hand-checked A1–B1 sentence
pairs (correct + the typical wrong version, each with a Persian
translation), with every explanation in Persian.

No model calls. No downloads. No API keys. Python 3.8+ standard library
only.

## The problem

```
Learner writes:   Ich jeden Tag gehe zur Schule.
Agent (guessing): looks fine ✓           ← wrong, and now the
                                           learner memorizes the error

With deutsch-word-order-fa:
$ python3 scripts/deutsch_word_order.py check "Ich jeden Tag gehe zur Schule"
✗ [DWO-01] Verb-second (V2) — فعل باید دومین جزء جمله باشد
  قبل از فعل «gehe» دو جزء آمده است: «Ich» و «jeden Tag».
  درست: Morgen fahre ich nach Berlin.

$ python3 scripts/deutsch_word_order.py fix "Ich bleibe zu Hause, weil ich bin krank"
Ich bleibe zu Hause, weil ich krank bin.   (اصلاح شد: DWO-02)
```

Before/after, from the engine:

| Before (guessed) | After (deutsch-word-order-fa) |
|---|---|
| *Ich jeden Tag gehe* | *Ich **gehe** jeden Tag* — V2, verb second |
| *weil ich bin krank* | *weil ich krank **bin*** — verb-final |
| *nach Berlin mit dem Zug morgen* | ***morgen** mit dem Zug **nach Berlin*** — TeKaMoLo |
| *Ich stehe auf um 7 Uhr* | *Ich stehe um 7 Uhr **auf*** — bracket closes the sentence |
| *Ich ankomme* | *Ich komme **an*** — separable verb splits |
| *Du gehst ins Kino?* | ***Gehst** du ins Kino?* — inversion |
| *Du gehst wohin?* | ***Wohin** gehst du?* — W-word first |
| *Ich gebe ihm es* | *Ich gebe **es ihm*** — Akk pronoun before Dat pronoun |

## What's inside

```
skills/deutsch-word-order-fa/
  SKILL.md                  the agent skill (the contract)
  scripts/deutsch_word_order.py  the engine — check, fix, explain, quiz, anki
  data/sentences.json       48 hand-checked A1–B1 sentence pairs (correct + wrong + Persian)
  references/
    word-order-rules.md     the ten rules, Persian first, with examples
    clause-guide.md         Hauptsatz / Nebensatz / Fragen
cursor/deutsch-word-order-fa.mdc the Cursor rule (same contract, condensed)
mcp-server/                 MCP server (stdio) exposing 6 tools
tests/                      46 tests, all passing (engine + MCP e2e)
```

## The ten rules

| Code | Rule |
|---|---|
| DWO-01 | Verb-second (V2): exactly one constituent before the verb |
| DWO-02 | Verb-final in subordinate clauses (weil/dass/wenn/obwohl/…) |
| DWO-03 | TeKaMoLo: time → manner → place |
| DWO-04 | Sentence bracket: participle / infinitive / separable prefix last |
| DWO-05 | Yes/no question verb-first |
| DWO-06 | W-word first, verb second |
| DWO-07 | No V1 statement (imperative excepted) |
| DWO-08 | V2 after und/aber/oder/denn/sondern |
| DWO-09 | "nicht" never directly before the verb |
| DWO-10 | Pronoun objects before noun objects; Akk pronoun before Dat pronoun |

## Install

### Claude Code

```bash
# copy the skill into your skills directory
cp -r skills/deutsch-word-order-fa ~/.claude/skills/
# or reference it from this repo in your project
```

Then ask Claude to check a German sentence — the skill tells it to
run the engine, never to guess.

### Claude.ai

Upload `dist/deutsch-word-order-fa-skill.zip` as a skill (Settings →
Skills → Upload). No setup: the engine is pure stdlib.

### Cursor / Windsurf / Cline / Continue

See `cursor/README.md` — copy `cursor/deutsch-word-order-fa.mdc`
into `.cursor/rules/` (Cursor), `.windsurf/rules/` (Windsurf),
`.clinerules/` (Cline, without frontmatter), or
`.continue/rules/` (Continue), plus `skills/deutsch-word-order-fa/`
so the script paths resolve.

### MCP clients

Any MCP client can use `mcp-server/deutsch_word_order_mcp_server.py`
(stdio, JSON-RPC 2.0, zero dependencies). Tools: `check_sentence`,
`fix_sentence`, `explain_rule`, `quiz`, `anki_export`,
`list_sentences`. Example Claude Code MCP config:

```json
{
  "mcpServers": {
    "deutsch-word-order-fa": {
      "command": "python3",
      "args": ["mcp-server/deutsch_word_order_mcp_server.py"]
    }
  }
}
```

## Usage

```bash
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py check "Ich jeden Tag gehe zur Schule"
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py fix "Ich jeden Tag gehe zur Schule"
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py explain DWO-03
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py rules
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py quiz --n 5 --level A2 --seed 7
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py quiz --answers "Ich gehe ...|..."
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py anki --out cards.tsv
python3 skills/deutsch-word-order-fa/scripts/deutsch_word_order.py list --level B1
```

Exit codes: `0` = clean / success · `1` = findings / unknown verb ·
`2` = usage error.

## Honest framing — what already exists

German word-order *teaching* is well covered by websites and games
([deutschable.games](https://deutschable.games/practice/german-word-order/),
sloeful.com, Study Rocket, ThoughtCo) and by two small practice apps
([ltn100/de-word-order](https://github.com/ltn100/de-word-order),
[mcoelho-dev/satzbau-trainer](https://github.com/mcoelho-dev/satzbau-trainer)
— both ★0, web trainers with no agent interface), plus
[satzklar.net](https://satzklar.net), a Claude-API grammar visualizer.
None of them is an agent skill, a CLI, or an MCP server; none checks a
learner's sentence deterministically; none explains the rules in
Persian. That is the gap this repo fills — the same "audit layer your
converter is missing" shape as `rtl-i18n-check` and
`persian-date-check`.

## Limits

- Curated lexicon is A1–B1 core vocabulary (73 verbs, 48 sentence
  pairs, v1.0.0) — not a dictionary replacement for verbs outside it.
- Simple main/subordinate clauses and questions only. Not judged:
  relative clauses, Ersatzinfinitiv (`habe gehen müssen`), fronted
  objects with pronoun objects.
- A deterministic reference, not a teacher: no judgment on style or
  naturalness. **No finding is not a proof of correctness.**

## Roadmap

- v1.1: B2 sentences (relative clauses, double infinitives), more
  adverbial phrases, `zu`-infinitive clauses.
- v1.2: `der/die/das` cross-check hook with `deutsch-fa` (case errors
  change word-order readings).
- v1.3: Goethe A1/A2 writing-task mode — check a full learner text,
  sentence by sentence, with a score.

## License

MIT — see [LICENSE](LICENSE).
