#!/usr/bin/env python3
"""deutsch-word-order-fa — German sentence structure (Satzbau) checker
for Persian-speaking learners.

Deterministic, zero-dependency (Python 3.8+ standard library only).
No model calls, no downloads, no API keys.

What it checks (DWO codes — see `explain DWO-01` .. `explain DWO-10`):

    DWO-01  verb-second (V2) broken in a declarative main clause
    DWO-02  finite verb not last in a subordinate clause (verb-final)
    DWO-03  TeKaMoLo violated — adverbials must run time -> manner -> place
    DWO-04  sentence bracket broken — participle / infinitive / separable
            prefix not at the end of a main clause
    DWO-05  yes/no question not verb-first (missing inversion)
    DWO-06  question word (W-word) not first
    DWO-07  statement starting with the finite verb (V1, not imperative)
    DWO-08  clause after und/aber/oder/denn/sondern not V2
    DWO-09  "nicht" directly before the finite verb
    DWO-10  object pronouns after noun objects, or dative pronoun
            before accusative pronoun

Honesty rule: the checker only flags what it can decide from its
curated A1-B1 lexicon. A sentence with no known finite verb is reported
as "unknown" — never guessed, never flagged.

Usage:
    python3 deutsch_word_order.py check "Ich jeden Tag gehe zur Schule"
    python3 deutsch_word_order.py check "Ich gehe zur Schule" --json
    python3 deutsch_word_order.py fix "Ich jeden Tag gehe zur Schule"
    python3 deutsch_word_order.py explain DWO-03
    python3 deutsch_word_order.py rules
    python3 deutsch_word_order.py quiz [--n 5] [--level A2] [--seed 7]
    python3 deutsch_word_order.py quiz --answers "Ich gehe ...|..."
    python3 deutsch_word_order.py anki [--level A1] [--out cards.tsv]
    python3 deutsch_word_order.py list [--level A1]

Exit codes: 0 = clean / success, 1 = findings / unknown verb,
2 = usage error.
"""
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE.parent / "data" / "sentences.json"
VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Lexicon — hand-checked A1-B1 verbs. Fields:
#   inf: infinitive, fa: Persian gloss, level: A1|A2|B1,
#   sc: stem change in du/er (None | "e-i" | "a-ae" | "e-ie"),
#   pres_du / pres_er: explicit du/er forms when generation is irregular,
#   part: Partizip II, aux: "haben" | "sein",
#   sep: separable prefix or None, pret: Präteritum stem (ich/er form),
#   pret_cls: "weak" | "strong"
# ---------------------------------------------------------------------------
VERBS = [
    {"inf": "gehen", "fa": "رفتن", "level": "A1", "sc": None, "part": "gegangen", "aux": "sein", "sep": None, "pret": "ging", "pret_cls": "strong"},
    {"inf": "kommen", "fa": "آمدن", "level": "A1", "sc": None, "part": "gekommen", "aux": "sein", "sep": None, "pret": "kam", "pret_cls": "strong"},
    {"inf": "fahren", "fa": "راندن/سفر کردن", "level": "A1", "sc": "a-ae", "part": "gefahren", "aux": "sein", "sep": None, "pret": "fuhr", "pret_cls": "strong"},
    {"inf": "bleiben", "fa": "ماندن", "level": "A1", "sc": None, "part": "geblieben", "aux": "sein", "sep": None, "pret": "blieb", "pret_cls": "strong"},
    {"inf": "sein", "fa": "بودن", "level": "A1", "sc": None, "part": "gewesen", "aux": "sein", "sep": None, "pret": "war", "pret_cls": "strong"},
    {"inf": "haben", "fa": "داشتن", "level": "A1", "sc": None, "part": "gehabt", "aux": "haben", "sep": None, "pret": "hatte", "pret_cls": "strong"},
    {"inf": "werden", "fa": "شدن", "level": "A1", "sc": None, "part": "geworden", "aux": "sein", "sep": None, "pret": "wurde", "pret_cls": "strong"},
    {"inf": "lernen", "fa": "یاد گرفتن", "level": "A1", "sc": None, "part": "gelernt", "aux": "haben", "sep": None, "pret": "lernte", "pret_cls": "weak"},
    {"inf": "arbeiten", "fa": "کار کردن", "level": "A1", "sc": None, "part": "gearbeitet", "aux": "haben", "sep": None, "pret": "arbeitete", "pret_cls": "weak"},
    {"inf": "wohnen", "fa": "زندگی کردن", "level": "A1", "sc": None, "part": "gewohnt", "aux": "haben", "sep": None, "pret": "wohnte", "pret_cls": "weak"},
    {"inf": "spielen", "fa": "بازی کردن", "level": "A1", "sc": None, "part": "gespielt", "aux": "haben", "sep": None, "pret": "spielte", "pret_cls": "weak"},
    {"inf": "machen", "fa": "انجام دادن/ساختن", "level": "A1", "sc": None, "part": "gemacht", "aux": "haben", "sep": None, "pret": "machte", "pret_cls": "weak"},
    {"inf": "kaufen", "fa": "خریدن", "level": "A1", "sc": None, "part": "gekauft", "aux": "haben", "sep": None, "pret": "kaufte", "pret_cls": "weak"},
    {"inf": "essen", "fa": "خوردن", "level": "A1", "sc": "e-i", "pres_du": "isst", "pres_er": "isst", "part": "gegessen", "aux": "haben", "sep": None, "pret": "aß", "pret_cls": "strong"},
    {"inf": "trinken", "fa": "نوشیدن", "level": "A1", "sc": None, "part": "getrunken", "aux": "haben", "sep": None, "pret": "trank", "pret_cls": "strong"},
    {"inf": "schlafen", "fa": "خوابیدن", "level": "A1", "sc": "a-ae", "part": "geschlafen", "aux": "haben", "sep": None, "pret": "schlief", "pret_cls": "strong"},
    {"inf": "sehen", "fa": "دیدن", "level": "A1", "sc": "e-ie", "pres_du": "siehst", "pres_er": "sieht", "part": "gesehen", "aux": "haben", "sep": None, "pret": "sah", "pret_cls": "strong"},
    {"inf": "lesen", "fa": "خواندن", "level": "A1", "sc": "e-ie", "pres_du": "liest", "pres_er": "liest", "part": "gelesen", "aux": "haben", "sep": None, "pret": "las", "pret_cls": "strong"},
    {"inf": "sprechen", "fa": "صحبت کردن", "level": "A1", "sc": "e-i", "pres_du": "sprichst", "pres_er": "spricht", "part": "gesprochen", "aux": "haben", "sep": None, "pret": "sprach", "pret_cls": "strong"},
    {"inf": "hören", "fa": "شنیدن", "level": "A1", "sc": None, "part": "gehört", "aux": "haben", "sep": None, "pret": "hörte", "pret_cls": "weak"},
    {"inf": "leben", "fa": "زندگی کردن", "level": "A1", "sc": None, "part": "gelebt", "aux": "haben", "sep": None, "pret": "lebte", "pret_cls": "weak"},
    {"inf": "lieben", "fa": "دوست داشتن", "level": "A1", "sc": None, "part": "geliebt", "aux": "haben", "sep": None, "pret": "liebte", "pret_cls": "weak"},
    {"inf": "brauchen", "fa": "نیاز داشتن", "level": "A1", "sc": None, "part": "gebraucht", "aux": "haben", "sep": None, "pret": "brauchte", "pret_cls": "weak"},
    {"inf": "warten", "fa": "منتظر ماندن", "level": "A1", "sc": None, "part": "gewartet", "aux": "haben", "sep": None, "pret": "wartete", "pret_cls": "weak"},
    {"inf": "fragen", "fa": "پرسیدن", "level": "A1", "sc": None, "part": "gefragt", "aux": "haben", "sep": None, "pret": "fragte", "pret_cls": "weak"},
    {"inf": "antworten", "fa": "جواب دادن", "level": "A1", "sc": None, "part": "geantwortet", "aux": "haben", "sep": None, "pret": "antwortete", "pret_cls": "weak"},
    {"inf": "sagen", "fa": "گفتن", "level": "A1", "sc": None, "part": "gesagt", "aux": "haben", "sep": None, "pret": "sagte", "pret_cls": "weak"},
    {"inf": "geben", "fa": "دادن", "level": "A1", "sc": "e-i", "pres_du": "gibst", "pres_er": "gibt", "part": "gegeben", "aux": "haben", "sep": None, "pret": "gab", "pret_cls": "strong"},
    {"inf": "nehmen", "fa": "گرفتن/برداشتن", "level": "A1", "sc": "e-i", "pres_du": "nimmst", "pres_er": "nimmt", "part": "genommen", "aux": "haben", "sep": None, "pret": "nahm", "pret_cls": "strong"},
    {"inf": "finden", "fa": "پیدا کردن", "level": "A1", "sc": None, "part": "gefunden", "aux": "haben", "sep": None, "pret": "fand", "pret_cls": "strong"},
    {"inf": "helfen", "fa": "کمک کردن", "level": "A1", "sc": "e-i", "pres_du": "hilfst", "pres_er": "hilft", "part": "geholfen", "aux": "haben", "sep": None, "pret": "half", "pret_cls": "strong"},
    {"inf": "beginnen", "fa": "شروع کردن", "level": "A2", "sc": None, "part": "begonnen", "aux": "haben", "sep": None, "pret": "begann", "pret_cls": "strong"},
    {"inf": "vergessen", "fa": "فراموش کردن", "level": "A2", "sc": "e-i", "pres_du": "vergisst", "pres_er": "vergisst", "part": "vergessen", "aux": "haben", "sep": None, "pret": "vergaß", "pret_cls": "strong"},
    {"inf": "verstehen", "fa": "فهمیدن", "level": "A2", "sc": None, "part": "verstanden", "aux": "haben", "sep": None, "pret": "verstand", "pret_cls": "strong"},
    {"inf": "verlieren", "fa": "گم کردن/باختن", "level": "A2", "sc": None, "part": "verloren", "aux": "haben", "sep": None, "pret": "verlor", "pret_cls": "strong"},
    {"inf": "gewinnen", "fa": "بردن", "level": "A2", "sc": None, "part": "gewonnen", "aux": "haben", "sep": None, "pret": "gewann", "pret_cls": "strong"},
    {"inf": "bringen", "fa": "آوردن", "level": "A2", "sc": None, "part": "gebracht", "aux": "haben", "sep": None, "pret": "brachte", "pret_cls": "strong"},
    {"inf": "denken", "fa": "فکر کردن", "level": "A2", "sc": None, "part": "gedacht", "aux": "haben", "sep": None, "pret": "dachte", "pret_cls": "strong"},
    {"inf": "kennen", "fa": "شناختن", "level": "A2", "sc": None, "part": "gekannt", "aux": "haben", "sep": None, "pret": "kannte", "pret_cls": "weak"},
    {"inf": "wissen", "fa": "دانستن", "level": "A2", "sc": None, "part": "gewusst", "aux": "haben", "sep": None, "pret": "wusste", "pret_cls": "strong"},
    {"inf": "suchen", "fa": "جستجو کردن", "level": "A2", "sc": None, "part": "gesucht", "aux": "haben", "sep": None, "pret": "suchte", "pret_cls": "weak"},
    {"inf": "besuchen", "fa": "دیدار کردن", "level": "A2", "sc": None, "part": "besucht", "aux": "haben", "sep": None, "pret": "besuchte", "pret_cls": "weak"},
    {"inf": "telefonieren", "fa": "تلفن زدن", "level": "A2", "sc": None, "part": "telefoniert", "aux": "haben", "sep": None, "pret": "telefonierte", "pret_cls": "weak"},
    {"inf": "bezahlen", "fa": "پرداخت کردن", "level": "A2", "sc": None, "part": "bezahlt", "aux": "haben", "sep": None, "pret": "bezahlte", "pret_cls": "weak"},
    {"inf": "bestellen", "fa": "سفارش دادن", "level": "A2", "sc": None, "part": "bestellt", "aux": "haben", "sep": None, "pret": "bestellte", "pret_cls": "weak"},
    {"inf": "öffnen", "fa": "باز کردن", "level": "A2", "sc": None, "part": "geöffnet", "aux": "haben", "sep": None, "pret": "öffnete", "pret_cls": "weak"},
    {"inf": "schließen", "fa": "بستن", "level": "A2", "sc": None, "part": "geschlossen", "aux": "haben", "sep": None, "pret": "schloss", "pret_cls": "strong"},
    {"inf": "laufen", "fa": "دویدن/راه رفتن", "level": "A2", "sc": "a-ae", "part": "gelaufen", "aux": "sein", "sep": None, "pret": "lief", "pret_cls": "strong"},
    {"inf": "schwimmen", "fa": "شنا کردن", "level": "A2", "sc": None, "part": "geschwommen", "aux": "sein", "sep": None, "pret": "schwamm", "pret_cls": "strong"},
    {"inf": "fliegen", "fa": "پرواز کردن", "level": "A2", "sc": None, "part": "geflogen", "aux": "sein", "sep": None, "pret": "flog", "pret_cls": "strong"},
    {"inf": "steigen", "fa": "بالا رفتن/سوار شدن", "level": "B1", "sc": None, "part": "gestiegen", "aux": "sein", "sep": None, "pret": "stieg", "pret_cls": "strong"},
    {"inf": "treffen", "fa": "ملاقات کردن", "level": "A2", "sc": "e-i", "pres_du": "triffst", "pres_er": "trifft", "part": "getroffen", "aux": "haben", "sep": None, "pret": "traf", "pret_cls": "strong"},
    {"inf": "schreiben", "fa": "نوشتن", "level": "A2", "sc": None, "part": "geschrieben", "aux": "haben", "sep": None, "pret": "schrieb", "pret_cls": "strong"},
    {"inf": "anrufen", "fa": "تلفن زدن (به کسی)", "level": "A2", "sc": None, "part": "angerufen", "aux": "haben", "sep": "an", "pret": "rief an", "pret_cls": "strong"},
    {"inf": "ankommen", "fa": "رسیدن", "level": "A1", "sc": None, "part": "angekommen", "aux": "sein", "sep": "an", "pret": "kam an", "pret_cls": "strong"},
    {"inf": "aufstehen", "fa": "بلند شدن/بیدار شدن", "level": "A1", "sc": None, "part": "aufgestanden", "aux": "sein", "sep": "auf", "pret": "stand auf", "pret_cls": "strong"},
    {"inf": "ausgehen", "fa": "بیرون رفتن", "level": "A2", "sc": None, "part": "ausgegangen", "aux": "sein", "sep": "aus", "pret": "ging aus", "pret_cls": "strong"},
    {"inf": "einkaufen", "fa": "خرید کردن", "level": "A1", "sc": None, "part": "eingekauft", "aux": "haben", "sep": "ein", "pret": "kaufte ein", "pret_cls": "weak"},
    {"inf": "fernsehen", "fa": "تلویزیون دیدن", "level": "A2", "sc": "e-ie", "pres_du": "siehst", "pres_er": "sieht", "part": "ferngesehen", "aux": "haben", "sep": "fern", "pret": "sah fern", "pret_cls": "strong"},
    {"inf": "anfangen", "fa": "شروع کردن", "level": "A2", "sc": None, "part": "angefangen", "aux": "haben", "sep": "an", "pret": "fing an", "pret_cls": "strong"},
    {"inf": "aufhören", "fa": "تمام کردن/دست کشیدن", "level": "A2", "sc": None, "part": "aufgehört", "aux": "haben", "sep": "auf", "pret": "hörte auf", "pret_cls": "weak"},
    {"inf": "abfahren", "fa": "حرکت کردن (وسیله)", "level": "A2", "sc": "a-ae", "part": "abgefahren", "aux": "sein", "sep": "ab", "pret": "fuhr ab", "pret_cls": "strong"},
    {"inf": "mitkommen", "fa": "همراه آمدن", "level": "A2", "sc": None, "part": "mitgekommen", "aux": "sein", "sep": "mit", "pret": "kam mit", "pret_cls": "strong"},
    {"inf": "zumachen", "fa": "بستن (در/پنجره)", "level": "A2", "sc": None, "part": "zugemacht", "aux": "haben", "sep": "zu", "pret": "machte zu", "pret_cls": "weak"},
    {"inf": "vorstellen", "fa": "معرفی کردن", "level": "B1", "sc": None, "part": "vorgestellt", "aux": "haben", "sep": "vor", "pret": "stellte vor", "pret_cls": "weak"},
    {"inf": "einsteigen", "fa": "سوار شدن", "level": "B1", "sc": None, "part": "eingestiegen", "aux": "sein", "sep": "ein", "pret": "stieg ein", "pret_cls": "strong"},
    {"inf": "zurückkommen", "fa": "برگشتن", "level": "B1", "sc": None, "part": "zurückgekommen", "aux": "sein", "sep": "zurück", "pret": "kam zurück", "pret_cls": "strong"},
    {"inf": "aussehen", "fa": "به نظر رسیدن", "level": "B1", "sc": "e-ie", "pres_du": "siehst", "pres_er": "sieht", "part": "ausgesehen", "aux": "haben", "sep": "aus", "pret": "sah aus", "pret_cls": "strong"},
    {"inf": "losgehen", "fa": "راه افتادن", "level": "B1", "sc": None, "part": "losgegangen", "aux": "sein", "sep": "los", "pret": "ging los", "pret_cls": "strong"},
    {"inf": "regnen", "fa": "باران باریدن", "level": "A1", "sc": None, "part": "geregnet", "aux": "haben", "sep": None, "pret": "regnete", "pret_cls": "weak"},
    {"inf": "scheinen", "fa": "به نظر رسیدن/درخشیدن", "level": "B1", "sc": None, "part": "geschienen", "aux": "haben", "sep": None, "pret": "schien", "pret_cls": "strong"},
    {"inf": "zeigen", "fa": "نشان دادن", "level": "A2", "sc": None, "part": "gezeigt", "aux": "haben", "sep": None, "pret": "zeigte", "pret_cls": "weak"},
    {"inf": "gehören", "fa": "تعلق داشتن", "level": "B1", "sc": None, "part": "gehört", "aux": "haben", "sep": None, "pret": "gehörte", "pret_cls": "weak"},
    {"inf": "passieren", "fa": "اتفاق افتادن", "level": "B1", "sc": None, "part": "passiert", "aux": "sein", "sep": None, "pret": "passierte", "pret_cls": "weak"},
]

