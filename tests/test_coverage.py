import unittest

from coverage import audit


class CoverageTests(unittest.TestCase):
    def test_marked_unlinked_is_distinct_from_pending(self):
        facts = [{"id": "f1", "consolidated_at": "now"}, {"id": "f2", "consolidated_at": "now"}, {"id": "f3"}]
        result = audit(facts, [{"source_memory_ids": ["f1"]}])
        self.assertEqual((result["represented"], result["marked_but_unlinked"], result["pending_unlinked"]), (1, 1, 1))

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            audit([{"id": "f1"}, {"id": "f1"}], [])

    def test_unknown_source_link_reported(self):
        result = audit([{"id": "f1"}], [{"source_memory_ids": ["missing"]}])
        self.assertEqual(result["unknown_source_links"], 1)

    def test_missing_source_ids_are_not_assumed_empty(self):
        with self.assertRaises(ValueError):
            audit([{"id": "f1", "consolidated_at": "now"}], [{"id": "o1"}])


if __name__ == "__main__":
    unittest.main()
