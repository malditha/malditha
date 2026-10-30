import json,tempfile,unittest
from pathlib import Path
from boundary_value_generator import SpecError,generate,load_json,main,report
class Tests(unittest.TestCase):
 def test_integer_minimum(self):
  c=generate({"fields":[{"name":"quantity","type":"integer","minimum":1}]});self.assertEqual([x.value for x in c],[0,1,2]);self.assertEqual([x.expected_valid for x in c],[False,True,True])
 def test_integer_maximum(self):
  c=generate({"fields":[{"name":"seats","type":"integer","maximum":5}]});self.assertEqual([x.expected_valid for x in c],[True,True,False])
 def test_number_step(self):
  c=generate({"fields":[{"name":"rate","type":"number","minimum":1.5,"step":0.25}]});self.assertEqual([x.value for x in c],[1.25,1.5,1.75])
 def test_string_minimum_zero_skips_impossible_below(self):
  c=generate({"fields":[{"name":"note","type":"string","min_length":0}]});self.assertEqual([x.relation for x in c],["at","above"])
 def test_string_maximum(self):
  c=generate({"fields":[{"name":"code","type":"string","max_length":2}]});self.assertEqual([len(x.value) for x in c],[1,2,3]);self.assertFalse(c[-1].expected_valid)
 def test_combined_limits_are_stable(self):
  c=generate({"fields":[{"name":"age","type":"integer","minimum":18,"maximum":65}]});self.assertEqual(len(c),6);self.assertEqual(c[3].boundary,"maximum")
 def test_duplicate_names_rejected(self):
  with self.assertRaises(SpecError): generate({"fields":[{"name":"x","type":"integer","minimum":0},{"name":"x","type":"integer","minimum":0}]})
 def test_inverted_range_rejected(self):
  with self.assertRaises(SpecError): generate({"fields":[{"name":"x","type":"number","minimum":2,"maximum":1}]})
 def test_mixed_constraints_rejected(self):
  with self.assertRaises(SpecError): generate({"fields":[{"name":"x","type":"string","minimum":1,"min_length":1}]})
 def test_duplicate_json_key_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_text('{"fields":[],"fields":[]}')
   with self.assertRaises(SpecError):load_json(p)
 def test_report_contains_no_source_metadata(self):
  r=report(generate({"fields":[{"name":"x","type":"integer","minimum":0}]}));self.assertEqual(set(r),{"case_count","cases"})
 def test_cli_writes_output(self):
  with tempfile.TemporaryDirectory() as d:
   i=Path(d)/"in.json";o=Path(d)/"out.json";i.write_text(json.dumps({"fields":[{"name":"x","type":"integer","maximum":2}]}));self.assertEqual(main([str(i),"-o",str(o)]),0);self.assertEqual(json.loads(o.read_text())["case_count"],3)
if __name__=="__main__":unittest.main()