# Irregular finite forms that generation cannot produce (sein/haben/werden/
# wissen + modals). person keys: 1s 2s 3s 1p 2p 3p.
IRREGULAR_PRESENS = {
    "sein":   {"1s": "bin", "2s": "bist", "3s": "ist", "1p": "sind", "2p": "seid", "3p": "sind"},
    "haben":  {"1s": "habe", "2s": "hast", "3s": "hat", "1p": "haben", "2p": "habt", "3p": "haben"},
    "werden": {"1s": "werde", "2s": "wirst", "3s": "wird", "1p": "werden", "2p": "werdet", "3p": "werden"},
    "wissen": {"1s": "weiß", "2s": "weißt", "3s": "weiß", "1p": "wissen", "2p": "wisst", "3p": "wissen"},
    "können": {"1s": "kann", "2s": "kannst", "3s": "kann", "1p": "können", "2p": "könnt", "3p": "können"},
    "müssen": {"1s": "muss", "2s": "musst", "3s": "muss", "1p": "müssen", "2p": "müsst", "3p": "müssen"},
    "wollen": {"1s": "will", "2s": "willst", "3s": "will", "1p": "wollen", "2p": "wollt", "3p": "wollen"},
    "sollen": {"1s": "soll", "2s": "sollst", "3s": "soll", "1p": "sollen", "2p": "sollt", "3p": "sollen"},
    "dürfen": {"1s": "darf", "2s": "darfst", "3s": "darf", "1p": "dürfen", "2p": "dürft", "3p": "dürfen"},
    "mögen":  {"1s": "mag", "2s": "magst", "3s": "mag", "1p": "mögen", "2p": "mögt", "3p": "mögen"},
}
MODALS = {"können", "müssen", "wollen", "sollen", "dürfen", "mögen"}
AUXILIARIES = {"sein", "haben", "werden"}

