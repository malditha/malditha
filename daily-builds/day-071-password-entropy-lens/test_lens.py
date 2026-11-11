import unittest
import subprocess
import sys
from pathlib import Path
from lens import estimate

class LensTests(unittest.TestCase):
    def test_binary(self):
        self.assertEqual(estimate(10, 2)['bits'], 10)
    def test_dice(self):
        self.assertEqual(estimate(5, 6)['bits'], 12.925)
    def test_words(self):
        self.assertEqual(estimate(6, 7776)['bits'], 77.549)
    def test_growth(self):
        self.assertGreater(estimate(13, 62)['bits'], estimate(12, 62)['bits'])
    def test_bounds(self):
        self.assertEqual(estimate(1000, 1000000)['bits'], 19931.569)
    def test_bad_lengths(self):
        for x in [0,-1,1001,True,1.5,'12',None]:
            with self.subTest(x=x), self.assertRaises(ValueError): estimate(x,26)
    def test_bad_pools(self):
        for x in [0,1,-1,1000001,True,2.5,'26',None]:
            with self.subTest(x=x), self.assertRaises(ValueError): estimate(12,x)
    def test_cli_comparison(self):
        r=subprocess.run([sys.executable,str(Path(__file__).with_name('lens.py')),'--length','10','--pool','2','--compare-length','12'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0)
        self.assertIn('"additional_bits": 2.0',r.stdout)
    def test_cli_invalid(self):
        r=subprocess.run([sys.executable,str(Path(__file__).with_name('lens.py')),'--length','0','--pool','2'],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertEqual(r.stdout,'')

if __name__=='__main__': unittest.main()
