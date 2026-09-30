import io
import unittest

from output_meter import analyze


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
