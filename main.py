"""Command-line menu for the Network Connectivity & Diagnostics Toolkit."""

from diagnostics import (
    check_ping,
    check_tcp_port,
    get_local_network_info,
    resolve_dns,
    run_all_diagnostics,
)
from report_generator import export_report_to_csv
from validators import validate_host, validate_port

DEFAULT_PORT = 443

# Latest real diagnostic results, kept in memory for CSV export.
latest_results: list = []


def _print_result(result: dict) -> None:
    """Print one result dictionary in a readable form."""
    print(f"[{result.get('status', '?')}] {result.get('test', '?')} -> {result.get('target', '?')}")
    print(f"  {result.get('message', '')}")
    if result.get("details"):
        print(f"  Details: {result.get('details')}")
    print(f"  Time: {result.get('timestamp', '')}")


def _print_summary(results: list) -> None:
    """Print a concise summary table of a diagnostic run."""
    print("\n--- Summary ---")
    for result in results:
        print(
            f"{result.get('test', '?'):10} "
            f"{result.get('status', '?'):8} "
            f"{result.get('message', '')}"
        )
    print("----------------\n")


def _ask_host(prompt: str = "Enter hostname or IP address: ") -> str:
    """Prompt for a host and return the validated, cleaned value."""
    raw = input(prompt)
    return validate_host(raw)


def _ask_port(prompt: str = f"Enter TCP port [default {DEFAULT_PORT}]: ") -> int:
    """Prompt for a port; an empty answer selects the default port."""
    raw = input(prompt).strip()
    if not raw:
        return DEFAULT_PORT
    return validate_port(raw)


def _show_menu() -> None:
    print("\n=== Network Connectivity & Diagnostics Toolkit ===")
    print("1. Run all diagnostics for a host")
    print("2. Check DNS resolution")
    print("3. Check network reachability using ping")
    print("4. Check TCP port connectivity")
    print("5. View local network information")
    print("6. Export the latest diagnostic report to CSV")
    print("7. Exit")


def _handle_run_all() -> None:
    global latest_results
    try:
        host = _ask_host()
        port = _ask_port()
    except ValueError as exc:
        print(f"Input error: {exc}")
        return
    results = run_all_diagnostics(host, port)
    latest_results = results
    for result in results:
        _print_result(result)
    _print_summary(results)


def _handle_dns() -> None:
    global latest_results
    try:
        host = _ask_host()
    except ValueError as exc:
        print(f"Input error: {exc}")
        return
    result = resolve_dns(host)
    latest_results = [result]
    _print_result(result)


def _handle_ping() -> None:
    global latest_results
    try:
        host = _ask_host()
    except ValueError as exc:
        print(f"Input error: {exc}")
        return
    result = check_ping(host)
    latest_results = [result]
    _print_result(result)


def _handle_tcp() -> None:
    global latest_results
    try:
        host = _ask_host()
        port = _ask_port()
    except ValueError as exc:
        print(f"Input error: {exc}")
        return
    print("Only test systems you own or have permission to diagnose.")
    result = check_tcp_port(host, port)
    latest_results = [result]
    _print_result(result)


def _handle_local_info() -> None:
    info = get_local_network_info()
    print("\n--- Local Network Information ---")
    print(f"Hostname:      {info['hostname']}")
    if info["local_ip"]:
        print(f"Local IPv4:    {info['local_ip']}")
        print(f"               ({info['local_ip_note']})")
    else:
        print(f"Local IPv4:    unavailable ({info['local_ip_note']})")
    print(f"Operating sys: {info['os']}")
    print(f"Python:        {info['python_version']} ({info['python_executable']})")
    print("---------------------------------\n")


def _handle_export() -> None:
    if not latest_results:
        print("No results to export yet. Run a diagnostic test first.")
        return
    export_report_to_csv(latest_results)


def main() -> None:
    """Run the menu loop until the user selects Exit."""
    print("Welcome! This tool runs basic network diagnostics.")
    print("No internet connection is needed just to start it.")
    while True:
        _show_menu()
        choice = input("Select an option (1-7): ").strip()
        if choice == "1":
            _handle_run_all()
        elif choice == "2":
            _handle_dns()
        elif choice == "3":
            _handle_ping()
        elif choice == "4":
            _handle_tcp()
        elif choice == "5":
            _handle_local_info()
        elif choice == "6":
            _handle_export()
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
