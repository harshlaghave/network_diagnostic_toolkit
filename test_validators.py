"""Tests for host and port validation. No internet access is used."""

import unittest

from validators import (
    is_valid_host,
    is_valid_hostname,
    is_valid_ip,
    is_valid_port,
    validate_host,
    validate_port,
)


class TestIPAddressValidation(unittest.TestCase):
    def test_valid_ipv4_addresses(self):
        for address in ["8.8.8.8", "127.0.0.1", "192.168.1.1", "255.255.255.255"]:
            with self.subTest(address=address):
                self.assertTrue(is_valid_ip(address))

    def test_valid_ipv6_addresses(self):
        for address in ["::1", "2001:db8::1", "fe80::1", "::ffff:192.0.2.1"]:
            with self.subTest(address=address):
                self.assertTrue(is_valid_ip(address))

    def test_invalid_ip_addresses(self):
        for address in ["999.999.999.999", "256.1.1.1", "abc", "12345", "1.2.3.4.5", ""]:
            with self.subTest(address=address):
                self.assertFalse(is_valid_ip(address))


class TestHostnameValidation(unittest.TestCase):
    def test_empty_hostname_is_invalid(self):
        self.assertFalse(is_valid_host(""))
        self.assertFalse(is_valid_host("   "))
        with self.assertRaises(ValueError):
            validate_host("")
        with self.assertRaises(ValueError):
            validate_host("   ")

    def test_valid_hostnames(self):
        for name in ["example.com", "localhost", "my-host123.example.org", "a.b"]:
            with self.subTest(name=name):
                self.assertTrue(is_valid_hostname(name))
                self.assertTrue(is_valid_host(name))
                self.assertEqual(validate_host(name), name)

    def test_valid_host_accepts_ips(self):
        self.assertTrue(is_valid_host("8.8.8.8"))
        self.assertTrue(is_valid_host("::1"))

    def test_invalid_hostnames(self):
        for name in ["-bad.com", "bad-.com", "bad_host.com", "exa mple.com", "http://x.com"]:
            with self.subTest(name=name):
                self.assertFalse(is_valid_hostname(name))


class TestPortValidation(unittest.TestCase):
    def test_valid_tcp_ports(self):
        for port in [1, 80, 443, 8080, 65535, "22", " 443 "]:
            with self.subTest(port=port):
                self.assertTrue(is_valid_port(port))
                parsed = validate_port(port)
                self.assertTrue(1 <= parsed <= 65535)

    def test_invalid_tcp_ports(self):
        for port in [0, -1, -443, 65536, 100000, "abc", "", None, "80.5", "port"]:
            with self.subTest(port=port):
                self.assertFalse(is_valid_port(port))
                with self.assertRaises(ValueError):
                    validate_port(port)


if __name__ == "__main__":
    unittest.main()
