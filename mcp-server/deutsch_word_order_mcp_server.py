#!/usr/bin/env python3
"""MCP server for deutsch-word-order-fa — expose the German word-order
engine as tools for any MCP client.

Zero-dependency (Python standard library only). Speaks JSON-RPC 2.0
over stdio, newline-delimited, following the MCP lifecycle:

    initialize -> notifications/initialized -> tools/list -> tools/call

Tools:
    check_sentence
        sentence  German sentence to check (required)
        format    "text" (default) or "json"
    fix_sentence
        sentence  German sentence to fix (required)
        format    "text" (default) or "json"
    explain_rule
        code      DWO-01 .. DWO-10 (required)
        format    "text" (default) or "json"
    quiz
        n       number of questions (default 5)
        level   A1 | A2 | B1 (optional)
        seed    integer seed for a reproducible set (optional)
        answers pipe-separated answers to score non-interactively
    anki_export
        level   A1 | A2 | B1 (optional)
    list_sentences
        level   A1 | A2 | B1 (optional)

The server runs skills/deutsch-word-order-fa/scripts/deutsch_word_order.py
as a subprocess; exit-code semantics are preserved in the returned text
(check: 1 = findings; fix: 1 = remaining findings).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "skills" / "deutsch-word-order-fa" / "scripts" / "deutsch_word_order.py"

SERVER_INFO = {"name": "deutsch-word-order-fa", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(ENGINE), *args],
                          capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _with_exit(code, out, err):
    lines = []
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_check_sentence(args):
    sentence = args.get("sentence")
    if not sentence:
        raise ValueError("check_sentence requires 'sentence'")
    cmd = ["check", sentence]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_fix_sentence(args):
    sentence = args.get("sentence")
    if not sentence:
        raise ValueError("fix_sentence requires 'sentence'")
    cmd = ["fix", sentence]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_explain_rule(args):
    code_arg = args.get("code")
    if not code_arg:
        raise ValueError("explain_rule requires 'code' (DWO-01..DWO-10)")
    cmd = ["explain", code_arg]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_quiz(args):
    cmd = ["quiz"]
    if args.get("n"):
        cmd += ["--n", str(args["n"])]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    if args.get("seed") is not None:
        cmd += ["--seed", str(args["seed"])]
    if args.get("answers"):
        cmd += ["--answers", args["answers"]]
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


def tool_anki_export(args):
    cmd = ["anki"]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    code, out, err = run_cli(*cmd)
    lines = [f"anki exit code: {code}",
             f"{len(out.splitlines())} cards (TSV: front<TAB>back)"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_list_sentences(args):
    cmd = ["list"]
    if args.get("level"):
        cmd += ["--level", args["level"]]
    code, out, err = run_cli(*cmd)
    return _with_exit(code, out, err)


TOOLS = [
    {
        "name": "check_sentence",
        "description": (
            "Check a Persian-speaking learner's German sentence for "
            "word-order errors — verb-second (V2), verb-final in "
            "subordinate clauses, TeKaMoLo adverbial order, sentence "
            "bracket, question inversion, 'nicht' placement, object "
            "order — only where deterministically decidable. "
            "Conservative: no finding does not mean the sentence is "
            "perfect. Explanations in Persian."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sentence": {"type": "string",
                             "description": "German sentence to check"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["sentence"],
        },
    },
    {
        "name": "fix_sentence",
        "description": (
            "Deterministically fix a learner's German sentence by "
            "reordering its words according to the word-order rules, "
            "then re-check it. Returns the fixed sentence, the applied "
            "rule codes, and any findings that could not be fixed "
            "automatically."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sentence": {"type": "string",
                             "description": "German sentence to fix"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["sentence"],
        },
    },
    {
        "name": "explain_rule",
        "description": (
            "Explain one word-order rule (DWO-01..DWO-10) in Persian, "
            "with a correct and a wrong example sentence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string",
                         "description": "rule code, e.g. DWO-03"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "quiz",
        "description": (
            "Drill German word order: scrambled correct sentences from "
            "the curated A1-B1 list for the learner to reorder. Pass "
            "answers to score non-interactively; pass a seed for a "
            "reproducible set."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer",
                      "description": "number of questions (default 5)"},
                "level": {"type": "string", "enum": ["A1", "A2", "B1"],
                          "description": "restrict to one level"},
                "seed": {"type": "integer",
                         "description": "seed for a reproducible question set"},
                "answers": {"type": "string",
                            "description": "pipe-separated answers to score"},
            },
        },
    },
    {
        "name": "anki_export",
        "description": (
            "Export the 48 curated sentence pairs as Anki-importable TSV "
            "(front: scrambled sentence + rule hint; back: correct "
            "sentence + Persian meaning + rule)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["A1", "A2", "B1"],
                          "description": "restrict to one level"},
            },
        },
    },
    {
        "name": "list_sentences",
        "description": (
            "List the curated sentence pairs (correct sentence, level, "
            "rule, Persian meaning), optionally filtered by level."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["A1", "A2", "B1"]},
            },
        },
    },
]

HANDLERS = {
    "check_sentence": tool_check_sentence,
    "fix_sentence": tool_fix_sentence,
    "explain_rule": tool_explain_rule,
    "quiz": tool_quiz,
    "anki_export": tool_anki_export,
    "list_sentences": tool_list_sentences,
}


def handle(request):
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": TOOLS},
        }
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32602,
                          "message": f"unknown tool: {name}"},
            }
        try:
            text = handler(arguments)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as exc:  # noqa: BLE001 - surface as tool error
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text",
                                        "text": f"error: {exc}"}],
                           "isError": True},
            }
    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
