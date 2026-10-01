import io
import unittest

import json
import tempfile
from pathlib import Path
from zipfile import ZipFile

from output_meter import analyze, analyze_context, read_dsh


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