# Adverbial lexicon: single words by type, and multi-word phrases.
TIME_WORDS = {
    "heute", "morgen", "gestern", "jetzt", "bald", "später", "oft", "immer",
    "manchmal", "nie", "selten", "schon", "noch", "täglich", "montags",
    "dienstags", "mittwochs", "donnerstags", "freitags", "samstags",
    "sonntags", "morgens", "mittags", "abends", "nachts", "früh", "spät",
    "gestern", "vorgestern", "übermorgen", "sofort", "gleich", "dann",
    "zuerst", "zuletzt", "endlich", "plötzlich", "wöchentlich", "jährlich",
}
MANNER_WORDS = {
    "gern", "gerne", "schnell", "langsam", "gut", "schlecht", "leise",
    "laut", "zusammen", "allein", "vorsichtig", "pünktlich", "hoffentlich",
    "leider", "wirklich", "sehr", "viel", "wenig", "fleißig",
    "besser", "lieber", "gern", "einfach", "schwer", "leicht",
}
PLACE_WORDS = {
    "hier", "dort", "draußen", "drinnen", "oben", "unten", "links",
    "rechts", "überall", "nirgendwo", "weg", "weit", "nah",
}
# phrase tuple (lowercase words) -> type: "time" | "manner" | "place"
PHRASES = {
    ("jeden", "tag"): "time", ("jede", "woche"): "time", ("jedes", "jahr"): "time",
    ("jeden", "morgen"): "time", ("jeden", "abend"): "time",
    ("am", "montag"): "time", ("am", "dienstag"): "time", ("am", "mittwoch"): "time",
    ("am", "donnerstag"): "time", ("am", "freitag"): "time", ("am", "samstag"): "time",
    ("am", "sonntag"): "time", ("am", "morgen"): "time", ("am", "abend"): "time",
    ("am", "wochenende"): "time", ("im", "sommer"): "time", ("im", "winter"): "time",
    ("im", "frühling"): "time", ("im", "herbst"): "time",
    ("nächste", "woche"): "time", ("letzte", "woche"): "time",
    ("nächsten", "monat"): "time", ("letzten", "monat"): "time",
    ("in", "zwei", "tagen"): "time", ("in", "einer", "woche"): "time",
    ("um", "7", "uhr"): "time", ("um", "8", "uhr"): "time", ("um", "9", "uhr"): "time",
    ("um", "acht", "uhr"): "time", ("um", "neun", "uhr"): "time",
    ("um", "zehn", "uhr"): "time", ("heute", "abend"): "time",
    ("heute", "morgen"): "time", ("morgen", "früh"): "time",
    ("morgen", "abend"): "time", ("zwei", "stunden"): "time",
    ("mit", "dem", "zug"): "manner", ("mit", "dem", "auto"): "manner",
    ("mit", "dem", "bus"): "manner", ("mit", "dem", "fahrrad"): "manner",
    ("mit", "dem", "flugzeug"): "manner", ("mit", "freunden"): "manner",
    ("mit", "meiner", "freundin"): "manner", ("mit", "meinem", "freund"): "manner",
    ("mit", "meiner", "familie"): "manner", ("mit", "dem", "handy"): "manner",
    ("zu", "fuß"): "manner",
    ("nach", "berlin"): "place", ("in", "berlin"): "place",
    ("nach", "deutschland"): "place", ("in", "deutschland"): "place",
    ("nach", "italien"): "place", ("in", "italien"): "place",
    ("im", "park"): "place", ("in", "der", "schule"): "place",
    ("in", "die", "schule"): "place", ("ins", "kino"): "place",
    ("im", "kino"): "place", ("zum", "arzt"): "place",
    ("in", "den", "supermarkt"): "place", ("im", "supermarkt"): "place",
    ("auf", "dem", "markt"): "place", ("am", "bahnhof"): "place",
    ("nach", "hause"): "place", ("zu", "hause"): "place",
    ("im", "büro"): "place", ("in", "der", "stadt"): "place",
    ("im", "restaurant"): "place", ("in", "der", "bibliothek"): "place",
    ("auf", "der", "arbeit"): "place", ("zur", "schule"): "place",
    ("zur", "arbeit"): "place", ("in", "den", "park"): "place",
    ("in", "der", "wohnung"): "place", ("im", "garten"): "place",
    ("in", "der", "küche"): "place", ("im", "zimmer"): "place",
    ("nach", "hamburg"): "place", ("in", "hamburg"): "place",
}

W_WORDS = {"wer", "was", "wann", "wo", "wohin", "woher", "warum", "wie",
           "wieso", "weshalb", "welcher", "welche", "welches", "wieviel",
           "wieviele"}
SUBORDINATORS = {"weil", "dass", "wenn", "obwohl", "als", "bevor",
                 "nachdem", "ob", "während", "seit", "bis", "damit", "falls",
                 "sobald", "obgleich"}
COORDINATORS = {"und", "aber", "oder", "denn", "sondern"}
SUBJECT_PRONOUNS = {"ich", "du", "er", "sie", "es", "wir", "ihr", "sie"}
AKK_PRONOUNS = {"mich", "dich", "ihn", "es"}          # unambiguous only
DAT_PRONOUNS = {"mir", "dir", "ihm", "ihr", "ihnen"}   # unambiguous only
ARTICLES = {"der", "die", "das", "den", "dem", "einen", "eine", "einem",
            "einer", "eines", "mein", "meine", "meinen", "meinem", "meiner",
            "dein", "deine", "deinen", "deinem", "sein", "seine", "seinen",
            "seinem", "seiner", "ihr", "ihre", "ihren", "ihrem", "unser",
            "unsere", "unseren", "euer", "eure", "kein", "keine", "keinen"}
NOUNS = {
    "mann", "frau", "kind", "buch", "auto", "zug", "schule", "kino", "arzt",
    "supermarkt", "freund", "freundin", "bruder", "schwester", "mutter",
    "vater", "zeit", "geld", "kaffee", "tee", "wasser", "brot", "tisch",
    "stuhl", "handy", "computer", "wohnung", "stadt", "land", "park",
    "restaurant", "büro", "bahnhof", "markt", "bibliothek", "arbeit",
    "deutsch", "englisch", "film", "musik", "foto", "geschenk", "schlüssel",
    "jacke", "tasche", "bus", "fahrrad", "flugzeug", "hund", "katze",
    "lehrer", "lehrerin", "student", "studentin", "kollege", "kollegin",
    "haus", "zimmer", "garten", "küche", "italien", "berlin", "hamburg",
    "urlaub", "morgen", "abend", "tag", "woche", "monat", "jahr", "uhr",
    "stunde", "minute", "essen", "frühstück", "mittagessen", "abendessen",
    "brot", "käse", "milch", "saft", "bier", "wein", "apfel", "banane",
    "heft", "stift", "brief", "email", "nachricht", "frage", "antwort",
    "prüfung", "kurs", "sprache", "wort", "satz", "text", "seite",
}

# ---------------------------------------------------------------------------
# Form generation — Präsens / Präteritum from the verb table.
# ---------------------------------------------------------------------------
def _stem(inf):
    if inf.endswith("eln") or inf.endswith("ern"):
        return inf[:-1]  # lächeln -> lächel- (not in the list, kept for safety)
    if inf.endswith("en"):
        return inf[:-2]
    if inf.endswith("n"):
        return inf[:-1]
    return inf


def _needs_e(stem):
    """-e- insertion before du/er/ihr endings (arbeiten -> arbeitest)."""
    if stem.endswith(("t", "d")):
        return True
    if stem.endswith(("m", "n")) and len(stem) >= 2 and stem[-2] not in "aeiouälrmn":
        return True
    return False


