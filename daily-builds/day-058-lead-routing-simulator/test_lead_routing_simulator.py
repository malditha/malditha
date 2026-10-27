import json,tempfile,unittest
from pathlib import Path
from lead_routing_simulator import InputError,condition_matches,format_text,load,simulate,validate
def plan(routes=None,leads=None):
 return {"default_team":"general","routes":routes or [{"name":"apac","priority":10,"team":"regional","all":[{"field":"region","op":"equals","value":"APAC"}]}],"leads":leads or []}
class Tests(unittest.TestCase):
 def test_equals(self):self.assertTrue(condition_matches({"region":"APAC"},{"field":"region","op":"equals","value":"APAC"}))
 def test_one_of(self):self.assertTrue(condition_matches({"source":"event"},{"field":"source","op":"one_of","value":["event","referral"]}))
 def test_exists(self):self.assertFalse(condition_matches({"email":""},{"field":"email","op":"exists"}))
 def test_highest_priority_wins(self):
  routes=[{"name":"broad","priority":1,"team":"a","all":[{"field":"region","op":"equals","value":"APAC"}]},{"name":"specific","priority":20,"team":"b","all":[{"field":"segment","op":"equals","value":"enterprise"}]}]
  result=simulate(plan(routes,[{"id":"L1","attributes":{"region":"APAC","segment":"enterprise"}}]))
  self.assertEqual(result["results"][0]["route"],"specific");self.assertEqual(result["results"][0]["overlapping_routes"],["broad"])
 def test_source_order_breaks_priority_tie(self):
  routes=[{"name":"first","priority":5,"team":"a","all":[{"field":"x","op":"exists"}]},{"name":"second","priority":5,"team":"b","all":[{"field":"x","op":"exists"}]}]
  self.assertEqual(simulate(plan(routes,[{"id":"L","attributes":{"x":1}}]))["results"][0]["route"],"first")
 def test_default_route(self):self.assertEqual(simulate(plan(leads=[{"id":"L","attributes":{"region":"EU"}}]))["results"][0]["team"],"general")
 def test_values_not_in_report(self):
  report=simulate(plan(leads=[{"id":"lead-safe","attributes":{"region":"PRIVATE-VALUE"}}]));self.assertNotIn("PRIVATE-VALUE",json.dumps(report))
 def test_duplicate_route_name(self):
  route={"name":"same","priority":1,"team":"a","all":[{"field":"x","op":"exists"}]}
  with self.assertRaises(InputError):validate(plan([route,route]))
 def test_invalid_one_of(self):
  with self.assertRaises(InputError):validate(plan([{"name":"x","priority":1,"team":"a","all":[{"field":"x","op":"one_of","value":[]}]}]))
 def test_duplicate_json_key(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_text('{"routes":[],"routes":[]}',encoding="utf-8")
   with self.assertRaises(InputError):load(p)
 def test_text_output(self):self.assertIn("Assignments:\n- none",format_text(simulate(plan())))
if __name__=="__main__":unittest.main()
