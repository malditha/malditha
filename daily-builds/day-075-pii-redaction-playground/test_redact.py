import json
import unittest
from redact import transform, MARKER, LIMIT

def run(value, keys): return transform(json.dumps(value).encode(), keys)

class RedactionTests(unittest.TestCase):
    def test_selected(self): self.assertEqual(run({'email':'demo@example.test'},['email']),{'email':MARKER})
    def test_case(self): self.assertEqual(run({'EMAIL':'demo'},['email'])['EMAIL'],MARKER)
    def test_nested_array(self): self.assertEqual(run([{'person':{'name':'Demo'}}],['name'])[0]['person']['name'],MARKER)
    def test_subtree(self): self.assertEqual(run({'person':{'name':'Demo'}},['person']),{'person':MARKER})
    def test_unselected(self): self.assertEqual(run({'note':'demo@example.test'},['email']),{'note':'demo@example.test'})
    def test_exact(self): self.assertEqual(run({'email_opt_in':True},['email']),{'email_opt_in':True})
    def test_scalar(self): self.assertEqual(run('demo',['email']),'demo')
    def test_null(self): self.assertEqual(run({'email':None},['email']),{'email':MARKER})
    def test_idempotent(self):
        a=run({'email':'demo'},['email']);self.assertEqual(run(a,['email']),a)
    def test_duplicate(self):
        with self.assertRaises(ValueError): transform(b'{"a":1,"a":2}',['a'])
    def test_invalid(self):
        for b in [b'{',b'NaN',b'\xff',b' '* (LIMIT+1)]:
            with self.assertRaises(ValueError): transform(b,['email'])
    def test_keys(self):
        for k in [[],[''],['x'*101]]:
            with self.assertRaises(ValueError): run({},k)
    def test_depth(self):
        value=0
        for _ in range(42):value=[value]
        with self.assertRaises(ValueError):run(value,['email'])
    def test_no_mutation(self):
        v={'email':'demo'};run(v,['email']);self.assertEqual(v,{'email':'demo'})

if __name__ == '__main__':unittest.main()
