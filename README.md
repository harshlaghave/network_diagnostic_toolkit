# Network Connectivity & Diagnostics Toolkit

A beginner-friendly Python command-line application that performs basic network
diagnostics on a computer or a network host and produces a readable report.

## Overview

This toolkit checks **DNS resolution**, **ping reachability (ICMP)**,
**TCP port connectivity**, and **local system/network information** using real
results from the operating system and Python's standard networking libraries.
It never fabricates successful results: every status reflects what actually
happened.

It is aimed at a final-year Computer Engineering student preparing for a
Graduate Engineer Trainee — Telecom Network Analyst Engineer role. The code is
deliberately small, modular, and readable line by line.

> This tool performs **basic diagnostics only**. It is not a full telecom
> network monitoring platform.

## Problem Statement

When a website or service does not load, beginners often cannot tell whether
the problem is a mistyped hostname, broken DNS, blocked ping traffic, a closed
TCP port, or their own local machine setup. This project gives them one simple
menu-driven tool that runs each of those checks separately, explains the
outcome in plain language, and saves the evidence to a CSV report.

## Objectives

- Run real DNS, ping, and TCP diagnostics from one menu.
- Teach basic networking concepts through readable code.
- Handle invalid input and network failures gracefully.
- Export actual test results to a timestamped CSV file.
- Verify behaviour with mocked unit tests that need no internet.
- Stay within the Python standard library with no extra dependencies.

## Features

1. **Main menu (looping CLI)** — run all diagnostics, DNS only, ping only,
   TCP only, local info, CSV export, or exit. Invalid choices are rejected
   without crashing.
2. **DNS resolution** — `resolve_dns(hostname)` uses `socket.gethostbyname`.
   IP-address input is accepted without a lookup and reported honestly.
3. **Ping / reachability** — `check_ping(host)` runs the OS `ping` command via
   `subprocess` (no `shell=True`), with a small fixed packet count (4) and a
   15-second subprocess timeout. Packet-loss / timing hints are extracted with
   format-tolerant parsing.
4. **TCP port connectivity** — `check_tcp_port(host, port)` uses
   `socket.create_connection` with a 3-second timeout inside a context manager.
   Default port is 443; any port 1–65535 can be entered. No port-range scanning.
5. **Local network information** — `get_local_network_info()` shows hostname,
   detected local IPv4 address (labelled as local, not public), OS, and Python
   version. No external website is contacted and no personal data is collected.
6. **Run all diagnostics** — `run_all_diagnostics(host, port)` records a start
   timestamp, validates input, runs DNS + ping + TCP, and keeps the results in
   memory for export.
7. **CSV report export** — `export_report_to_csv(results)` writes real results
   with headers to `reports/network_report_YYYYMMDD_HHMMSS.csv` (UTF-8,
   auto-created directory, never overwrites by appending `_1`, `_2`, …).
8. **Input validation** — `validators.py` uses the `ipaddress` module plus
   hostname rules; empty hosts and out-of-range ports are rejected with
   beginner-friendly messages.

## Technologies Used

- **Language:** Python 3 (tested on 3.13; any Python 3.8+ should work)
- **Standard-library modules only:**
  `socket`, `subprocess`, `platform`, `sys`, `csv`, `datetime`, `pathlib`,
  `ipaddress`, `unittest`, `re`, `shutil`
- No third-party packages, no web framework, no database.

## Project Structure

```text
network-connectivity-diagnostics/
├── main.py                  # Menu, input prompts, program entry point
├── diagnostics.py           # DNS, ping, TCP, local info, run-all logic
├── report_generator.py      # CSV export functionality
├── validators.py            # Hostname / IP / port validation
├── tests/
│   ├── __init__.py
│   ├── test_validators.py
│   ├── test_report_generator.py
│   └── test_diagnostics.py
├── reports/
│   └── .gitkeep             # Keeps the folder tracked; *.csv files are ignored
├── .gitignore
├── README.md
├── requirements.txt         # States standard-library-only (no dependencies)
└── LICENSE                  # MIT License
```

## Prerequisites

- Python 3.8 or newer.
- A `ping` command on your system PATH (preinstalled on Windows, Linux, macOS).
- Permission to diagnose only hosts you own or are allowed to test.

Check Python:

```powershell
python --version
```

```bash
python3 --version
```

## Installation and Setup on Windows

Using Windows PowerShell:

```powershell
# 1. Clone the repository (or download and open the folder)
git clone https://github.com/harshlaghave/network-connectivity-diagnostics.git
cd network-connectivity-diagnostics

# 2. (Optional but recommended) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. No packages to install (standard library only)
# If a requirements file gains dependencies later:
# pip install -r requirements.txt

# 4. Run the test suite
python -m unittest discover -s tests -v
```

