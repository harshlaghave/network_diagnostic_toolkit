"""Input validation helpers for the diagnostics toolkit.

This module checks hostnames, IP addresses and TCP port numbers
before any network test runs, so bad input becomes a friendly
error message instead of a crash.
"""

import ipaddress
import re


# A hostname label is 1-63 chars: letters, digits, hyphens,
# but it may not start or end with a hyphen.
_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def is_valid_ip(value: str) -> bool:
    """Return True if *value* is a valid IPv4 or IPv6 address."""
    if not isinstance(value, str):
        return False
    value = value.strip()
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_hostname(value: str) -> bool:
    """Return True if *value* looks like a valid DNS hostname.

    IP addresses are NOT hostnames, so this returns False for them.
    A trailing dot (fully-qualified form like "example.com.") is allowed.
    """
    if not isinstance(value, str):
        return False
    hostname = value.strip().rstrip(".")
    if not hostname or len(hostname) > 253:
        return False
    if is_valid_ip(hostname):
        return False
    # Reject spaces, underscores, slashes and other illegal characters early.
    if any(ch.isspace() for ch in hostname):
        return False
    labels = hostname.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not _LABEL_PATTERN.match(label):
            return False
    return True


def is_valid_host(value: str) -> bool:
    """Return True if *value* is a valid hostname or IP address."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    return is_valid_ip(text) or is_valid_hostname(text)


def validate_host(host: str) -> str:
    """Validate *host* and return its cleaned form.

    Raises:
        ValueError: with a beginner-friendly message when invalid.
    """
    if not isinstance(host, str):
        raise ValueError("Host must be text, for example 'example.com'.")
    cleaned = host.strip()
    if not cleaned:
        raise ValueError("Host must not be empty. Try 'example.com' or '8.8.8.8'.")
    if is_valid_ip(cleaned) or is_valid_hostname(cleaned):
        return cleaned
    raise ValueError(
        f"'{cleaned}' is not a valid hostname or IP address. "
        "Use something like 'example.com' or '8.8.8.8'."
    )


def is_valid_port(value) -> bool:
    """Return True if *value* is a TCP port in the range 1-65535."""
    try:
        number = int(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return False
    return 1 <= number <= 65535


def validate_port(value) -> int:
    """Validate *value* as a TCP port and return it as an int.

    Raises:
        ValueError: with a beginner-friendly message when invalid.
    """
    try:
        number = int(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        raise ValueError(
            f"Port '{value}' is not a number. Enter a number from 1 to 65535."
        )
    if 1 <= number <= 65535:
        return number
    raise ValueError(f"Port {number} is out of range. Enter a number from 1 to 65535.")
