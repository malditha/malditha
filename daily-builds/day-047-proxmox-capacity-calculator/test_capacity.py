import json
import subprocess
import sys
import unittest
from pathlib import Path
from capacity import calculate


def plan(**changes):
    args = dict(cores=8, ram_gib=32, disk_gib=500, guest_vcpus=2,
                guest_ram_gib=4, guest_disk_gib=40)
    args.update(changes)
    return calculate(**args)


class CapacityTests(unittest.TestCase):
    def test_cpu_limit(self):
        self.assertEqual(plan()["guest_count"], 4)
        self.assertEqual(plan()["limiting_resources"], ["cpu"])

    def test_ram_limit(self):
        self.assertEqual(plan(guest_ram_gib=16)["guest_count"], 1)

    def test_disk_limit(self):
        self.assertEqual(plan(guest_disk_gib=300)["guest_count"], 1)

    def test_allocation_ratio(self):
        self.assertEqual(plan(cpu_ratio=2)["guest_count"], 7)

    def test_tied_limits(self):
        self.assertEqual(plan(ram_gib=18)["limiting_resources"], ["cpu", "ram"])

    def test_zero_available_capacity(self):
        self.assertEqual(plan(reserve_ram_gib=32)["guest_count"], 0)

    def test_remaining_resources(self):
        self.assertEqual(plan()["remaining"], {"cpu": 0, "ram": 14, "disk": 320})

    def test_invalid_numbers(self):
        for n in [float("nan"), float("inf"), True, 0, -1]:
            with self.subTest(n=n), self.assertRaises(ValueError): plan(guest_ram_gib=n)

    def test_reserve_bounds(self):
        for n in [-1, 33]:
            with self.assertRaises(ValueError): plan(reserve_ram_gib=n)

    def test_integer_and_ratio_bounds(self):
        for args in [{"cores": 1.5}, {"guest_vcpus": 0}, {"cpu_ratio": .5}, {"cpu_ratio": 17}]:
            with self.assertRaises(ValueError): plan(**args)

    def test_cli_json(self):
        cmd = [sys.executable, "capacity.py", "--cores", "8", "--ram-gib", "32", "--disk-gib", "500", "--guest-vcpus", "2", "--guest-ram-gib", "4", "--guest-disk-gib", "40", "--json"]
        r = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["guest_count"], 4)


if __name__ == "__main__": unittest.main()
