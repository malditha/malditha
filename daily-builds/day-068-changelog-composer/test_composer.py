import copy
import unittest
from composer import compose, pairs

BASE={"version":"1.0","date":"2026-11-06","changes":[{"id":"a","category":"Fixed","summary":"Repair export.","breaking":False}]}
class Tests(unittest.TestCase):
    def data(self): return copy.deepcopy(BASE)
    def test_heading(self): self.assertIn("## 1.0",compose(BASE))
    def test_category(self): self.assertIn("### Fixed",compose(BASE))
    def test_no_empty_sections(self): self.assertNotIn("### Added",compose(BASE))
    def test_breaking(self):
        d=self.data();d["changes"][0]["breaking"]=True
        self.assertIn("**BREAKING:**",compose(d))
    def test_order(self):
        d=self.data();d["changes"].append({"id":"b","category":"Added","summary":"Add export.","breaking":False})
        s=compose(d);self.assertLess(s.index("### Added"),s.index("### Fixed"))
    def test_escape(self):
        d=self.data();d["changes"][0]["summary"]="<script> *bold*"
        self.assertIn("\\<script\\>",compose(d))
    def test_invalid_date(self):
        d=self.data();d["date"]="2026-02-30"
        with self.assertRaises(ValueError): compose(d)
    def test_duplicate_id(self):
        d=self.data();d["changes"]*=2
        with self.assertRaises(ValueError): compose(d)
    def test_empty(self):
        d=self.data();d["changes"]=[]
        with self.assertRaises(ValueError): compose(d)
    def test_unknown(self):
        d=self.data();d["extra"]=1
        with self.assertRaises(ValueError): compose(d)
    def test_control(self):
        d=self.data();d["version"]="x\ny"
        with self.assertRaises(ValueError): compose(d)
    def test_duplicate_keys(self):
        with self.assertRaises(ValueError): pairs([("x",1),("x",2)])
if __name__=="__main__": unittest.main()