If script activation is blocked, see `Set-ExecutionPolicy` help, or simply
skip the virtual environment — the project runs fine on the system Python.

## Installation and Setup on Linux/macOS

```bash
# 1. Clone the repository (or download and open the folder)
git clone https://github.com/harshlaghave/network-connectivity-diagnostics.git
cd network-connectivity-diagnostics

# 2. (Optional but recommended) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. No packages to install (standard library only)

# 4. Run the test suite
python3 -m unittest discover -s tests -v
```

## How to Run the Project

Windows (PowerShell):

```powershell
python main.py
```

Linux/macOS:

```bash
python3 main.py
```

You will see:

```text
=== Network Connectivity & Diagnostics Toolkit ===
1. Run all diagnostics for a host
2. Check DNS resolution
3. Check network reachability using ping
4. Check TCP port connectivity
5. View local network information
6. Export the latest diagnostic report to CSV
7. Exit
```

The program needs no internet connection just to start. Diagnostics that
contact a host will naturally report failures when offline.

## Example Usage

```text
Select an option (1-7): 1
Enter hostname or IP address: example.com
Enter TCP port [default 443]: 443
Only test systems you own or have permission to diagnose.

[SUCCESS] INFO -> example.com
  Starting diagnostics for example.com on TCP port 443.
[SUCCESS] DNS -> example.com
  'example.com' resolved to 93.184.216.34.
  Details: 93.184.216.34
[FAILED] PING -> example.com
  No ping response from example.com. This does NOT prove the host is offline:
  many firewalls block ICMP ping traffic.
[SUCCESS] TCP -> example.com
  TCP port 443 on example.com accepted a connection.
  Details: port=443

--- Summary ---
INFO       SUCCESS  Starting diagnostics for example.com on TCP port 443.
DNS        SUCCESS  'example.com' resolved to 93.184.216.34.
PING       FAILED   No ping response ... firewalls block ICMP ping traffic.
TCP        SUCCESS  TCP port 443 on example.com accepted a connection.
----------------
```

(Addresses and outcomes above are illustrative of the format; your real output
depends on your network. The program reports what actually happens.)

Exporting (menu option 6) after a run:

```text
Report saved to reports\network_report_20260115_103000.csv
```

## Example CSV Report Format

Headers:

```csv
timestamp,target,test,status,message,details
```

Example rows (from real runs, not hardcoded):

```csv
timestamp,target,test,status,message,details
2026-01-15T10:30:00+00:00,example.com,INFO,SUCCESS,Starting diagnostics for example.com on TCP port 443.,port=443
2026-01-15T10:30:01+00:00,example.com,DNS,SUCCESS,'example.com' resolved to 93.184.216.34.,93.184.216.34
2026-01-15T10:30:05+00:00,example.com,PING,FAILED,"No ping response from example.com. This does NOT prove the host is offline: many firewalls block ICMP ping traffic.",0% loss
2026-01-15T10:30:06+00:00,example.com,TCP,SUCCESS,TCP port 443 on example.com accepted a connection.,port=443
```

Possible `status` values: `SUCCESS`, `FAILED`, `TIMEOUT`, `ERROR`.

## Explanation of DNS, Ping/ICMP and TCP Ports

- **DNS (Domain Name System):** the internet's phone book. It translates a
  human name like `example.com` into an IP address like `93.184.216.34` so
  your computer knows where to connect. This tool uses `socket.gethostbyname`.
  Note: your computer or router may cache answers, so repeated lookups can
  return a stored result. Entering an IP address directly skips DNS entirely.
- **Ping / ICMP:** `ping` sends small ICMP Echo Request packets and waits for
  Echo Replies. It answers "can packets make a round trip?" — not "is the
  website working?" Ping results depend on ICMP support and firewall rules:
  many servers deliberately block ping while serving web traffic normally, so
  a failed ping never proves a host is offline.
- **TCP ports:** a TCP connection is a two-way channel to one numbered "door"
  (port) on a host. Port 443 is the default for HTTPS, 80 for HTTP, 22 for SSH.
  A successful TCP connection means something accepted the connection on that
  port — but it does **not** prove the application behind it is healthy,
  correct, or secure. A refused connection means the host was reachable but
  nothing accepted on that port; a timeout often means a firewall silently
  dropped the attempt. Either way, it says nothing definitive about the whole
  host.

## How the Program Handles Errors

- Empty hostnames and ports outside 1–65535 are rejected before any network
  call, with plain-language guidance.