def _presens_forms(v):
    inf = v["inf"]
    if inf in IRREGULAR_PRESENS:
        forms = dict(IRREGULAR_PRESENS[inf])
        return forms
    if v.get("sep"):
        base = inf[len(v["sep"]):]
        base_v = dict(v, inf=base, sep=None)
        return _presens_forms(base_v)
    stem = _stem(inf)
    sc = v.get("sc")
    du_stem, er_stem = stem, stem
    if sc == "e-i":
        du_stem = er_stem = stem[:-1] + "i" if stem.endswith("e") else stem
        # sprechen: sprech- -> sprich- ; nehmen: nehm- -> nimm-
        if stem.endswith("ech"):
            du_stem = er_stem = stem[:-3] + "ich"
        elif stem.endswith("ehm"):
            du_stem = er_stem = stem[:-3] + "imm"
        elif stem.endswith("e"):
            du_stem = er_stem = stem[:-1] + "i"
    elif sc == "a-ae":
        # fahren: fahr- -> fähr- ; schlafen: schlaf- -> schläf-
        du_stem = er_stem = stem.replace("a", "ä", 1)
    elif sc == "e-ie":
        # sehen: seh- -> sieh- ; lesen: les- -> lies-
        if stem.endswith("eh"):
            du_stem = er_stem = stem[:-2] + "ieh"
        elif stem.endswith("e"):
            du_stem = er_stem = stem[:-1] + "ie"
    e = "e" if _needs_e(stem) else ""
    du_e = "e" if _needs_e(du_stem) else ""
    er_e = "e" if _needs_e(er_stem) else ""
    s_drop = stem.endswith(("s", "ß", "x", "z"))
    du_end = "t" if s_drop else "st"
    forms = {
        "1s": stem + "e",
        "2s": v.get("pres_du") or (du_stem + du_e + du_end),
        "3s": v.get("pres_er") or (er_stem + er_e + "t"),
        "1p": stem + "en",
        "2p": stem + e + "t",
        "3p": stem + "en",
    }
    return forms


IMPERATIVE_OVERRIDES = {
    "sein": "sei", "haben": "hab", "werden": "werd", "wissen": "wisse",
    "essen": "iss", "geben": "gib", "sehen": "sieh", "lesen": "lies",
    "sprechen": "sprich", "nehmen": "nimm", "fahren": "fahr",
    "schlafen": "schlaf", "laufen": "lauf", "helfen": "hilf",
    "treffen": "triff", "vergessen": "vergiss",
}


def _imperative_stem(v):
    """du-Imperativ stem: "geh", "sprich", "arbeite", "steh auf" -> "steh".

    The a-umlaut of the du-form does NOT carry over ("fahr", not
    "fähr"); the e->i / e->ie changes do ("sprich", "sieh")."""
    inf = v["inf"]
    if inf in IMPERATIVE_OVERRIDES:
        return IMPERATIVE_OVERRIDES[inf]
    if v.get("sep"):
        base = inf[len(v["sep"]):]
        return _imperative_stem(dict(v, inf=base, sep=None))
    stem = _stem(inf)
    sc = v.get("sc")
    if sc == "e-i":
        if stem.endswith("ech"):
            stem = stem[:-3] + "ich"
        elif stem.endswith("ehm"):
            stem = stem[:-3] + "imm"
        elif stem.endswith("e"):
            stem = stem[:-1] + "i"
    elif sc == "e-ie":
        if stem.endswith("eh"):
            stem = stem[:-2] + "ieh"
        elif stem.endswith("e"):
            stem = stem[:-1] + "ie"
    if _needs_e(stem):
        return stem + "e"
    return stem


def _preterite_forms(v):
    inf = v["inf"]
    if inf in IRREGULAR_PRESENS:
        # sein war, haben hatte, werden wurde, wissen wusste, modals konnte...
        pret_map = {
            "sein": "war", "haben": "hatte", "werden": "wurde",
            "wissen": "wusste", "können": "konnte", "müssen": "musste",
            "wollen": "wollte", "sollen": "sollte", "dürfen": "durfte",
            "mögen": "mochte",
        }
        base = pret_map[inf]
        if inf == "sein":
            return {"1s": "war", "2s": "warst", "3s": "war",
                    "1p": "waren", "2p": "wart", "3p": "waren"}
        if inf == "haben":
            return {"1s": "hatte", "2s": "hattest", "3s": "hatte",
                    "1p": "hatten", "2p": "hattet", "3p": "hatten"}
        return {"1s": base, "2s": base + "st", "3s": base,
                "1p": base + "n", "2p": base + "t", "3p": base + "n"}
    if v.get("sep"):
        base = inf[len(v["sep"]):]
        # pret holds "fing an" / "kaufte ein" — the base form needs the
        # bare stem ("fing" / "kaufte") only.
        pret = (v.get("pret") or "").split()[0] if v.get("pret") else None
        return _preterite_forms(dict(v, inf=base, sep=None, pret=pret))
    pret = v.get("pret")
    if not pret:
        return {}
    if v.get("pret_cls") == "weak":
        # pret already holds the ich/er form (lernte, kaufte)
        stem = pret[:-1] if pret.endswith("e") else pret
        return {"1s": pret, "2s": pret + "st", "3s": pret,
                "1p": pret + "n", "2p": pret + "t", "3p": pret + "n"}
    # strong: pret holds ich/er (ging, fuhr, sah)
    return {"1s": pret, "2s": pret + "st", "3s": pret,
            "1p": pret + "en", "2p": pret + "t", "3p": pret + "en"}


def _build_maps():
    finite = {}      # form (lower) -> (infinitive, person, tense)
    participles = {} # participle (lower) -> infinitive
    infinitives = set()
    attached = {}    # attached separable finite form -> (infinitive, person)
    for v in VERBS:
        inf = v["inf"]
        infinitives.add(inf)
        participles[v["part"].lower()] = inf
        for person, form in _presens_forms(v).items():
            finite.setdefault(form.lower(), (inf, person, "präsens"))
        for person, form in _preterite_forms(v).items():
            finite.setdefault(form.lower(), (inf, person, "präteritum"))
        if v.get("sep"):
            # _presens_forms / _preterite_forms on a separable verb
            # already return the BASE forms (komme / kam); attach the
            # prefix to get the (incorrect-in-a-main-clause) full form.
            prefix = v["sep"]
            for person, form in _presens_forms(v).items():
                attached[(prefix + form).lower()] = (inf, person, "präsens")
            for person, form in _preterite_forms(v).items():
                attached[(prefix + form).lower()] = (inf, person, "präteritum")
    # du-Imperativ stems ("geh", "sprich", "arbeite") — needed so the
    # checker recognises an imperative instead of reporting "unknown".
    for v in VERBS:
        imp = _imperative_stem(v)
        finite.setdefault(imp.lower(), (v["inf"], "2s", "imperativ"))
    for inf, imp in IMPERATIVE_OVERRIDES.items():
        finite.setdefault(imp.lower(), (inf, "2s", "imperativ"))
    # modals / irregulars not in VERBS
    for inf, forms in IRREGULAR_PRESENS.items():
        infinitives.add(inf)
        for person, form in forms.items():
            finite.setdefault(form.lower(), (inf, person, "präsens"))
        for person, form in _preterite_forms({"inf": inf}).items():
            finite.setdefault(form.lower(), (inf, person, "präteritum"))
    return finite, participles, infinitives, attached


FINITE, PARTICIPLES, INFINITIVES, ATTACHED_SEP = _build_maps()
# separable infinitive -> (prefix, base infinitive)
SEP_INF = {v["inf"]: (v["sep"], v["inf"][len(v["sep"]):]) for v in VERBS if v.get("sep")}
# prefix -> set of separable infinitives (for bracket checks)
SEP_PREFIXES = {v["sep"] for v in VERBS if v.get("sep")}
PART_SET = set(PARTICIPLES)
INF_SET = set(INFINITIVES)

