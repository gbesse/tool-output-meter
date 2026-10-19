import unittest
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from receipt import observe, read_status, read_document, TEXT


class ReceiptTests(unittest.TestCase):
    def test_http_200_without_content_cannot_satisfy_identity_check(self):
        result = observe(lambda: 200, expected_sha256=hashlib.sha256(b'expected').hexdigest())
        self.assertEqual(result['status'], 'content_unverified')
        self.assertFalse(result['identity_verified'])

    def test_wrong_content_stops_without_retrying_or_showing_text(self):
        digest = hashlib.sha256(b'private wrong document').hexdigest()
        result = observe(lambda: {'http_status': 200, 'content_sha256': digest}, attempts=10, expected_sha256=hashlib.sha256(b'expected').hexdigest())
        self.assertEqual(result['status'], 'content_mismatch')
        self.assertEqual(result['attempts'], 1)
        self.assertNotIn('private wrong document', str(result))
        self.assertTrue(all('content_mismatch' in TEXT[lang] for lang in ('fr', 'en', 'es')))

    def test_real_get_hashes_exact_bytes_and_rejects_oversized_body(self):
        body = 'document synthétique 🛰️'.encode()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.end_headers(); self.wfile.write(body)
            def log_message(self, *_args): pass
        server = HTTPServer(('127.0.0.1', 0), Handler); thread = Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/document'
            receipt = read_document(url)
            result = observe(lambda: receipt, expected_sha256=hashlib.sha256(body).hexdigest())
            self.assertTrue(result['identity_verified'])
            self.assertEqual(result['content_bytes'], len(body))
            limited = observe(lambda: read_document(url, max_bytes=3), expected_sha256=hashlib.sha256(body[:3]).hexdigest())
            self.assertEqual(limited['status'], 'body_limit')
            self.assertFalse(limited['identity_verified'])
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_invalid_digest_and_nonfinite_polling_options_fail_before_fetch(self):
        def forbidden(): self.fail('invalid configuration contacted server')
        for options in ({'expected_sha256': 'not-a-hash'}, {'attempts': True}, {'interval': float('nan')}):
            with self.assertRaises(ValueError): observe(forbidden, **options)

    def test_lag_then_visible(self):
        codes = iter([404, 404, 200])
        result = observe(lambda: next(codes), attempts=3, interval=0)
        self.assertEqual((result["status"], result["attempts"]), ("visible", 3))

    def test_denied_is_not_retried_as_pending(self):
        result = observe(lambda: 403, attempts=5, interval=0)
        self.assertEqual((result["status"], result["attempts"]), ("denied", 1))

    def test_persistent_404_remains_unproven(self):
        result = observe(lambda: 404, attempts=2, interval=0)
        self.assertEqual(result["status"], "not_visible")

    def test_read_status_uses_get_against_local_http_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"visible": true}')

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertEqual(read_status(f"http://127.0.0.1:{server.server_port}/documents/demo"), 200)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
