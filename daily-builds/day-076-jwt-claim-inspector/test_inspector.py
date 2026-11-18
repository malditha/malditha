import base64
import json
import subprocess
import sys
import unittest
from pathlib import Path
from inspector import inspect


def enc(value):
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip('=')


def token(claims, header=None):
    return enc(json.dumps(header or {'alg': 'none'})) + '.' + enc(json.dumps(claims)) + '.'


class InspectorTests(unittest.TestCase):
    def test_claims_preserved_and_untrusted(self):
        r = inspect(token({'sub': 'demo', 'roles': ['reader']}), 100)
        self.assertEqual(r['claims']['roles'], ['reader'])
        self.assertIn('NOT VERIFIED', r['verification'])
    def test_exp_boundary(self):
        self.assertEqual(inspect(token({'exp': 100}), 100)['time_checks']['exp'], 'expired')
    def test_before_exp(self):
        self.assertEqual(inspect(token({'exp': 100.5}), 100)['time_checks']['exp'], 'not expired')
    def test_nbf_boundary(self):
        self.assertEqual(inspect(token({'nbf': 100}), 100)['time_checks']['nbf'], 'time reached')
    def test_before_nbf(self):
        self.assertEqual(inspect(token({'nbf': 101}), 100)['time_checks']['nbf'], 'not yet active')
    def test_future_iat(self):
        self.assertEqual(inspect(token({'iat': 101}), 100)['time_checks']['iat'], 'future issued-at')
    def test_missing(self):
        self.assertEqual(set(inspect(token({}), 0)['time_checks'].values()), {'absent'})
    def test_invalid_dates(self):
        for value in (True, None, '100', [], {}):
            self.assertEqual(inspect(token({'exp': value}), 0)['time_checks']['exp'], 'invalid NumericDate')
    def test_malformed(self):
        for value in ('a.b', 'a.b.c.d.e', '*.e30.', 'e30=.e30.', 'e31.e30.', 'e30.e30.*'):
            with self.assertRaises(ValueError): inspect(value, 0)
    def test_nonobjects(self):
        for h, c in (('[]', '{}'), ('{}', '[]')):
            with self.assertRaises(ValueError): inspect(enc(h)+'.'+enc(c)+'.', 0)
    def test_duplicate(self):
        with self.assertRaises(ValueError): inspect(enc('{}')+'.'+enc('{"exp":1,"exp":2}')+'.', 0)
    def test_nonfinite(self):
        with self.assertRaises(ValueError): inspect(enc('{}')+'.'+enc('{"exp":NaN}')+'.', 0)
    def test_clock_and_limit(self):
        for clock in (float('nan'), float('inf'), True):
            with self.assertRaises(ValueError): inspect(token({}), clock)
        with self.assertRaises(ValueError): inspect('x'*16385, 0)
    def test_signature_is_not_verified(self):
        r = inspect(token({}, {'alg':'HS256'}) + 'AA', 0)
        self.assertIn('NOT VERIFIED', r['verification'])
    def test_cli_sample(self):
        root = Path(__file__).parent
        r = subprocess.run([sys.executable, str(root/'inspector.py'), str(root/'sample.jwt'), '--now', '100'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['time_checks']['exp'], 'not expired')
    def test_cli_error_is_value_free(self):
        r = subprocess.run([sys.executable, str(Path(__file__).parent/'inspector.py'), '/nonexistent/private-name'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn('private-name', r.stderr)


if __name__ == '__main__': unittest.main()