RULES = {
    "DWO-01": {
        "title": "Verb-second (V2) — فعل باید دومین جزء جمله باشد",
        "fa": "در جمله‌ی خبری آلمانی، فعل صرف‌شده همیشه در جایگاه دوم است؛ یعنی فقط «یک» جزء قبل از فعل می‌آید. اگر دو جزء قبل از فعل باشند (مثلاً فاعل + قید زمان)، فعل باید بعد از جزء اول بیاید و فاعل بعد از فعل: «Gestern ging ich …» نه «Gestern ich ging …».",
        "de": "Im deutschen Aussagesatz steht das finite Verb an zweiter Stelle (Verbzweitstellung). Nur EIN Satzglied darf vor dem Verb stehen.",
        "example_ok": "Morgen fahre ich nach Berlin.",
        "example_bad": "Morgen ich fahre nach Berlin.",
    },
    "DWO-02": {
        "title": "Verb-final — در جمله‌ی فرعی فعل به انتها می‌رود",
        "fa": "بعد از حروف ربط فرعی (weil, dass, wenn, obwohl, als, bevor, nachdem, ob …) فعل صرف‌شده به انتهای جمله‌ی فرعی می‌رود: «…, weil ich krank bin» نه «…, weil ich bin krank».",
        "de": "Im Nebensatz steht das finite Verb am Ende (Verbletztstellung).",
        "example_ok": "Ich bleibe zu Hause, weil ich krank bin.",
        "example_bad": "Ich bleibe zu Hause, weil ich bin krank.",
    },
    "DWO-03": {
        "title": "TeKaMoLo — ترتیب قیدها: زمان، حالت، مکان",
        "fa": "وقتی چند قید در جمله هست، ترتیب خنثی این است: زمان (Temporal) ← حالت/چگونگی (Kausal/Modal) ← مکان (Lokal). «Ich fahre morgen mit dem Zug nach Berlin» نه «Ich fahre nach Berlin mit dem Zug morgen».",
        "de": "Mehrere Adverbiale stehen in der neutralen Reihenfolge Temporal – Kausal/Modal – Lokal (TeKaMoLo).",
        "example_ok": "Ich fahre morgen mit dem Zug nach Berlin.",
        "example_bad": "Ich fahre nach Berlin mit dem Zug morgen.",
    },
    "DWO-04": {
        "title": "Sentence bracket (Satzklammer) — بخش دوم فعل به انتها می‌رود",
        "fa": "در جمله‌ی اصلی، بخش دوم فعل (Partizip در Perfekt، مصدر بعد از Modal، یا پیشوند فعل جداشدنی) به انتهای جمله می‌رود و هیچ چیز بعد از آن نمی‌آید: «Ich habe das Buch gestern gelesen» و «Ich stehe um 7 Uhr auf». همچنین فعل جداشدنی در جمله‌ی اصلی جدا نوشته می‌شود: «Ich komme an» نه «Ich ankomme».",
        "de": "In der Satzklammer steht der zweite Verbteil (Partizip II, Infinitiv, trennbares Präfix) am Satzende.",
        "example_ok": "Ich stehe um 7 Uhr auf.",
        "example_bad": "Ich stehe auf um 7 Uhr.",
    },
    "DWO-05": {
        "title": "Yes/no question — سؤال بله/خیر با فعل شروع می‌شود",
        "fa": "سؤال بدون کلمه‌ی پرسشی با فعل صرف‌شده شروع می‌شود (وارونگی): «Gehst du ins Kino؟» نه «Du gehst ins Kino؟».",
        "de": "Ja/Nein-Fragen beginnen mit dem finiten Verb (Inversion).",
        "example_ok": "Gehst du ins Kino?",
        "example_bad": "Du gehst ins Kino?",
    },
    "DWO-06": {
        "title": "W-question — کلمه‌ی پرسشی اول جمله می‌آید",
        "fa": "در سؤال با کلمه‌ی پرسشی (wer, was, wann, wo, wohin, warum, wie …) کلمه‌ی پرسشی اول می‌آید و فعل بلافاصله بعد از آن: «Wohin gehst du؟» نه «Du gehst wohin؟».",
        "de": "Im W-Fragesatz steht das Fragewort an erster Stelle, das finite Verb direkt danach.",
        "example_ok": "Wohin gehst du?",
        "example_bad": "Du gehst wohin?",
    },
    "DWO-07": {
        "title": "V1 statement — جمله‌ی خبری با فعل شروع نمی‌شود",
        "fa": "جمله‌ی خبری با فعل شروع نمی‌شود (مگر امر: «Geh ins Kino.»). اگر جمله با فعل شروع شود و بعد فاعل بیاید، یا سؤال است (با ؟) یا اشتباه است: «Gehe ich zur Schule.» غلط است؛ درستش «Ich gehe zur Schule.» است.",
        "de": "Ein Aussagesatz beginnt nicht mit dem finiten Verb (Ausnahme: Imperativ).",
        "example_ok": "Ich gehe zur Schule.",
        "example_bad": "Gehe ich zur Schule.",
    },
    "DWO-08": {
        "title": "Coordinator clause — بعد از und/aber هم V2 برقرار است",
        "fa": "بعد از حروف ربط هم‌پایه (und, aber, oder, denn, sondern) جمله‌ی بعدی همچنان V2 است: «Ich lerne Deutsch und ich spreche ein bisschen» نه «… und spreche ich ein bisschen».",
        "de": "Nach nebenordnenden Konjunktionen (und, aber, oder, denn, sondern) gilt weiterhin V2.",
        "example_ok": "Ich lerne Deutsch und ich spreche ein bisschen.",
        "example_bad": "Ich lerne Deutsch und spreche ich ein bisschen.",
    },
    "DWO-09": {
        "title": "«nicht» — «nicht» قبل از فعل نمی‌آید",
        "fa": "«nicht» هرگز بلافاصله قبل از فعل صرف‌شده نمی‌آید؛ بعد از فعل (و معمولاً بعد از مفعول) می‌آید: «Ich gehe nicht zur Schule» نه «Ich nicht gehe zur Schule».",
        "de": "«nicht» steht nie direkt vor dem finiten Verb, sondern danach.",
        "example_ok": "Ich gehe nicht zur Schule.",
        "example_bad": "Ich nicht gehe zur Schule.",
    },
    "DWO-10": {
        "title": "Object order — ضمیر مفعولی قبل از اسم می‌آید",
        "fa": "مفعول ضمیری همیشه قبل از مفعول اسمی می‌آید («Ich gebe es dem Mann»)، و اگر دو ضمیر باشند، مفعول Accusativ قبل از Dativ می‌آید («Ich gebe es ihm» نه «Ich gebe ihm es»).",
        "de": "Pronominale Objekte stehen vor nominalen Objekten; bei zwei Pronomen steht Akkusativ vor Dativ.",
        "example_ok": "Ich gebe es ihm.",
        "example_bad": "Ich gebe ihm es.",
    },
}

RANK = {"time": 0, "manner": 1, "place": 2}

# ---------------------------------------------------------------------------
# Tokenizing, chunking, clause analysis
# ---------------------------------------------------------------------------
def tokenize(sentence):
    """Return (tokens, comma_after, final_punct)."""
    s = sentence.strip()
    final = ""
    if s and s[-1] in ".?!":
        final = s[-1]
        s = s[:-1]
    tokens = []
    comma_after = set()
    for raw in s.split():
        if raw.endswith(","):
            tokens.append(raw[:-1])
            comma_after.add(len(tokens) - 1)
        else:
            tokens.append(raw)
    return tokens, comma_after, final


def split_segments(tokens, comma_after):
    """Split tokens into clause segments at commas."""
    segments = []
    start = 0
    for i in range(len(tokens)):
        if i in comma_after:
            segments.append(tokens[start:i + 1])
            start = i + 1
    if start < len(tokens):
        segments.append(tokens[start:])
    return segments


_LOWERCASE_MID = (SUBJECT_PRONOUNS | AKK_PRONOUNS | DAT_PRONOUNS
                 | {"uns", "euch", "sie", "ihnen", "nicht"}
                 | set(FINITE) | set(PARTICIPLES) | set(INF_SET)
                 | set(ATTACHED_SEP) | TIME_WORDS | MANNER_WORDS
                 | PLACE_WORDS | W_WORDS | SUBORDINATORS | COORDINATORS
                 | ARTICLES)


def join_sentence(segments, final):
    flat = [t for seg in segments for t in seg]
    chunks = chunk_tokens(flat)
    # Only single-token chunks may lose their capital mid-sentence:
    # "Morgen" inside "jeden Morgen" and "Essen" inside "das Essen"
    # are nouns and keep it; a moved "Du" / "Gehe" does not.
    lower_idx = {a for (a, b, k) in chunks
                 if b - a == 1 and flat[a].lower() in _LOWERCASE_MID}
    parts, pos = [], 0
    for seg in segments:
        if not seg:
            continue
        fixed = []
        for j, tok in enumerate(seg):
            if pos + j > 0 and (pos + j) in lower_idx:
                fixed.append(tok.lower())
            else:
                fixed.append(tok)
        parts.append(" ".join(fixed))
        pos += len(seg)
    s = ", ".join(parts)
    if s:
        s = s[0].upper() + s[1:]
    return s + final if final else s


def chunk_tokens(tokens):
    """Greedy constituent chunking. Returns [(start, end, kind)]."""
    chunks = []
    i, n = 0, len(tokens)
    while i < n:
        low = tokens[i].lower()
        if low == "um" and i + 2 < n and tokens[i + 1].isdigit() \
                and tokens[i + 2].lower() == "uhr":
            chunks.append((i, i + 3, "time"))
            i += 3
            continue
        matched = None
        for length in (4, 3, 2):
            if i + length <= n:
                key = tuple(t.lower() for t in tokens[i:i + length])
                if key in PHRASES:
                    matched = (length, PHRASES[key])
                    break
        if matched:
            length, kind = matched
            chunks.append((i, i + length, kind))
            i += length
            continue
        if low in FINITE or low in ATTACHED_SEP:
            chunks.append((i, i + 1, "verb"))
        elif low in PARTICIPLES:
            chunks.append((i, i + 1, "part"))
        elif low in INF_SET:
            chunks.append((i, i + 1, "inf"))
        elif low in W_WORDS:
            chunks.append((i, i + 1, "w"))
        elif low in SUBORDINATORS:
            chunks.append((i, i + 1, "sub"))
        elif low in COORDINATORS:
            chunks.append((i, i + 1, "coord"))
        elif low == "nicht":
            chunks.append((i, i + 1, "neg"))
        elif low in TIME_WORDS:
            chunks.append((i, i + 1, "time"))
        elif low in MANNER_WORDS:
            chunks.append((i, i + 1, "manner"))
        elif low in PLACE_WORDS:
            chunks.append((i, i + 1, "place"))
        elif low in SUBJECT_PRONOUNS:
            chunks.append((i, i + 1, "subj"))
        elif low in ARTICLES and i + 1 < n and tokens[i + 1].lower() in NOUNS:
            chunks.append((i, i + 2, "obj"))
            i += 2
            continue
        elif low in NOUNS:
            chunks.append((i, i + 1, "obj"))
        elif low in AKK_PRONOUNS or low in DAT_PRONOUNS or low in {"uns", "euch", "sie", "ihnen"}:
            chunks.append((i, i + 1, "objpron"))
        else:
            chunks.append((i, i + 1, "other"))
        i += 1
    return chunks


