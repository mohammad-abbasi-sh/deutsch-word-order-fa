#!/usr/bin/env python3
"""MCP stdio end-to-end tests for deutsch-word-order-fa — run with:
    python3 -m unittest discover -s tests -v
Zero dependencies (stdlib unittest only)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "mcp-server" / "deutsch_word_order_mcp_server.py"


def mcp_session(requests):
    payload = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run([sys.executable, str(SERVER)], input=payload,
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


class TestMCPServer(unittest.TestCase):
    def test_initialize_and_list(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05",
                        "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "deutsch-word-order-fa")
        names = [t["name"] for t in responses[1]["result"]["tools"]]
        self.assertEqual(names, ["check_sentence", "fix_sentence", "explain_rule",
                                 "quiz", "anki_export", "list_sentences"])

    def test_check_sentence_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "check_sentence",
                        "arguments": {"sentence": "Ich jeden Tag gehe zur Schule."}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertIn("DWO-01", text)

    def test_check_sentence_json(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "check_sentence",
                        "arguments": {"sentence": "Ich gehe zur Schule.",
                                      "format": "json"}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertEqual(json.loads(text)["verdict"], "clean")

    def test_fix_sentence_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "fix_sentence",
                        "arguments": {"sentence": "Ich bleibe zu Hause, weil ich bin krank."}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertIn("Ich bleibe zu Hause, weil ich krank bin.", text)

    def test_explain_rule_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "explain_rule", "arguments": {"code": "DWO-03"}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertIn("TeKaMoLo", text)

    def test_quiz_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "quiz", "arguments": {"n": 2, "seed": 5}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertIn("S", text)

    def test_anki_export_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "anki_export", "arguments": {"level": "A1"}}},
        ])
        text = responses[0]["result"]["content"][0]["text"]
        self.assertIn("cards (TSV", text)
        self.assertIn("Ordne die Wörter", text)

    def test_unknown_tool(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "nope", "arguments": {}}},
        ])
        self.assertEqual(responses[0]["error"]["code"], -32602)

    def test_unknown_method(self):
        responses = mcp_session([
            {"jsonrpc": "2.0", "id": 1, "method": "resources/list"},
        ])
        self.assertEqual(responses[0]["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
