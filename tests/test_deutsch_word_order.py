#!/usr/bin/env python3
"""Tests for deutsch-word-order-fa — run with:
    python3 -m unittest discover -s tests -v
Zero dependencies (stdlib unittest only)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = ROOT / "skills" / "deutsch-word-order-fa" / "scripts" / "deutsch_word_order.py"
DATA = ROOT / "skills" / "deutsch-word-order-fa" / "data" / "sentences.json"
sys.path.insert(0, str(ENGINE.parent))

import deutsch_word_order as dwo  # noqa: E402


def codes(result):
    return [f["code"] for f in result["findings"]]


class TestVerbForms(unittest.TestCase):
    def test_prasens_regular(self):
        forms = dwo._presens_forms({"inf": "lernen", "sc": None})
        self.assertEqual(forms["1s"], "lerne")
        self.assertEqual(forms["2s"], "lernst")
        self.assertEqual(forms["3s"], "lernt")

    def test_e_insertion(self):
        self.assertEqual(dwo._presens_forms({"inf": "arbeiten", "sc": None})["2s"], "arbeitest")
        self.assertEqual(dwo._presens_forms({"inf": "finden", "sc": None})["2s"], "findest")
        self.assertEqual(dwo._presens_forms({"inf": "öffnen", "sc": None})["2s"], "öffnest")

    def test_no_e_insertion_for_double_consonant(self):
        self.assertEqual(dwo._presens_forms({"inf": "kommen", "sc": None})["2s"], "kommst")

    def test_stem_changes(self):
        self.assertEqual(dwo._presens_forms({"inf": "fahren", "sc": "a-ae"})["2s"], "fährst")
        self.assertEqual(dwo._presens_forms({"inf": "sprechen", "sc": "e-i"})["2s"], "sprichst")
        self.assertEqual(dwo._presens_forms({"inf": "sehen", "sc": "e-ie"})["3s"], "sieht")
        self.assertEqual(dwo._presens_forms({"inf": "nehmen", "sc": "e-i", "pres_du": "nimmst", "pres_er": "nimmt"})["2s"], "nimmst")

    def test_irregulars(self):
        self.assertEqual(dwo.FINITE["bin"], ("sein", "1s", "präsens"))
        self.assertEqual(dwo.FINITE["kann"], ("können", "1s", "präsens"))
        self.assertEqual(dwo.FINITE["konnte"], ("können", "1s", "präteritum"))
        self.assertEqual(dwo.FINITE["ging"], ("gehen", "1s", "präteritum"))

    def test_separable_attached_forms(self):
        self.assertEqual(dwo.ATTACHED_SEP["ankomme"][0], "ankommen")
        self.assertEqual(dwo.ATTACHED_SEP["ankam"][0], "ankommen")
        self.assertEqual(dwo.ATTACHED_SEP["aufstand"][0], "aufstehen")

    def test_imperative_stems(self):
        self.assertEqual(dwo._imperative_stem({"inf": "gehen", "sc": None}), "geh")
        self.assertEqual(dwo._imperative_stem({"inf": "sprechen", "sc": "e-i"}), "sprich")
        self.assertEqual(dwo._imperative_stem({"inf": "arbeiten", "sc": None}), "arbeite")
        self.assertEqual(dwo._imperative_stem({"inf": "fahren", "sc": "a-ae"}), "fahr")
        self.assertEqual(dwo._imperative_stem({"inf": "sehen", "sc": "e-ie"}), "sieh")
        self.assertEqual(dwo.FINITE["geh"], ("gehen", "2s", "imperativ"))
        self.assertEqual(dwo.FINITE["steh"], ("aufstehen", "2s", "imperativ"))

    def test_participles(self):
        self.assertEqual(dwo.PARTICIPLES["gegangen"], "gehen")
        self.assertEqual(dwo.PARTICIPLES["gelesen"], "lesen")
        self.assertEqual(dwo.PARTICIPLES["angekommen"], "ankommen")


class TestChecks(unittest.TestCase):
    def test_v2_clean(self):
        self.assertEqual(dwo.check_sentence("Ich gehe jeden Tag zur Schule.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Morgen fahre ich nach Berlin.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Am Wochenende schlafen wir lange.")["verdict"], "clean")

    def test_v2_broken(self):
        self.assertIn("DWO-01", codes(dwo.check_sentence("Ich jeden Tag gehe zur Schule.")))
        self.assertIn("DWO-01", codes(dwo.check_sentence("Morgen ich fahre nach Berlin.")))
        self.assertIn("DWO-01", codes(dwo.check_sentence("Gestern ich ging ins Kino.")))

    def test_verb_final(self):
        self.assertEqual(dwo.check_sentence("Ich bleibe zu Hause, weil ich krank bin.")["verdict"], "clean")
        self.assertIn("DWO-02", codes(dwo.check_sentence("Ich bleibe zu Hause, weil ich bin krank.")))
        self.assertIn("DWO-02", codes(dwo.check_sentence("Ich weiß, dass du fährst nach Berlin.")))
        self.assertEqual(dwo.check_sentence("Ich habe keine Zeit, weil ich arbeiten muss.")["verdict"], "clean")

    def test_tekamolo(self):
        self.assertEqual(dwo.check_sentence("Ich fahre morgen mit dem Zug nach Berlin.")["verdict"], "clean")
        self.assertIn("DWO-03", codes(dwo.check_sentence("Ich fahre nach Berlin mit dem Zug morgen.")))
        self.assertIn("DWO-03", codes(dwo.check_sentence("Ich lerne zu Hause jeden Tag Deutsch.")))

    def test_bracket(self):
        self.assertEqual(dwo.check_sentence("Ich habe das Buch gestern gelesen.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Ich stehe um 7 Uhr auf.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Ich will morgen nach Berlin fahren.")["verdict"], "clean")
        self.assertIn("DWO-04", codes(dwo.check_sentence("Ich habe das Buch gelesen gestern.")))
        self.assertIn("DWO-04", codes(dwo.check_sentence("Ich stehe auf um 7 Uhr.")))
        self.assertIn("DWO-04", codes(dwo.check_sentence("Ich ankomme um 9 Uhr.")))
        self.assertIn("DWO-04", codes(dwo.check_sentence("Ich komme an um 9 Uhr.")))
        # preposition "aus" is not the prefix of "ausgehen" here
        self.assertEqual(dwo.check_sentence("Ich gehe aus dem Haus.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Ich komme mit dem Zug nach Berlin.")["verdict"], "clean")

    def test_questions(self):
        self.assertEqual(dwo.check_sentence("Gehst du ins Kino?")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Wohin gehst du?")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Was machst du heute Abend?")["verdict"], "clean")
        self.assertIn("DWO-05", codes(dwo.check_sentence("Du gehst ins Kino?")))
        self.assertIn("DWO-06", codes(dwo.check_sentence("Du gehst wohin?")))
        self.assertIn("DWO-06", codes(dwo.check_sentence("Du kommst wann nach Hause?")))

    def test_v1_statement(self):
        self.assertIn("DWO-07", codes(dwo.check_sentence("Gehe ich zur Schule.")))
        self.assertIn("DWO-07", codes(dwo.check_sentence("Lernt er Deutsch.")))
        # imperative is fine
        self.assertEqual(dwo.check_sentence("Geh ins Kino.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Steh bitte auf.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Sprich bitte langsam.")["verdict"], "clean")

    def test_coordinator(self):
        self.assertEqual(dwo.check_sentence("Ich lerne Deutsch und ich spreche ein bisschen.")["verdict"], "clean")
        self.assertIn("DWO-08", codes(dwo.check_sentence("Ich lerne Deutsch und spreche ich ein bisschen.")))
        self.assertIn("DWO-08", codes(dwo.check_sentence("Er bleibt zu Hause, aber arbeitet er nicht.")))

    def test_nicht(self):
        self.assertEqual(dwo.check_sentence("Ich gehe nicht zur Schule.")["verdict"], "clean")
        self.assertIn("DWO-09", codes(dwo.check_sentence("Ich nicht gehe zur Schule.")))

    def test_objects(self):
        self.assertEqual(dwo.check_sentence("Ich gebe es ihm.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Ich gebe es dem Mann.")["verdict"], "clean")
        self.assertEqual(dwo.check_sentence("Ich gebe ihm das Buch.")["verdict"], "clean")
        self.assertIn("DWO-10", codes(dwo.check_sentence("Ich gebe ihm es.")))
        self.assertIn("DWO-10", codes(dwo.check_sentence("Ich gebe dem Mann es.")))
        self.assertIn("DWO-10", codes(dwo.check_sentence("Ich gebe das Buch ihm.")))

    def test_fronted_subordinate(self):
        self.assertEqual(dwo.check_sentence("Wenn es regnet, bleiben wir zu Hause.")["verdict"], "clean")
        self.assertIn("DWO-01", codes(dwo.check_sentence("Wenn es regnet, wir bleiben zu Hause.")))

    def test_unknown_verb(self):
        r = dwo.check_sentence("Ich flibbertiere jeden Tag.")
        self.assertEqual(r["verdict"], "unknown")
        self.assertEqual(r["findings"], [])


class TestDataFixtures(unittest.TestCase):
    def test_every_correct_sentence_is_clean(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 48)
        for item in data:
            with self.subTest(item=item["id"]):
                self.assertEqual(dwo.check_sentence(item["correct"])["verdict"], "clean")

    def test_every_wrong_variant_flags_its_rule(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        for item in data:
            for w in item["wrong"]:
                with self.subTest(item=item["id"], wrong=w["sentence"]):
                    self.assertIn(w["rule"], codes(dwo.check_sentence(w["sentence"])))

    def test_fix_round_trip(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        for item in data:
            for w in item["wrong"]:
                with self.subTest(item=item["id"], wrong=w["sentence"]):
                    fixed = dwo.fix_sentence(w["sentence"])
                    self.assertEqual(fixed["remaining"], [])
                    self.assertEqual(dwo.check_sentence(fixed["fixed"])["verdict"], "clean")

    def test_fix_leaves_clean_sentences_unchanged(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        for item in data:
            with self.subTest(item=item["id"]):
                self.assertEqual(dwo.fix_sentence(item["correct"])["fixed"], item["correct"])


class TestFix(unittest.TestCase):
    CASES = [
        ("Ich jeden Tag gehe zur Schule.", "Ich gehe jeden Tag zur Schule."),
        ("Morgen ich fahre nach Berlin.", "Morgen fahre ich nach Berlin."),
        ("Ich bleibe zu Hause, weil ich bin krank.", "Ich bleibe zu Hause, weil ich krank bin."),
        ("Ich fahre nach Berlin mit dem Zug morgen.", "Ich fahre morgen mit dem Zug nach Berlin."),
        ("Ich habe das Buch gelesen gestern.", "Ich habe das Buch gestern gelesen."),
        ("Ich ankomme um 9 Uhr.", "Ich komme um 9 Uhr an."),
        ("Du gehst ins Kino?", "Gehst du ins Kino?"),
        ("Du gehst wohin?", "Wohin gehst du?"),
        ("Gehe ich zur Schule.", "Ich gehe zur Schule."),
        ("Ich lerne Deutsch und spreche ich ein bisschen.", "Ich lerne Deutsch und ich spreche ein bisschen."),
        ("Ich nicht gehe zur Schule.", "Ich gehe nicht zur Schule."),
        ("Ich gebe ihm es.", "Ich gebe es ihm."),
        ("Ich gebe dem Mann es.", "Ich gebe es dem Mann."),
        ("Wenn es regnet, wir bleiben zu Hause.", "Wenn es regnet, bleiben wir zu Hause."),
    ]

    def test_fix_cases(self):
        for wrong, expected in self.CASES:
            with self.subTest(wrong=wrong):
                result = dwo.fix_sentence(wrong)
                self.assertEqual(result["fixed"], expected)
                self.assertEqual(result["remaining"], [])


class TestQuizAnki(unittest.TestCase):
    def test_quiz_deterministic(self):
        a = dwo.quiz_questions(5, seed=7)
        b = dwo.quiz_questions(5, seed=7)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5)

    def test_quiz_scrambled_differs(self):
        for q in dwo.quiz_questions(5, seed=3):
            self.assertNotEqual(q["scrambled"].rstrip(".?!"), q["correct"].rstrip(".?!"))

    def test_score_answers(self):
        qs = dwo.quiz_questions(2, seed=1)
        results = dwo.score_answers(qs, [qs[0]["correct"], "Ich jeden Tag gehe zur Schule."])
        self.assertTrue(results[0]["correct"])
        self.assertFalse(results[1]["correct"])

    def test_anki_rows(self):
        rows = dwo.anki_rows()
        self.assertEqual(len(rows), 48)
        for front, back in rows:
            self.assertIn("Ordne die Wörter", front)
            self.assertIn("<br>", back)

    def test_explain(self):
        r = dwo.explain_rule("DWO-03")
        self.assertIn("TeKaMoLo", r["title"])
        self.assertIn("زمان", r["fa"])
        self.assertIsNone(dwo.explain_rule("DWO-99"))


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        proc = subprocess.run([sys.executable, str(ENGINE), *args],
                              capture_output=True, text=True, timeout=60)
        return proc

    def test_check_clean_exit_0(self):
        self.assertEqual(self.run_cli("check", "Ich gehe zur Schule.").returncode, 0)

    def test_check_findings_exit_1(self):
        proc = self.run_cli("check", "Ich jeden Tag gehe zur Schule.")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DWO-01", proc.stdout)

    def test_check_json(self):
        proc = self.run_cli("check", "Ich jeden Tag gehe zur Schule.", "--json")
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "findings")
        self.assertEqual(payload["findings"][0]["code"], "DWO-01")

    def test_fix_cli(self):
        proc = self.run_cli("fix", "Ich jeden Tag gehe zur Schule.")
        self.assertIn("Ich gehe jeden Tag zur Schule.", proc.stdout)

    def test_explain_cli(self):
        proc = self.run_cli("explain", "DWO-02")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("DWO-02", proc.stdout)

    def test_rules_cli(self):
        proc = self.run_cli("rules")
        self.assertEqual(proc.returncode, 0)
        for code in ("DWO-01", "DWO-05", "DWO-10"):
            self.assertIn(code, proc.stdout)

    def test_usage_error(self):
        self.assertEqual(self.run_cli("check").returncode, 2)
        self.assertEqual(self.run_cli("nonsense").returncode, 2)


if __name__ == "__main__":
    unittest.main()