def find_finite(tokens, last=False):
    """Finite verb token. Returns (index, inf, person, tense, attached).

    First match by default; last=True for subordinate clauses, where
    the finite verb stands at the end and an infinitive (e.g. "arbeiten"
    in "weil ich arbeiten muss") would otherwise shadow the modal."""
    found = None
    for i, tok in enumerate(tokens):
        low = tok.lower()
        if low in FINITE:
            inf, person, tense = FINITE[low]
            found = (i, inf, person, tense, False)
            if not last:
                return found
        elif low in ATTACHED_SEP:
            inf, person, tense = ATTACHED_SEP[low]
            found = (i, inf, person, tense, True)
            if not last:
                return found
    return found


def find_bracket(tokens, fi, inf):
    """Index of the second verb element (participle / infinitive /
    separable prefix) in a main clause, or None."""
    if inf in AUXILIARIES or inf in MODALS:
        for j in range(fi + 1, len(tokens)):
            low = tokens[j].lower()
            if low in PARTICIPLES or low in INF_SET:
                return j
        return None
    if inf in SEP_INF:
        prefix = SEP_INF[inf][0]
        for j in range(fi + 1, len(tokens)):
            if tokens[j].lower() == prefix:
                return j
        return None
    # The finite verb may be the BASE of a separable verb ("komme" for
    # "ankommen" / "mitkommen"). A standalone prefix token after the verb
    # is then the bracket element — but not when it starts a prepositional
    # phrase ("Ich gehe aus dem Haus": "aus" + article is a preposition,
    # not the prefix of "ausgehen").
    cands = {prefix for sep_inf, (prefix, base) in SEP_INF.items()
             if base == inf}
    if cands:
        chunks = chunk_tokens(tokens)
        single = {a for (a, b, k) in chunks if b - a == 1}
        for j in range(fi + 1, len(tokens)):
            if tokens[j].lower() in cands and j in single:
                nxt = tokens[j + 1].lower() if j + 1 < len(tokens) else ""
                if nxt not in ARTICLES and nxt not in NOUNS:
                    return j
    return None


def _finding(code, segment, detail_fa="", detail_de=""):
    rule = RULES[code]
    return {
        "code": code,
        "title": rule["title"],
        "message_fa": rule["fa"] + (" " + detail_fa if detail_fa else ""),
        "message_de": rule["de"] + (" " + detail_de if detail_de else ""),
        "segment": segment,
        "example_ok": rule["example_ok"],
        "example_bad": rule["example_bad"],
    }


def _check_tekamolo(tokens, seg_idx, findings):
    chunks = chunk_tokens(tokens)
    adv = [(RANK[kind], a, " ".join(tokens[a:b]))
           for (a, b, kind) in chunks if kind in RANK]
    for j in range(1, len(adv)):
        if adv[j][0] < adv[j - 1][0]:
            order = {"time": "زمان", "manner": "حالت", "place": "مکان"}
            findings.append(_finding(
                "DWO-03", seg_idx,
                detail_fa="«%s» (%s) قبل از «%s» (%s) آمده است." % (
                    adv[j][2], order[["time", "manner", "place"][adv[j][0]]],
                    adv[j - 1][2], order[["time", "manner", "place"][adv[j - 1][0]]]),
                detail_de="«%s» steht vor «%s»." % (adv[j][2], adv[j - 1][2])))
            return


def _check_objects(tokens, fi, seg_idx, findings, window_start=0):
    """Object-order rules inside one clause window.

    window_start: first token index to consider (1 for subordinate
    clauses, to skip the subordinator; fi+1 for main clauses is
    handled by passing window_start=fi+1)."""
    pron = []
    for i in range(window_start, len(tokens)):
        if i == fi:
            continue
        low = tokens[i].lower()
        if low in AKK_PRONOUNS:
            pron.append((i, "akk"))
        elif low in DAT_PRONOUNS:
            pron.append((i, "dat"))
    if not pron:
        return
    chunks = chunk_tokens(tokens)
    noun_starts = [a for (a, b, kind) in chunks
                   if kind == "obj" and a >= window_start and a != fi]
    if noun_starts and min(noun_starts) < min(i for i, _ in pron):
        findings.append(_finding(
            "DWO-10", seg_idx,
            detail_fa="مفعول ضمیری («%s») باید قبل از مفعول اسمی بیاید." % tokens[min(i for i, _ in pron)],
            detail_de="Das pronominale Objekt muss vor dem nominalen Objekt stehen."))
        return
    akk = [i for i, c in pron if c == "akk"]
    dat = [i for i, c in pron if c == "dat"]
    if akk and dat and min(dat) < min(akk):
        findings.append(_finding(
            "DWO-10", seg_idx,
            detail_fa="«%s» (Dativ) قبل از «%s» (Akkusativ) آمده است؛ ترتیب درست: ضمیر Akkusativ اول می‌آید، بعد ضمیر Dativ." % (
                tokens[min(dat)], tokens[min(akk)]),
            detail_de="Akkusativ-Pronomen steht vor Dativ-Pronomen."))


def _split_coordinator_parts(tokens):
    """Split a main-clause token list at coordinators.

    A leading coordinator ("aber arbeitet er nicht") still splits:
    the first part is empty and skipped, the rest is part 1."""
    parts, cur = [], []
    for tok in tokens:
        if tok.lower() in COORDINATORS:
            parts.append(cur)
            cur = []
        else:
            cur.append(tok)
    if cur:
        parts.append(cur)
    return parts


def _analyze_main_part(tokens, seg_idx, findings, v2_code="DWO-01",
                       v1_code="DWO-07", after_subordinate=False):
    found = find_finite(tokens)
    if found is None:
        return False
    fi, inf, person, tense, attached = found
    if attached:
        findings.append(_finding(
            "DWO-04", seg_idx,
            detail_fa="فعل جداشدنی «%s» در جمله‌ی اصلی جدا نوشته می‌شود: «%s» + «%s»." % (
                inf, tokens[fi], SEP_INF[inf][0]),
            detail_de="Trennbares Verb «%s» wird im Hauptsatz getrennt." % inf))
        return True
    pre = tokens[:fi]
    pre_chunks = chunk_tokens(pre)
    pre_chunks = [c for c in pre_chunks if c[2] != "coord"]
    if after_subordinate:
        if fi != 0:
            findings.append(_finding(
                v2_code, seg_idx,
                detail_fa="بعد از جمله‌ی فرعیِ اول جمله، فعل جمله‌ی اصلی باید بلافاصله بعد از آن بیاید (وارونگی).",
                detail_de="Nach einem vorangestellten Nebensatz steht das finite Verb direkt danach (Inversion)."))
    elif len(pre_chunks) == 0:
        if fi + 1 < len(tokens) and tokens[fi + 1].lower() in SUBJECT_PRONOUNS:
            findings.append(_finding(
                v1_code, seg_idx,
                detail_fa="جمله با فعل شروع شده و بعد فاعل آمده است؛ یا باید سؤال باشد (با ؟) یا فاعل اول بیاید.",
                detail_de="Der Satz beginnt mit dem finiten Verb, danach folgt das Subjekt."))
    elif len(pre_chunks) >= 2:
        findings.append(_finding(
            v2_code, seg_idx,
            detail_fa="قبل از فعل «%s» دو جزء آمده است: «%s» و «%s». فقط یک جزء می‌تواند قبل از فعل باشد." % (
                tokens[fi], " ".join(tokens[pre_chunks[0][0]:pre_chunks[0][1]]),
                " ".join(tokens[pre_chunks[1][0]:pre_chunks[1][1]])),
            detail_de="Vor dem finiten Verb «%s» stehen zwei Satzglieder." % tokens[fi]))
    if fi > 0 and tokens[fi - 1].lower() == "nicht":
        findings.append(_finding(
            "DWO-09", seg_idx,
            detail_fa="«nicht» بلافاصله قبل از فعل «%s» آمده است." % tokens[fi],
            detail_de="«nicht» steht direkt vor dem finiten Verb «%s»." % tokens[fi]))
    bracket = find_bracket(tokens, fi, inf)
    if bracket is not None and bracket != len(tokens) - 1:
        findings.append(_finding(
            "DWO-04", seg_idx,
            detail_fa="بعد از «%s» هنوز «%s» آمده است؛ بخش دوم فعل باید آخرین کلمه‌ی جمله باشد." % (
                tokens[bracket], " ".join(tokens[bracket + 1:])),
            detail_de="Nach «%s» steht noch «%s»; der zweite Verbteil muss am Satzende stehen." % (
                tokens[bracket], " ".join(tokens[bracket + 1:]))))
    _check_tekamolo(tokens, seg_idx, findings)
    _check_objects(tokens, fi, seg_idx, findings, window_start=fi + 1)
    return True


