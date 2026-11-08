import copy
import json
import unittest
from pathlib import Path
from repro import render, pairs

BASE = json.loads(Path(__file__).with_name("sample.json").read_text())
class Tests(unittest.TestCase):
    def data(self): return copy.deepcopy(BASE)
    def test_title(self): self.assertTrue(render(BASE).startswith("# Draft"))
    def test_ordered_steps(self): self.assertIn("3. Close and reopen", render(BASE))
    def test_expected_actual(self): self.assertIn("## Actual result", render(BASE))
    def test_frequency(self): self.assertIn("2 of 3 attempts.", render(BASE))
    def test_environment_order(self):
        d=self.data();d["environment"]=dict(reversed(list(d["environment"].items())))
        self.assertEqual(render(d),render(BASE))
    def test_escape(self):
        d=self.data();d["title"]="<test>"
        self.assertIn("\\<test\\>",render(d))
    def test_empty_steps(self):
        d=self.data();d["steps"]=[]
        with self.assertRaises(ValueError): render(d)
    def test_invalid_frequency(self):
        d=self.data();d["frequency"]["observed"]=4
        with self.assertRaises(ValueError): render(d)
    def test_boolean_count(self):
        d=self.data();d["frequency"]["observed"]=True
        with self.assertRaises(ValueError): render(d)
    def test_unknown_field(self):
        d=self.data();d["secret"]="x"
        with self.assertRaises(ValueError): render(d)
    def test_control_character(self):
        d=self.data();d["title"]="x\ny"
        with self.assertRaises(ValueError): render(d)
    def test_duplicate_key(self):
        with self.assertRaises(ValueError): pairs([("x",1),("x",2)])
if __name__=="__main__": unittest.main()
