import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from receipt import observe, read_status


class ReceiptTests(unittest.TestCase):
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