def _analyze_subordinate(tokens, seg_idx, findings):
    found = find_finite(tokens, last=True)
    if found is None:
        return False
    fi, inf, person, tense, attached = found
    if fi != len(tokens) - 1:
        tail = tokens[fi + 1:]
        zu_tail = len(tail) == 2 and tail[0].lower() == "zu" \
            and tail[1].lower() in INF_SET
        if not zu_tail:
            findings.append(_finding(
                "DWO-02", seg_idx,
                detail_fa="در جمله‌ی فرعی فعل «%s» باید آخرین کلمه باشد؛ بعد از آن «%s» آمده است." % (
                    tokens[fi], " ".join(tail)),
                detail_de="Im Nebensatz muss «%s» am Ende stehen." % tokens[fi]))
    _check_tekamolo(tokens, seg_idx, findings)
    _check_objects(tokens, fi, seg_idx, findings, window_start=1)
    return True


def _analyze_question(tokens, seg_idx, findings):
    found = find_finite(tokens)
    if found is None:
        return False
    fi, inf, person, tense, attached = found
    first = tokens[0].lower() if tokens else ""
    has_w = any(t.lower() in W_WORDS for t in tokens)
    if has_w and first not in W_WORDS:
        w = next(t for t in tokens if t.lower() in W_WORDS)
        findings.append(_finding(
            "DWO-06", seg_idx,
            detail_fa="کلمه‌ی پرسشی «%s» اول جمله نیست." % w,
            detail_de="Das Fragewort «%s» steht nicht am Satzanfang." % w))
    elif first in W_WORDS:
        if fi != 1:
            findings.append(_finding(
                "DWO-06", seg_idx,
                detail_fa="بعد از کلمه‌ی پرسشی «%s» فعل «%s» باید بلافاصله بیاید." % (tokens[0], tokens[fi]),
                detail_de="Nach dem Fragewort «%s» muss das finite Verb direkt folgen." % tokens[0]))
    else:
        if fi != 0:
            findings.append(_finding(
                "DWO-05", seg_idx,
                detail_fa="سؤال بله/خیر باید با فعل «%s» شروع شود." % tokens[fi],
                detail_de="Eine Ja/Nein-Frage beginnt mit dem finiten Verb."))
    if attached:
        findings.append(_finding(
            "DWO-04", seg_idx,
            detail_fa="فعل جداشدنی «%s» در سؤال هم جدا نوشته می‌شود." % inf,
            detail_de="Trennbares Verb «%s» wird auch im Fragesatz getrennt." % inf))
    if fi > 0 and tokens[fi - 1].lower() == "nicht":
        findings.append(_finding("DWO-09", seg_idx))
    bracket = find_bracket(tokens, fi, inf)
    if bracket is not None and bracket != len(tokens) - 1:
        findings.append(_finding(
            "DWO-04", seg_idx,
            detail_fa="بعد از «%s» هنوز «%s» آمده است؛ بخش دوم فعل باید آخرین کلمه‌ی جمله باشد." % (
                tokens[bracket], " ".join(tokens[bracket + 1:]))))
    _check_tekamolo(tokens, seg_idx, findings)
    _check_objects(tokens, fi, seg_idx, findings, window_start=fi + 1)
    return True


def check_sentence(sentence):
    """Check one German sentence.

    Returns {"sentence", "verdict": "clean"|"findings"|"unknown",
    "findings": [...]}."""
    tokens, comma_after, final = tokenize(sentence)
    if not tokens:
        return {"sentence": sentence, "verdict": "unknown", "findings": []}
    segments = split_segments(tokens, comma_after)
    findings = []
    any_verb = False
    is_question = final == "?"
    for si, seg in enumerate(segments):
        if not seg:
            continue
        if seg[0].lower() in SUBORDINATORS:
            any_verb = _analyze_subordinate(seg, si, findings) or any_verb
            continue
        after_sub = si > 0 and segments[si - 1] and \
            segments[si - 1][0].lower() in SUBORDINATORS
        if is_question:
            any_verb = _analyze_question(seg, si, findings) or any_verb
            continue
        parts = _split_coordinator_parts(seg)
        for pi, part in enumerate(parts):
            if not part:
                continue
            code = "DWO-01" if pi == 0 else "DWO-08"
            ok = _analyze_main_part(part, si, findings, v2_code=code,
                                    v1_code=code if pi else "DWO-07",
                                    after_subordinate=after_sub and pi == 0)
            any_verb = ok or any_verb
    if not any_verb:
        return {"sentence": sentence, "verdict": "unknown", "findings": []}
    verdict = "findings" if findings else "clean"
    return {"sentence": sentence, "verdict": verdict, "findings": findings}

# ---------------------------------------------------------------------------
# Fixing — deterministic token surgery, re-checked after every step
# ---------------------------------------------------------------------------
def _finite_form(inf, person, tense):
    for v in VERBS:
        if v["inf"] == inf:
            forms = _presens_forms(v) if tense == "präsens" else _preterite_forms(v)
            return forms.get(person)
    if inf in IRREGULAR_PRESENS:
        if tense == "präsens":
            return IRREGULAR_PRESENS[inf].get(person)
        return _preterite_forms({"inf": inf}).get(person)
    return None


def _move_verb_after_first_chunk(tokens, fi):
    pre_chunks = [c for c in chunk_tokens(tokens[:fi]) if c[2] != "coord"]
    if not pre_chunks:
        return tokens
    _, b, _ = pre_chunks[0]
    return tokens[:b] + [tokens[fi]] + tokens[b:fi] + tokens[fi + 1:]


def _reorder_adverbials(tokens):
    chunks = chunk_tokens(tokens)
    adv = [c for c in chunks if c[2] in RANK]
    if len(adv) < 2:
        return tokens
    ordered = sorted(adv, key=lambda c: RANK[c[2]])
    if [c[2] for c in adv] == [c[2] for c in ordered]:
        return tokens
    new, i, k = [], 0, 0
    adv_by_start = {a: idx for idx, (a, _, _) in enumerate(adv)}
    while i < len(tokens):
        if i in adv_by_start:
            idx = adv_by_start[i]
            a, b, _ = ordered[idx]
            new.extend(tokens[a:b])
            i = adv[idx][1]
            k += 1
        else:
            new.append(tokens[i])
            i += 1
    return new


def _fix_part(tokens, kind, after_sub=False, v2_code="DWO-01",
              v1_code="DWO-07"):
    """Fix one coordinator-part (or a whole segment without coordinators)."""
    tokens = list(tokens)
    applied = []
    for _ in range(6):
        findings = []
        if kind == "sub":
            _analyze_subordinate(tokens, 0, findings)
        elif kind == "question":
            _analyze_question(tokens, 0, findings)
        else:
            _analyze_main_part(tokens, 0, findings, v2_code=v2_code,
                               v1_code=v1_code,
                               after_subordinate=after_sub)
        if not findings:
            break
        code = findings[0]["code"]
        found = find_finite(tokens)
        if found is None:
            break
        fi, inf, person, tense, attached = found
        new = None
        if code in ("DWO-01", "DWO-08"):
            if after_sub:
                new = [tokens[fi]] + tokens[:fi] + tokens[fi + 1:]
            else:
                pre_chunks = [c for c in chunk_tokens(tokens[:fi])
                              if c[2] != "coord"]
                if not pre_chunks and fi + 1 < len(tokens) and \
                        tokens[fi + 1].lower() in SUBJECT_PRONOUNS:
                    # verb-first clause ("und spreche ich ..."): swap
                    # verb and subject instead of moving the verb
                    new = tokens[:fi] + [tokens[fi + 1]] + [tokens[fi]] \
                        + tokens[fi + 2:]
                else:
                    new = _move_verb_after_first_chunk(tokens, fi)
        elif code == "DWO-07":
            chunks = chunk_tokens(tokens[fi + 1:])
            if chunks and chunks[0][2] in ("subj", "obj"):
                a, b, _ = chunks[0]
                new = tokens[:fi] + tokens[fi + 1 + a:fi + 1 + b] + [tokens[fi]] + tokens[fi + 1 + b:]
            else:
                new = tokens[:fi] + [tokens[fi + 1]] + [tokens[fi]] + tokens[fi + 2:]
        elif code == "DWO-02":
            new = tokens[:fi] + tokens[fi + 1:] + [tokens[fi]]
        elif code == "DWO-05":
            new = [tokens[fi]] + tokens[:fi] + tokens[fi + 1:]
        elif code == "DWO-06":
            wi = next(i for i, t in enumerate(tokens) if t.lower() in W_WORDS)
            wchunks = chunk_tokens(tokens)
            wspan = next((a, b) for (a, b, k) in wchunks if a == wi)
            rest = [t for i, t in enumerate(tokens)
                    if not (wspan[0] <= i < wspan[1]) and i != fi]
            new = tokens[wspan[0]:wspan[1]] + [tokens[fi]] + rest
        elif code == "DWO-04":
            if attached:
                prefix = SEP_INF[inf][0]
                base_inf = inf[len(prefix):]
                base = _finite_form(base_inf, person, tense) or tokens[fi]
                new = tokens[:fi] + [base] + tokens[fi + 1:] + [prefix]
            else:
                bi = find_bracket(tokens, fi, inf)
                if bi is None:
                    break
                new = tokens[:bi] + tokens[bi + 1:] + [tokens[bi]]
        elif code == "DWO-03":
            new = _reorder_adverbials(tokens)
        elif code == "DWO-09":
            new = tokens[:fi - 1] + [tokens[fi]] + ["nicht"] + tokens[fi + 1:]
        elif code == "DWO-10":
            pron_idx = [i for i in range(fi + 1, len(tokens))
                        if tokens[i].lower() in AKK_PRONOUNS
                        or tokens[i].lower() in DAT_PRONOUNS]
            if not pron_idx:
                break
            pron = [tokens[i] for i in pron_idx]
            ordered = sorted(pron, key=lambda t: 0 if t.lower() in AKK_PRONOUNS else 1)
            rest = [t for i, t in enumerate(tokens) if i not in pron_idx]
            new = rest[:fi + 1] + ordered + rest[fi + 1:]
        else:
            break
        if new is None or new == tokens:
            break
        tokens = new
        applied.append(code)
    return tokens, applied


