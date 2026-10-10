"""Real network diagnostic functions using the standard library.

Each check returns a plain dictionary with the same shape so the
menu code and the CSV exporter can handle every result uniformly:

    {
        "timestamp": "2026-01-01T10:00:00",
        "target": "example.com",
        "test": "DNS",
        "status": "SUCCESS" | "FAILED" | "TIMEOUT" | "ERROR",
        "message": "Short human-readable explanation.",
        "details": "Extra info such as an IP address or timings.",
    }

Nothing here invents results. Every status reflects what the
operating system or Python's networking libraries actually reported.
"""

import datetime
import ipaddress
import platform
import shutil
import socket
import subprocess
import sys

from validators import is_valid_ip, validate_host, validate_port

# Small, fixed ping packet count so we never flood a host.
PING_COUNT = 4
# Upper bound for the whole ping subprocess call.
PING_SUBPROCESS_TIMEOUT = 15
# Default TCP connect timeout in seconds.
TCP_TIMEOUT = 3.0


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string (no microseconds)."""
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _make_result(target: str, test: str, status: str, message: str, details: str = "") -> dict:
    """Build one standardised result dictionary."""
    return {
        "timestamp": _utc_now(),
        "target": target,
        "test": test,
        "status": status,
        "message": message,
        "details": details,
    }


def resolve_dns(hostname: str) -> dict:
    """Resolve *hostname* to an IP address with the socket module.

    An input that is already an IP address needs no lookup: it is
    reported as SUCCESS with a note that no resolution was required.
    """
    raw = (hostname or "").strip()
    if not raw:
        return _make_result(
            raw or "(empty)",
            "DNS",
            "ERROR",
            "Empty hostname. Enter something like 'example.com' or '8.8.8.8'.",
        )

    # An IP literal does not need DNS resolution at all.
    try:
        ipaddress.ip_address(raw)
        return _make_result(
            raw,
            "DNS",
            "SUCCESS",
            "Input is already an IP address; no DNS lookup was needed.",
            raw,
        )
    except ValueError:
        pass  # Not an IP address, so continue to real DNS resolution.

    try:
        cleaned = validate_host(raw)
    except ValueError as exc:
        return _make_result(raw, "DNS", "ERROR", str(exc))

    try:
        resolved = socket.gethostbyname(cleaned)
        return _make_result(
            cleaned,
            "DNS",
            "SUCCESS",
            f"'{cleaned}' resolved to {resolved}.",
            resolved,
        )
    except socket.gaierror:
        return _make_result(
            cleaned,
            "DNS",
            "FAILED",
            f"Could not resolve '{cleaned}'. Check the spelling and DNS settings.",
        )
    except (OSError, UnicodeError) as exc:
        return _make_result(
            cleaned,
            "DNS",
            "ERROR",
            f"DNS lookup for '{cleaned}' hit an unexpected error: {exc}.",
        )


def _build_ping_command(host: str) -> list:
    """Return the OS-appropriate ping command (never uses shell=True)."""
    system = platform.system().lower()
    if system == "windows":
        # -n count, -w timeout per reply in milliseconds.
        return ["ping", "-n", str(PING_COUNT), "-w", "1000", host]
    # Linux and macOS: -c count, -W timeout. macOS treats -W
    # slightly differently but still accepts it; keep values small.
    if system == "darwin":
        return ["ping", "-c", str(PING_COUNT), "-W", "2000", host]
    return ["ping", "-c", str(PING_COUNT), "-W", "2", host]


def _parse_ping_details(output: str) -> str:
    """Pull packet-loss / timing hints out of ping output (best effort).

    Ping output differs between Windows, Linux and macOS, so we look
    for several common patterns and return whatever we find. If none
    match, an empty string is returned instead of guessing.
    """
    import re

    if not output:
        return ""
    details: list = []
    loss_match = re.search(r"(\d+\s?%[^,\n]*loss)", output, re.IGNORECASE)
    if loss_match:
        details.append(loss_match.group(1).strip())
    # Linux/macOS style: "time=12.3 ms".
    times = re.findall(r"time[=<]\s*([\d.]+)\s*ms", output, re.IGNORECASE)
    if times:
        try:
            numbers = [float(t) for t in times]
            details.append(
                f"replies={len(numbers)} min={min(numbers):.1f}ms "
                f"avg={sum(numbers) / len(numbers):.1f}ms max={max(numbers):.1f}ms"
            )
        except ValueError:
            details.append(f"replies={len(times)}")
    else:
        # Windows style: "Average = 12ms".
        avg_match = re.search(r"Average\s*=\s*(\d+\s*ms)", output, re.IGNORECASE)
        if avg_match:
            details.append("Average=" + avg_match.group(1).strip())
    return "; ".join(details)


def check_ping(host: str) -> dict:
    """Ping *host* once using the operating system's ping command."""
    raw = (host or "").strip()
    if not raw:
        return _make_result(
            raw or "(empty)", "PING", "ERROR", "Empty host. Enter a hostname or IP address."
        )
    try:
        target = validate_host(raw)
    except ValueError as exc:
        return _make_result(raw, "PING", "ERROR", str(exc))

    if shutil.which("ping") is None:
        return _make_result(
            target,
            "PING",
            "ERROR",
            "The 'ping' command was not found on this computer, so no test ran.",
        )

    command = _build_ping_command(target)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PING_SUBPROCESS_TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        return _make_result(
            target,
            "PING",
            "ERROR",
            "The 'ping' command could not be started on this computer.",
        )
    except subprocess.TimeoutExpired:
        return _make_result(
            target,
            "PING",
            "TIMEOUT",
            f"No ping reply within {PING_SUBPROCESS_TIMEOUT} seconds. "
            "The host may be slow, offline, or blocking ICMP traffic.",
        )
    except PermissionError as exc:
        return _make_result(
            target, "PING", "ERROR", f"Permission problem while running ping: {exc}."
        )
    except OSError as exc:
        return _make_result(
            target, "PING", "ERROR", f"Could not run ping: {exc}."
        )

    output = (completed.stdout or "") + (completed.stderr or "")
    details = _parse_ping_details(output)
    if completed.returncode == 0:
        return _make_result(
            target,
            "PING",
            "SUCCESS",
            f"Received a ping response from {target}.",
            details or "Ping exited with status 0 (success).",
        )
    return _make_result(
        target,
        "PING",
        "FAILED",
        f"No ping response from {target}. This does NOT prove the host is offline: "
        "many firewalls block ICMP ping traffic.",
        details or output.strip()[:300],
    )