- DNS failures (`socket.gaierror`) become a `FAILED` result, not a crash.
- Missing `ping` binary, permission errors, and subprocess timeouts become
  `ERROR` / `TIMEOUT` results with explanations.
- TCP refused connections, timeouts, DNS failures, and other `OSError`s become
  `FAILED` / `TIMEOUT` results that stress a single failed test does not mean
  the whole host is down.
- File-writing problems during CSV export print a short message and return an
  empty string instead of raising.
- Ordinary users never see raw tracebacks; unexpected input cannot crash the
  menu loop.
- Network failures are treated as normal diagnostic outcomes, and not every
  exception is reported as "network unavailable".

## Limitations

- Basic diagnostics only — not a full telecom network monitoring platform.
- Ping depends on ICMP being allowed; blocked ICMP looks like failure.
- DNS may return cached results from the OS or local resolver.
- A successful TCP connection does not prove the application is healthy or
  secure.
- No public-IP discovery (by design — no external websites are contacted).
- Local IP detection can fail on machines without a normal IPv4 route; the
  tool then reports "unavailable" honestly.
- Single-port checks only; there is deliberately no port-range scanning,
  packet sniffing, or vulnerability scanning.
- Reports are local CSV files; there is no database, dashboard, or alerting.

## Testing Instructions

Tests use `unittest` with mocks, so they need **no internet access** and never
scan external hosts. File-writing tests use temporary directories.

```powershell
python -m unittest discover -s tests -v
```

```bash
python3 -m unittest discover -s tests -v
```

What is covered (31 tests):

- Valid IPv4 and IPv6 addresses; invalid IP addresses.
- Empty hostname rejection; valid and invalid hostnames.
- Valid ports (1, 80, 443, 8080, 65535) and invalid ports
  (0, negatives, > 65535, non-numeric).
- CSV export with sample data; header and row-count checks; empty-results
  handling; non-overwriting filenames; default timestamped filename pattern.
- DNS success and failure via mocked `socket.gethostbyname`; IP-input shortcut.
- TCP success, refusal, timeout, and DNS-failure via mocked
  `socket.create_connection`; invalid-port handling.
- Ping success and failure via mocked `subprocess.run` (including the ICMP
  disclaimer), missing-command and timeout handling.

## Future Improvements

- Optional reverse-DNS display alongside forward resolution.
- Configurable ping count / timeout flags while keeping safe defaults.
- JSON report export next to CSV.
- Traceroute-style hop display (platform-dependent, clearly labelled).
- Colourised terminal output with a `--no-color` fallback.
- Clearer per-OS guidance when `ping` is missing or restricted.

## Learning Outcomes

- Using `socket` for DNS lookups and TCP connections with timeouts.
- Running OS commands safely with `subprocess` (argument lists, no
  `shell=True`, capturing output, enforcing timeouts).
- Validating hostnames and IP addresses with `ipaddress` and careful rules.
- Designing uniform result dictionaries that feed both terminal output and CSV.
- Writing CSV files with the `csv` module (UTF-8, headers, safe filenames).
- Mocking DNS, subprocess, and sockets so tests run offline.
- Structuring a small Python project (`main.py` UI vs. logic modules,
  `main()` + `if __name__ == "__main__"` entry point, type hints, docstrings).

## How to Explain This Project in an Interview

**What the project does:** It is a menu-driven command-line tool. You type a
hostname or IP, and it runs three real checks — DNS lookup, OS ping, and a TCP
connection to one port — then prints a summary and optionally saves the real
results to a timestamped CSV file. It also shows your own hostname, local IP,
OS, and Python version.

**Why it is useful:** When something does not load, it separates the layers:
"did the name resolve?", "did echo packets return?", "did this specific port
accept a connection?" Each answer narrows down the fault instead of guessing.

**What DNS does:** DNS maps names to IP addresses. Entering `example.com`
asks your configured resolver for its address; entering `8.8.8.8` skips DNS
because you already have the address.

**What ping checks and what ICMP means:** Ping sends ICMP Echo Requests and
waits for Echo Replies, measuring round-trip reachability. ICMP is the
control-message protocol ping uses — distinct from TCP/UDP application traffic.

**What a TCP port is:** An endpoint number for a service on a host
(e.g. 443 for HTTPS). Connecting to it tests whether something there accepts
TCP connections.

**Why a successful ping and a successful TCP connection are different:** Ping
tests ICMP echo at the network layer; TCP tests one application port. A host
can block ping yet serve HTTPS, or answer ping while its web port is closed.

