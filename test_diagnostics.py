"""Tests for diagnostics with mocks. No internet access, no real scans."""

import socket
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import diagnostics
from diagnostics import check_ping, check_tcp_port, resolve_dns, run_all_diagnostics


class TestDNSResolution(unittest.TestCase):
    @patch("diagnostics.socket.gethostbyname", return_value="93.184.216.34")
    def test_dns_success(self, mock_lookup):
        result = resolve_dns("example.com")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["test"], "DNS")
        self.assertIn("93.184.216.34", result["details"])
        mock_lookup.assert_called_once_with("example.com")

    @patch("diagnostics.socket.gethostbyname", side_effect=socket.gaierror("nope"))
    def test_dns_failure(self, mock_lookup):
        result = resolve_dns("bad.invalid")
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["test"], "DNS")

    def test_ip_input_needs_no_lookup(self):
        with patch("diagnostics.socket.gethostbyname") as mock_lookup:
            result = resolve_dns("8.8.8.8")
            self.assertEqual(result["status"], "SUCCESS")
            self.assertIn("no dns lookup was needed", result["message"].lower())
            mock_lookup.assert_not_called()

    def test_empty_hostname_is_error(self):
        result = resolve_dns("")
        self.assertEqual(result["status"], "ERROR")


class TestPing(unittest.TestCase):
    @patch("diagnostics.shutil.which", return_value="/bin/ping")
    @patch("diagnostics.subprocess.run")
    def test_ping_success(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Reply from 8.8.8.8: bytes=32 time=12ms TTL=117",
            stderr="",
        )
        result = check_ping("8.8.8.8")
        self.assertEqual(result["status"], "SUCCESS")
        # Must never use shell=True.
        _, kwargs = mock_run.call_args
        self.assertFalse(kwargs.get("shell", False))

    @patch("diagnostics.shutil.which", return_value="/bin/ping")
    @patch("diagnostics.subprocess.run")
    def test_ping_failure_mentions_icmp(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="Request timed out.", stderr=""
        )
        result = check_ping("example.com")
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("ICMP", result["message"])

    @patch("diagnostics.shutil.which", return_value=None)
    def test_ping_missing_command(self, mock_which):
        result = check_ping("example.com")
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("not found", result["message"])

    @patch("diagnostics.shutil.which", return_value="/bin/ping")
    @patch("diagnostics.subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 15))
    def test_ping_timeout(self, mock_run, mock_which):
        result = check_ping("example.com")
        self.assertEqual(result["status"], "TIMEOUT")

    def test_ping_empty_input(self):
        result = check_ping("")
        self.assertEqual(result["status"], "ERROR")


class TestTCPConnectivity(unittest.TestCase):
    @patch("diagnostics.socket.create_connection")
    def test_tcp_success(self, mock_connect):
        mock_connect.return_value = MagicMock()
        mock_connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = check_tcp_port("example.com", 443)
        self.assertEqual(result["status"], "SUCCESS")

    @patch("diagnostics.socket.create_connection", side_effect=ConnectionRefusedError())
    def test_tcp_refused(self, mock_connect):
        result = check_tcp_port("example.com", 443)
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("refused", result["message"].lower())

    @patch("diagnostics.socket.create_connection", side_effect=socket.timeout())
    def test_tcp_timeout(self, mock_connect):
        result = check_tcp_port("example.com", 443)
        self.assertEqual(result["status"], "TIMEOUT")

    @patch("diagnostics.socket.create_connection", side_effect=socket.gaierror("dns fail"))
    def test_tcp_dns_failure(self, mock_connect):
        result = check_tcp_port("bad.invalid", 443)
        self.assertEqual(result["status"], "FAILED")

    def test_tcp_invalid_port(self):
        result = check_tcp_port("example.com", 0)
        self.assertEqual(result["status"], "ERROR")
        result = check_tcp_port("example.com", 70000)
        self.assertEqual(result["status"], "ERROR")


class TestRunAllDiagnostics(unittest.TestCase):
    @patch("diagnostics.check_tcp_port")
    @patch("diagnostics.check_ping")
    @patch("diagnostics.resolve_dns")
    def test_run_all_calls_each_check(self, mock_dns, mock_ping, mock_tcp):
        mock_dns.return_value = {
            "timestamp": "t", "target": "example.com", "test": "DNS",
            "status": "SUCCESS", "message": "ok", "details": "",
        }
        mock_ping.return_value = {
            "timestamp": "t", "target": "example.com", "test": "PING",
            "status": "SUCCESS", "message": "ok", "details": "",
        }
        mock_tcp.return_value = {
            "timestamp": "t", "target": "example.com", "test": "TCP",
            "status": "SUCCESS", "message": "ok", "details": "",
        }
        results = run_all_diagnostics("example.com", 443)
        mock_dns.assert_called_once()
        mock_ping.assert_called_once()
        mock_tcp.assert_called_once()
        tests = [r["test"] for r in results]
        self.assertIn("DNS", tests)
        self.assertIn("PING", tests)
        self.assertIn("TCP", tests)
        for row in results:
            for key in ("timestamp", "target", "test", "status", "message", "details"):
                self.assertIn(key, row)

    def test_run_all_rejects_empty_host(self):
        results = run_all_diagnostics("", 443)
        self.assertEqual(results[0]["status"], "ERROR")

    def test_run_all_rejects_bad_port(self):
        results = run_all_diagnostics("example.com", 0)
        self.assertEqual(results[0]["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
