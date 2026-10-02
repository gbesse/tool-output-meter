import io
import unittest

import json
import tempfile
from pathlib import Path
from zipfile import ZipFile

from output_meter import analyze, analyze_context, analyze_memory_arrival, read_dsh, render_memory_html


class OutputMeterTests(unittest.TestCase):
    def test_counts_repeated_and_truncated_outputs(self):
        data = io.StringIO('''{"type":"response_item","payload":{"type":"function_call","call_id":"1","name":"search"}}\n{"type":"response_item","payload":{"type":"function_call_output","call_id":"1","output":"same"}}\n{"type":"response_item","payload":{"type":"function_call_output","call_id":"2","output":"same"}}\n{"type":"response_item","payload":{"type":"function_call_output","call_id":"3","output":"Warning: truncated output"}}\n''')
        result = analyze(data)
        self.assertEqual(result["repeated_outputs"], 2)
        self.assertEqual(result["truncated_outputs"], 1)
        self.assertNotIn("sha256", result["top"][0])

    def test_no_outputs_is_error(self):
        with self.assertRaises(ValueError):
            analyze(io.StringIO('{"type":"session_meta","payload":{}}\n'))

    def test_dsh_injected_context_repeats_without_echoing_content(self):
        path = Path(__file__).parents[1] / "fixtures" / "dsh-session.jsonl"
        result = analyze_context(read_dsh(path))
        self.assertEqual(result["injections"], 3)
        self.assertEqual(result["repeated_injections"], 2)
        self.assertEqual(result["groups"][0]["last_turn"], 3)
        self.assertNotIn("Project context", json.dumps(result))

    def test_dsh_export_zip_uses_root_session_only(self):
        path = Path(__file__).parents[1] / "fixtures" / "dsh-session.jsonl"
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "export.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.write(path, "session.v4.jsonl")
                archive.writestr("subagents/child/session.v4.jsonl", "not JSON")
            self.assertEqual(analyze_context(read_dsh(archive_path))["repeated_injections"], 2)

    def test_dsh_replacement_is_not_counted_as_accumulating(self):
        path = Path(__file__).parents[1] / "fixtures" / "dsh-session.jsonl"
        lines = path.read_text().splitlines()
        last = json.loads(lines[-1])
        last["surfaceOp"] = {"op": "replace", "startSeq": 2, "endSeq": 3}
        lines[-1] = json.dumps(last)
        result = analyze_context((line + "\n" for line in lines))
        self.assertEqual(result["repeated_injections"], 1)
        self.assertEqual(result["replaced_or_unverified_surface_events"], 1)

    def test_turn_boundary_supplies_turn_when_message_omits_it(self):
        source = {"kind": "plugin:@vectorize-io/hindsight-coding-agents"}
        text = "A project rule for repeated context that is long enough to remain comparable across turns."
        records = [
            {"type": "turn/start", "data": {"turn": 1}},
            {"type": "user/message", "surfaceOp": "append", "data": {"source": source, "content": [{"type": "text", "text": text}]}},
            {"type": "turn/end", "data": {"turn": 1}},
            {"type": "turn/start", "data": {"turn": 2}},
            {"type": "user/message", "surfaceOp": "append", "data": {"source": source, "content": [{"type": "text", "text": text}]}},
        ]
        result = analyze_context((json.dumps(item) for item in records))
        self.assertEqual(result["groups"][0]["first_turn"], 1)
        self.assertEqual(result["groups"][0]["last_turn"], 2)

    def test_memory_arrival_distinguishes_present_empty_and_missing_without_text(self):
        path = Path(__file__).parents[1] / "fixtures" / "memory-arrival.jsonl"
        result = analyze_memory_arrival(read_dsh(path))
        self.assertEqual((result["confirmed_memory"], result["empty_memory"], result["without_injection"]), (1, 1, 1))
        self.assertNotIn("release requires", json.dumps(result))

    def test_unknown_hindsight_wrapper_is_not_claimed_empty(self):
        record = {"type": "user/message", "data": {"turn": 1, "source": {"kind": "plugin:hindsight"},
                  "content": [{"type": "text", "text": "memory format changed"}]}}
        result = analyze_memory_arrival([json.dumps(record)])
        self.assertEqual(result["unclassified"], 1)
        self.assertEqual(result["empty_memory"], 0)

    def test_memory_xray_html_escapes_turn_and_omits_memory_text(self):
        result = {"turns": 1, "timeline": [{"turn": "<script>", "status": "confirmed_memory"}],
                  "note": "Content-free report"}
        page = render_memory_html(result, "fr")
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)
        self.assertIn('lang="fr"', page)