**Why a firewall can block ping:** Administrators often drop ICMP to reduce
noise and probing while still allowing TCP services. The tool's failure message
says exactly this so users do not misread a blocked ping as "host is down".

**Why socket timeouts are needed:** Without a timeout, a connection to a
filtered port or dead host could hang for minutes. A 3-second TCP timeout and
a 15-second ping-process cap keep the tool responsive.

**Why exceptions must be handled:** DNS failures, refused connections,
timeouts, missing binaries, and bad input are *expected* in networking. Each
maps to a `FAILED` / `TIMEOUT` / `ERROR` result with a beginner-friendly
message instead of a traceback.

**How CSV reports are generated:** `report_generator.py` takes the in-memory
result list, creates `reports/` if needed, picks a timestamped filename that
does not overwrite existing files, and writes the rows with `csv.DictWriter`
in UTF-8.

**How unit tests and mocks work:** Tests replace real network calls with fakes:
a fake `gethostbyname` for DNS, a fake `subprocess.run` for ping, a fake
`create_connection` for TCP. That way success, failure, timeout, and
missing-command paths are tested offline without touching real hosts.
File tests write to temporary directories. Mocked data never leaks into the
real application.

**What the limitations are:** Basic checks only; ping needs ICMP allowed; DNS
may be cached; TCP success does not mean the app is healthy; single-port
checks only; no monitoring dashboard.

**Data flow:**

```text
User Input → Validation → Diagnostic Functions → Result Collection → Terminal Summary / CSV Export
```

1. `main.py` reads menu choice, hostname, and port.
2. `validators.py` cleans and checks them.
3. `diagnostics.py` runs real DNS / ping / TCP checks, each returning a
   uniform result dict.
4. Results accumulate in a list (`latest_results`).
5. The list is printed as a summary and, on request, written to CSV by
   `report_generator.py`.

### Interview Questions and Concise Answers

1. **What does this project do?** Runs real DNS, ping, and single-port TCP
   checks from a CLI menu and exports the actual results to CSV.
2. **Which Python modules did you use and why?** `socket` (DNS/TCP),
   `subprocess` (OS ping), `ipaddress` (IP validation), `csv`/`pathlib`/
   `datetime` (reports), `platform`/`sys` (local info), `unittest` (tests).
3. **How does DNS resolution work here?** `socket.gethostbyname(host)`; IP
   literals skip the lookup and are reported as such.
4. **What happens on a DNS failure?** `socket.gaierror` is caught and returned
   as a `FAILED` result with a spelling/DNS-settings hint.
5. **How do you run ping portably?** `platform.system()` picks Windows
   (`-n`, `-w`) vs. Linux/macOS (`-c`, `-W`) arguments; the command runs as an
   argument list with `capture_output=True` and a timeout.
6. **Why never `shell=True`?** It invites shell-injection and quoting bugs;
   an argument list is safer and portable.
7. **How do you avoid hanging on ping?** A small fixed packet count (4) plus
   `subprocess.run(..., timeout=15)`, mapped to a `TIMEOUT` result.
8. **Why can't a failed ping prove a host is offline?** Firewalls commonly
   block ICMP while allowing TCP services, so the message says so explicitly.
9. **How does the TCP check work?** `socket.create_connection((host, port),
   timeout=3)` in a `with` block so the socket always closes.
10. **What do refused vs. timed-out TCP mean?** Refused = host reachable but
    nothing listening there; timeout = possibly filtered or slow. Neither
    proves the whole host is down.
11. **Why validate ports 1–65535?** That is the valid TCP port range; 0,
    negatives, > 65535, and non-numbers are rejected before connecting.
12. **How do you find the local IP without external sites?** Open a UDP socket
    and `connect()` to a well-known address (sends nothing); `getsockname()`
    reveals the local address the OS would use. Failures report "unavailable".
13. **What does each result dict contain?** `timestamp`, `target`, `test`,
    `status` (`SUCCESS`/`FAILED`/`TIMEOUT`/`ERROR`), `message`, `details`.
14. **How does CSV export avoid overwriting?** Timestamped default filename;
    if the name exists, `_1`, `_2`, … are appended; files are UTF-8 under
    `reports/`, which is auto-created.
15. **How do the tests avoid the internet?** They mock `gethostbyname`,
    `subprocess.run`, `create_connection`, and `shutil.which`, and write CSVs
    to temporary directories — 31 offline tests.

## Author

**Harsh Sandesh Laghave** — final-year Computer Engineering student.
Repository: <https://github.com/harshlaghave/network-connectivity-diagnostics>

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 Harsh Sandesh Laghave.
