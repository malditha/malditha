import tempfile, unittest
from pathlib import Path
from error_message_reviewer import InputError, load_json, review_message, review_messages
class ReviewerTests(unittest.TestCase):
    def codes(self,text): return [f["code"] for f in review_message({"id":"x","text":text})["findings"]]
    def test_ready(self): self.assertEqual(review_message({"id":"x","text":"We couldn't save the draft. Try again."})["status"],"ready")
    def test_generic(self): self.assertIn("generic",self.codes("Something went wrong."))
    def test_action(self): self.assertIn("no_next_step",self.codes("The file is too large."))
    def test_technical(self): self.assertIn("technical_detail",self.codes("SQLSTATE exception. Contact support."))
    def test_blame(self): self.assertIn("blaming_tone",self.codes("You failed to enter a date. Try again."))
    def test_empty(self): self.assertEqual(self.codes(" ")[0],"empty")
    def test_long(self): self.assertIn("too_long",self.codes("a"*501))
    def test_summary(self): self.assertEqual(review_messages([{"id":"a","text":"Check the address and try again."},{"id":"b","text":"Error"}])["summary"],{"ready":1,"review":1})
    def test_duplicate_id(self):
        with self.assertRaises(InputError): review_messages([{"id":"a","text":"Try again"},{"id":"a","text":"Try again"}])
    def test_unknown_field(self):
        with self.assertRaises(InputError): review_message({"id":"a","text":"Try again","secret":"x"})
    def test_empty_collection(self):
        with self.assertRaises(InputError): review_messages([])
    def test_duplicate_key(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"in.json"; p.write_text('[{"id":"a","id":"b","text":"Try again"}]')
            with self.assertRaises(InputError): load_json(p)
if __name__=="__main__": unittest.main()
