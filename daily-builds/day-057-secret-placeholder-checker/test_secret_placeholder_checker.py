import json,tempfile,unittest
from pathlib import Path
from secret_placeholder_checker import InputError,classify,format_text,load,scan
class Tests(unittest.TestCase):
 def test_known_placeholder(self):self.assertEqual(classify("CHANGE_ME"),"known_placeholder")
 def test_template_placeholder(self):self.assertEqual(classify("YOUR_API_KEY_HERE"),"template_placeholder")
 def test_bracket_only_for_sensitive_key(self):self.assertEqual(classify("$"+"{API_KEY}","api_key"),"credential_template")
 def test_normal_template_is_not_flagged(self):self.assertIsNone(classify("$"+"{customer_name}","message"))
 def test_empty_sensitive_field(self):self.assertEqual(classify("","password"),"empty_credential_field")
 def test_nested_paths_without_values(self):
  r=scan({"nodes":[{"credentials":{"token":"CHANGE_ME"}}]})
  self.assertEqual(r["findings"],[{"path":"$.nodes[0].credentials.token","code":"known_placeholder"}])
  self.assertNotIn("CHANGE_ME",json.dumps(r))
 def test_clear_document(self):self.assertEqual(scan({"message":"hello"})["status"],"clear")
 def test_duplicate_keys(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_text('{"a":1,"a":2}',encoding="utf-8")
   with self.assertRaises(InputError):load(p)
 def test_depth_limit(self):
  value={};cursor=value
  for _ in range(22):cursor["next"]={};cursor=cursor["next"]
  with self.assertRaises(InputError):scan(value)
 def test_text_report(self):self.assertIn("Findings:\n- none",format_text(scan({"ok":True})))
if __name__=="__main__":unittest.main()
