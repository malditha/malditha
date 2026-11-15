import json
import unittest
from scanner import scan, LIMIT

class ScannerTests(unittest.TestCase):
    def test_empty(self): self.assertEqual(scan('')['count'], 0)
    def test_assignment(self): self.assertEqual(scan('API_KEY = fictional-example')['count'], 1)
    def test_export(self): self.assertEqual(scan('export password: example')['count'], 1)
    def test_marker(self): self.assertEqual(scan('-----BEGIN PRIVATE KEY-----')['findings'][0]['rule'], 'private-key-marker')
    def test_marker_variants(self):
        for kind in ['RSA ', 'EC ', 'OPENSSH ', 'ENCRYPTED ']:
            self.assertEqual(scan('-----BEGIN '+kind+'PRIVATE KEY-----')['count'], 1)
    def test_comments(self): self.assertEqual(scan('# password=example')['count'], 0)
    def test_blank_value(self): self.assertEqual(scan('password=  ')['count'], 0)
    def test_unknown(self): self.assertEqual(scan('my_password=example')['count'], 0)
    def test_line_numbers(self): self.assertEqual(scan('\npassword=example\r\napi_key=example')['findings'][1]['line'], 3)
    def test_no_values(self): self.assertNotIn('fictional-example', json.dumps(scan('password=fictional-example')))
    def test_placeholder_flagged(self): self.assertEqual(scan('password=${PASSWORD}')['count'], 1)
    def test_size(self):
        with self.assertRaises(ValueError): scan('x'*(LIMIT+1))
    def test_nul(self):
        with self.assertRaises(ValueError): scan('x\0')
    def test_type(self):
        with self.assertRaises(ValueError): scan(None)

if __name__ == '__main__': unittest.main()
