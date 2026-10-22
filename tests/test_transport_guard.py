import unittest
from unittest.mock import patch
from receipt import read_document,read_status,checked_request
class TransportGuardTests(unittest.TestCase):
 def test_library_functions_reject_unsafe_bearer_transport_before_network(self):
  with patch('receipt.build_opener') as opener:
   for reader in (read_document,read_status):
    for url in ('http://example.com/x','https://user@example.com/x','https://example.com/x#fragment','https://example.com:99999/x'):
     with self.assertRaises(ValueError):reader(url,'synthetic-token')
   opener.assert_not_called()
 def test_loopback_and_https_allowed_without_exposing_token_in_errors(self):
  self.assertEqual(checked_request('http://127.0.0.1:42/x','synthetic').get_method(),'GET')
  for token in ('private\rvalue','private\nvalue',True):
   with self.assertRaises(ValueError) as e:checked_request('https://example.com',token)
   self.assertNotIn('private',str(e.exception))
