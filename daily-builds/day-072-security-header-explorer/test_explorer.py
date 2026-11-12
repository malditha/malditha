import unittest
from explorer import inspect

class ExplorerTests(unittest.TestCase):
    def item(self, text, name):
        return next(x for x in inspect(text) if x['header'] == name)
    def test_missing(self): self.assertTrue(all(x['status']=='missing' for x in inspect('')))
    def test_case(self): self.assertEqual(self.item('X-Content-Type-Options: nosniff','x-content-type-options')['status'],'present')
    def test_empty(self): self.assertEqual(self.item('Referrer-Policy: ','referrer-policy')['status'],'empty')
    def test_duplicate(self): self.assertEqual(self.item('Referrer-Policy: a\nreferrer-policy: b','referrer-policy')['occurrences'],2)
    def test_no_values(self): self.assertNotIn('private-value',str(inspect('Content-Security-Policy: private-value\nSet-Cookie: private-value')))
    def test_invalid_nosniff(self): self.assertTrue(self.item('X-Content-Type-Options: other','x-content-type-options')['notes'])
    def test_valid_nosniff(self): self.assertFalse(self.item('X-Content-Type-Options: nosniff','x-content-type-options')['notes'])
    def test_status_rejected(self):
        with self.assertRaises(ValueError): inspect('HTTP/2 200')
    def test_fold_rejected(self):
        with self.assertRaises(ValueError): inspect(' a: b')
    def test_name_rejected(self):
        with self.assertRaises(ValueError): inspect('bad name: b')
    def test_control_rejected(self):
        with self.assertRaises(ValueError): inspect('Name: a\x00')
    def test_size(self):
        with self.assertRaises(ValueError): inspect('a'*65537)
    def test_crlf(self): self.assertEqual(len(inspect('Referrer-Policy: no-referrer\r\n')),6)

if __name__=='__main__': unittest.main()
