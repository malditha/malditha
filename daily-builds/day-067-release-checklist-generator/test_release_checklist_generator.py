import tempfile,unittest
from pathlib import Path
from release_checklist_generator import InputError,generate_checklist,load,markdown

def profile(**updates):
    data={"release_id":"release-42","components":["application"],"risk":"low","customer_facing":False};data.update(updates);return data

class Tests(unittest.TestCase):
    def ids(self,**updates): return [x["id"] for x in generate_checklist(profile(**updates))["tasks"]]
    def test_base_tasks(self): self.assertEqual(generate_checklist(profile())["summary"]["tasks"],6)
    def test_database_tasks(self): self.assertTrue({"backup","migration","data-check"}<=set(self.ids(components=["database"])))
    def test_infrastructure_tasks(self): self.assertIn("capacity",self.ids(components=["infrastructure"]))
    def test_medium_rollback(self): self.assertIn("rollback",self.ids(risk="medium"))
    def test_high_approval(self): self.assertTrue({"approval","rehearsal"}<=set(self.ids(risk="high")))
    def test_customer_tasks(self): self.assertIn("message",self.ids(customer_facing=True))
    def test_component_order_stable(self): self.assertEqual(generate_checklist(profile(components=["database","application"]))["profile"]["components"],["application","database"])
    def test_phase_order(self):
        phases=[t["phase"] for t in generate_checklist(profile(risk="high"))["tasks"]]
        self.assertEqual(phases,sorted(phases,key={"before":0,"after":1}.get))
    def test_markdown(self): self.assertIn("## Before release",markdown(generate_checklist(profile())))
    def test_duplicate_components(self):
        with self.assertRaises(InputError): generate_checklist(profile(components=["application","application"]))
    def test_unknown_field(self):
        with self.assertRaises(InputError): generate_checklist({**profile(),"secret":"x"})
    def test_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"p.json";p.write_text('{"release_id":"a","release_id":"b"}')
            with self.assertRaises(InputError): load(p)
if __name__=="__main__": unittest.main()
