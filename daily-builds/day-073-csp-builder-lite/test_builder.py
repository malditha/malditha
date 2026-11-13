import json
import unittest
from builder import build, unique

class BuilderTests(unittest.TestCase):
    def test_prefix(self): self.assertEqual(build({'default-src':["'self'"]}),"Content-Security-Policy-Report-Only: default-src 'self'")
    def test_order(self): self.assertTrue(build({'img-src':['https://b.example','https://a.example'],'default-src':["'none'"]}).endswith('img-src https://a.example https://b.example'))
    def test_missing_default(self):
        with self.assertRaises(ValueError): build({'img-src':["'self'"]})
    def test_unknown(self):
        with self.assertRaises(ValueError): build({'default-src':["'self'"],'unknown':[]})
    def test_none_alone(self):
        with self.assertRaises(ValueError): build({'default-src':["'none'","'self'"]})
    def test_duplicates(self):
        with self.assertRaises(ValueError): build({'default-src':["'self'","'self'"]})
    def test_sources(self):
        for x in ['*','http://example.com','https://x.test/path','https://x.test; img-src *',"'unsafe-inline'",'https://x.test:99999','https://x.test\n','data:',True]:
            with self.subTest(x=x),self.assertRaises(ValueError): build({'default-src':[x]})
    def test_port(self): self.assertIn('https://example.test:8443',build({'default-src':['https://example.test:8443']}))
    def test_empty(self):
        with self.assertRaises(ValueError): build({'default-src':[]})
    def test_wrong_type(self):
        with self.assertRaises(ValueError): build({'default-src':"'self'"})
    def test_key_duplicates(self):
        with self.assertRaises(ValueError): json.loads('{"a":1,"a":2}',object_pairs_hook=unique)
    def test_no_implicit_directives(self): self.assertNotIn('frame-ancestors',build({'default-src':["'none'"]}))

if __name__=='__main__': unittest.main()