def check_tcp_port(host: str, port: int = 443) -> dict:
    """Try a TCP connection to *host*:*port* with a short timeout."""
    raw_host = (host or "").strip() if isinstance(host, str) else ""
    if not raw_host:
        return _make_result(
            raw_host or "(empty)",
            "TCP",
            "ERROR",
            "Empty host. Enter a hostname or IP address.",
        )
    try:
        target = validate_host(raw_host)
    except ValueError as exc:
        return _make_result(raw_host, "TCP", "ERROR", str(exc))
    try:
        port_number = validate_port(port)
    except ValueError as exc:
        return _make_result(target, "TCP", "ERROR", str(exc))

    try:
        # The context manager reliably closes the socket for us.
        with socket.create_connection((target, port_number), timeout=TCP_TIMEOUT):
            pass
        return _make_result(
            target,
            "TCP",
            "SUCCESS",
            f"TCP port {port_number} on {target} accepted a connection.",
            f"port={port_number}",
        )
    except socket.gaierror:
        return _make_result(
            target,
            "TCP",
            "FAILED",
            f"Could not resolve '{target}', so the TCP test could not run.",
            f"port={port_number}",
        )
    except socket.timeout:
        return _make_result(
            target,
            "TCP",
            "TIMEOUT",
            f"TCP connection to {target}:{port_number} timed out after "
            f"{TCP_TIMEOUT:g} seconds. The port may be filtered or the host slow. "
            "This does not necessarily mean the whole host is offline.",
            f"port={port_number}",
        )
    except ConnectionRefusedError:
        return _make_result(
            target,
            "TCP",
            "FAILED",
            f"TCP port {port_number} on {target} refused the connection. "
            "The host is reachable but nothing is accepting connections there; "
            "this does not mean the entire host is offline.",
            f"port={port_number}",
        )
    except OSError as exc:
        return _make_result(
            target,
            "TCP",
            "FAILED",
            f"TCP connection to {target}:{port_number} failed ({exc}). "
            "This does not necessarily mean the entire host is offline.",
            f"port={port_number}",
        )


def get_local_network_info() -> dict:
    """Collect basic local hostname / OS / Python information.

    Returns a dictionary (not a result list) because this is
    informational rather than a pass/fail test against a target.
    """
    hostname = socket.gethostname()
    local_ip = ""
    note = ""
    try:
        # Opens a UDP socket but sends nothing; the OS then tells us
        # which local address it would use. No internet needed.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            note = "Detected local IPv4 address (not necessarily the public IP)."
    except OSError:
        local_ip = ""
        note = "Could not determine a reliable local IP on this network."
    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "local_ip_note": note,
        "os": f"{platform.system()} {platform.release()} ({platform.platform()})",
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
    }


def run_all_diagnostics(host: str, port: int = 443) -> list:
    """Run DNS + ping + TCP checks for *host* and return the result list."""
    raw = (host or "").strip() if isinstance(host, str) else ""
    if not raw:
        return [
            _make_result(
                raw or "(empty)",
                "VALIDATION",
                "ERROR",
                "Empty host. Enter a hostname or IP address.",
            )
        ]
    try:
        target = validate_host(raw)
    except ValueError as exc:
        return [_make_result(raw, "VALIDATION", "ERROR", str(exc))]
    try:
        port_number = validate_port(port)
    except ValueError as exc:
        return [_make_result(target, "VALIDATION", "ERROR", str(exc))]

    results = []
    started = _utc_now()
    results.append(
        {
            "timestamp": started,
            "target": target,
            "test": "INFO",
            "status": "SUCCESS",
            "message": f"Starting diagnostics for {target} on TCP port {port_number}.",
            "details": f"port={port_number}",
        }
    )
    # Only report an IP-input hint if the input really is an IP literal.
    dns_result = resolve_dns(target)
    results.append(dns_result)
    results.append(check_ping(target))
    results.append(check_tcp_port(target, port_number))
    return results
