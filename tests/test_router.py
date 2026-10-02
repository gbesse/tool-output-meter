import unittest

from router import audit, topic_tag


class RouterTests(unittest.TestCase):
    def test_same_topic_in_two_chats_gets_different_tags(self):
        first = {"platform": "telegram", "chat_id": 1, "topic_id": 5}
        second = {"platform": "telegram", "chat_id": 2, "topic_id": 5}
        self.assertNotEqual(topic_tag(first), topic_tag(second))
        self.assertEqual(topic_tag(first), topic_tag(first))

    def test_audit_excludes_other_topics(self):
        event = {"platform": "telegram", "chat_id": 1, "topic_id": 5}
        rows = [{"tags": [topic_tag(event)]}, {"tags": [topic_tag({**event, "topic_id": 6})]}]
        self.assertEqual((audit(event, rows)["matching_records"], audit(event, rows)["excluded_records"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
