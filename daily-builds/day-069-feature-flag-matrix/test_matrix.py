import unittest
from matrix import generate, pairs

def data(): return {"flags":["a","b"],"environments":["staging"],"requires":[]}
class Tests(unittest.TestCase):
    def test_exhaustive(self): self.assertEqual(generate(data())["summary"]["scenarios"],4)
    def test_dependency(self):
        d=data();d["requires"]=[["a","b"]]
        self.assertEqual(generate(d)["summary"]["valid_combinations"],3)
    def test_no_invalid_scenario(self):
        d=data();d["requires"]=[["a","b"]]
        self.assertTrue(all(not s["flags"]["a"] or s["flags"]["b"] for s in generate(d)["scenarios"]))
    def test_environments(self):
        d=data();d["environments"]=["staging","production"]
        self.assertEqual(generate(d)["summary"]["scenarios"],8)
    def test_order_invariant(self):
        d=data();d["flags"].reverse()
        self.assertEqual(generate(d),generate(data()))
    def test_cycles(self):
        d=data();d["requires"]=[["a","b"],["b","a"]]
        self.assertEqual(generate(d)["summary"]["valid_combinations"],2)
    def test_unique_ids(self):
        rows=generate(data())["scenarios"]
        self.assertEqual(len({s["id"] for s in rows}),len(rows))
    def test_unknown_dependency(self):
        d=data();d["requires"]=[["a","c"]]
        with self.assertRaises(ValueError): generate(d)
    def test_duplicate_names(self):
        d=data();d["flags"]=["a","a"]
        with self.assertRaises(ValueError): generate(d)
    def test_bound(self):
        d=data();d["flags"]=[f"f{i}" for i in range(9)]
        with self.assertRaises(ValueError): generate(d)
    def test_unknown_field(self):
        d=data();d["extra"]=True
        with self.assertRaises(ValueError): generate(d)
    def test_duplicate_key(self):
        with self.assertRaises(ValueError): pairs([("x",1),("x",2)])
if __name__=="__main__": unittest.main()
