import json
import socket
import unittest

from port_probe_report import as_json, as_text, parse_ports, probe_port, run_report


class FakeConnection:
    def __init__(self): self.closed = False
    def close(self): self.closed = True


class PortProbeReportTests(unittest.TestCase):
    def test_parse_ports_sorts_and_deduplicates(self):
        self.assertEqual(parse_ports("443,80,80,8000-8002"), (80, 443, 8000, 8001, 8002))

    def test_parse_ports_rejects_invalid_values(self):
        for value in ("", "0", "65536", "90-80", "abc", "80,,443", "1-101"):
            with self.subTest(value=value), self.assertRaises(ValueError): parse_ports(value)

    def test_open_port_records_latency_and_closes(self):
        connection = FakeConnection(); ticks = iter((10.0, 10.01234))
        result = probe_port("example.test", 443, 1, connector=lambda address, timeout: connection, clock=lambda: next(ticks))
        self.assertEqual((result.state, result.latency_ms, connection.closed), ("open", 12.34, True))

    def test_refused_connection_is_closed(self):
        def refused(address, timeout): raise ConnectionRefusedError
        self.assertEqual(probe_port("example.test", 81, 1, connector=refused).state, "closed")

    def test_socket_timeout_is_reported(self):
        def timed_out(address, timeout): raise socket.timeout
        self.assertEqual(probe_port("example.test", 82, 1, connector=timed_out).state, "timeout")

    def test_os_error_is_preserved_without_traceback(self):
        def failed(address, timeout): raise OSError("name lookup failed")
        result = probe_port("bad.test", 83, 1, connector=failed)
        self.assertEqual((result.state, result.error), ("error", "name lookup failed"))

    def test_report_preserves_requested_order(self):
        def refused(address, timeout): raise ConnectionRefusedError
        self.assertEqual([item.port for item in run_report("example.test", (22, 80), 1, connector=refused)], [22, 80])

    def test_text_and_json_outputs_are_consistent(self):
        def refused(address, timeout): raise ConnectionRefusedError
        results = run_report("example.test", (80,), 1, connector=refused)
        self.assertIn("1 closed", as_text("example.test", 1, results))
        self.assertEqual(json.loads(as_json("example.test", 1, results))["results"][0]["state"], "closed")


if __name__ == "__main__": unittest.main()