def _fix_main_segment(tokens, after_sub=False):
    """Fix a main segment, preserving coordinator tokens."""
    # split into (coord, part) keeping coordinators
    groups = []
    cur, coord = [], None
    for tok in tokens:
        if tok.lower() in COORDINATORS:
            groups.append((coord, cur))
            coord, cur = tok, []
        else:
            cur.append(tok)
    groups.append((coord, cur))
    out, applied = [], []
    for gi, (coord, part) in enumerate(groups):
        if coord is not None:
            out.append(coord)
        if not part:
            continue
        fixed, codes = _fix_part(
            part, "main", after_sub=after_sub and gi == 0,
            v2_code="DWO-01" if gi == 0 else "DWO-08",
            v1_code="DWO-07" if gi == 0 else "DWO-08")
        out.extend(fixed)
        applied.extend(codes)
    return out, applied


def fix_sentence(sentence):
    """Deterministically fix a sentence. Returns dict with the fixed
    sentence, applied codes and any remaining findings."""
    tokens, comma_after, final = tokenize(sentence)
    if not tokens:
        return {"original": sentence, "fixed": sentence, "applied": [],
                "remaining": []}
    segments = split_segments(tokens, comma_after)
    is_question = final == "?"
    applied_all = []
    for _ in range(6):
        new_segments, applied_round = [], []
        for si, seg in enumerate(segments):
            if not seg:
                new_segments.append(seg)
                continue
            if seg[0].lower() in SUBORDINATORS:
                fixed, codes = _fix_part(seg, "sub")
            elif is_question:
                fixed, codes = _fix_part(seg, "question")
            else:
                after_sub = si > 0 and segments[si - 1] and \
                    segments[si - 1][0].lower() in SUBORDINATORS
                fixed, codes = _fix_main_segment(seg, after_sub=after_sub)
            new_segments.append(fixed)
            applied_round.extend(codes)
        if new_segments == segments:
            break
        segments = new_segments
        applied_all.extend(applied_round)
    fixed = join_sentence(segments, final)
    remaining = check_sentence(fixed)["findings"]
    return {"original": sentence, "fixed": fixed,
            "applied": sorted(set(applied_all)), "remaining": remaining}


# ---------------------------------------------------------------------------
# Data, quiz, Anki, explain, CLI
# ---------------------------------------------------------------------------
def load_sentences():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def scramble_words(sentence, seed):
    tokens, _, final = tokenize(sentence)
    rng = random.Random(seed)
    words = list(tokens)
    for _ in range(20):
        rng.shuffle(words)
        if words != tokens:
            break
    return " ".join(words), final


def quiz_questions(n=5, level=None, seed=0):
    data = load_sentences()
    if level:
        data = [d for d in data if d.get("level") == level]
    rng = random.Random(seed)
    picks = rng.sample(data, min(n, len(data))) if data else []
    out = []
    for i, item in enumerate(picks):
        scrambled, final = scramble_words(item["correct"], seed * 100 + i)
        out.append({"id": item["id"], "level": item.get("level"),
                    "rule": item.get("rule"), "fa": item.get("fa"),
                    "scrambled": scrambled + final,
                    "correct": item["correct"]})
    return out


def score_answers(questions, answers):
    results = []
    for q, ans in zip(questions, answers):
        ans = (ans or "").strip()
        ok = ans.rstrip(".?!") == q["correct"].rstrip(".?!")
        findings = check_sentence(ans)["findings"] if ans else []
        results.append({"id": q["id"], "correct": ok,
                        "your_answer": ans, "expected": q["correct"],
                        "findings": [f["code"] for f in findings]})
    return results


def anki_rows(level=None):
    rows = []
    for item in load_sentences():
        if level and item.get("level") != level:
            continue
        scrambled, final = scramble_words(item["correct"], hash(item["id"]) % 10000)
        front = "Ordne die Wörter: %s%s<br><small>Regel: %s · %s</small>" % (
            scrambled, final, item.get("rule", ""), item.get("level", ""))
        back = "%s<br>%s<br><small>%s — %s</small>" % (
            item["correct"], item.get("fa", ""), item.get("rule", ""),
            RULES.get(item.get("rule", ""), {}).get("title", ""))
        rows.append((front, back))
    return rows


def explain_rule(code):
    code = code.upper()
    if code not in RULES:
        return None
    r = RULES[code]
    return {"code": code, "title": r["title"], "fa": r["fa"], "de": r["de"],
            "example_ok": r["example_ok"], "example_bad": r["example_bad"]}


def _print_check(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verdict"] == "clean" else 1
    if result["verdict"] == "clean":
        print("✓ Keine Fehler gefunden — جمله درست است.")
        return 0
    if result["verdict"] == "unknown":
        print("؟ فعل شناخته‌شده‌ای پیدا نشد — نمی‌توانم قضاوت کنم (واژه در فهرست A1–B1 نیست).")
        print("  No known finite verb found — cannot judge (verb not in the A1–B1 list).")
        return 1
    for f in result["findings"]:
        print("✗ [%s] %s" % (f["code"], f["title"]))
        print("  %s" % f["message_fa"])
        print("  درست: %s" % f["example_ok"])
    return 1


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 2
    cmd = argv[1]
    as_json = "--json" in argv
    args = [a for a in argv[2:] if a != "--json"]

    if cmd == "check":
        if not args:
            print("usage: check \"<sentence>\" [--json]", file=sys.stderr)
            return 2
        return _print_check(check_sentence(" ".join(args)), as_json)

    if cmd == "fix":
        if not args:
            print("usage: fix \"<sentence>\" [--json]", file=sys.stderr)
            return 2
        result = fix_sentence(" ".join(args))
        if as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["fixed"])
            if result["applied"]:
                print("اصلاح شد: %s" % ", ".join(result["applied"]))
            if result["remaining"]:
                print("باقی‌مانده (خودکار اصلاح نشد): %s" %
                      ", ".join(f["code"] for f in result["remaining"]))
        return 0 if not result["remaining"] else 1

    if cmd == "explain":
        if not args:
            print("usage: explain DWO-01", file=sys.stderr)
            return 2
        r = explain_rule(args[0])
        if r is None:
            print("unknown rule: %s (DWO-01..DWO-10)" % args[0], file=sys.stderr)
            return 2
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print("[%s] %s" % (r["code"], r["title"]))
            print(r["fa"])
            print(r["de"])
            print("✓ %s" % r["example_ok"])
            print("✗ %s" % r["example_bad"])
        return 0

    if cmd == "rules":
        for code in sorted(RULES):
            print("%s — %s" % (code, RULES[code]["title"]))
        return 0

    if cmd == "quiz":
        n, level, seed = 5, None, 0
        answers = None
        i = 0
        while i < len(args):
            if args[i] == "--n" and i + 1 < len(args):
                n, i = int(args[i + 1]), i + 2
            elif args[i] == "--level" and i + 1 < len(args):
                level, i = args[i + 1], i + 2
            elif args[i] == "--seed" and i + 1 < len(args):
                seed, i = int(args[i + 1]), i + 2
            elif args[i] == "--answers" and i + 1 < len(args):
                answers, i = args[i + 1].split("|"), i + 2
            else:
                i += 1
        questions = quiz_questions(n, level, seed)
        if as_json:
            print(json.dumps({"questions": questions}, ensure_ascii=False, indent=2))
            return 0
        if answers is not None:
            results = score_answers(questions, answers)
            good = sum(1 for r in results if r["correct"])
            for r in results:
                mark = "✓" if r["correct"] else "✗"
                print("%s %s — شما: %s" % (mark, r["id"], r["your_answer"]))
                if not r["correct"]:
                    print("  درست: %s" % r["expected"])
                    if r["findings"]:
                        print("  خطاها: %s" % ", ".join(r["findings"]))
            print("نتیجه: %d/%d درست" % (good, len(results)))
            return 0 if good == len(results) else 1
        for q in questions:
            print("[%s · %s · %s] %s" % (q["id"], q["level"], q["rule"], q["scrambled"]))
            print("  معنی: %s" % q["fa"])
        return 0

    if cmd == "anki":
        level, out = None, None
        i = 0
        while i < len(args):
            if args[i] == "--level" and i + 1 < len(args):
                level, i = args[i + 1], i + 2
            elif args[i] == "--out" and i + 1 < len(args):
                out, i = args[i + 1], i + 2
            else:
                i += 1
        rows = anki_rows(level)
        text = "".join("%s\t%s\n" % r for r in rows)
        if out:
            Path(out).write_text(text, encoding="utf-8")
            print("wrote %d cards to %s" % (len(rows), out))
        else:
            print(text, end="")
        return 0

    if cmd == "list":
        level = None
        if "--level" in args:
            level = args[args.index("--level") + 1]
        for item in load_sentences():
            if level and item.get("level") != level:
                continue
            print("[%s · %s · %s] %s — %s" % (
                item["id"], item.get("level"), item.get("rule"),
                item["correct"], item.get("fa", "")))
        return 0

    print("unknown command: %s" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
