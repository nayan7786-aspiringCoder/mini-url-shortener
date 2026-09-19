#!/usr/bin/env python3
"""
Mini URL Shortener - Command Line Interface (CLI)
Track A: 1st Year (CLI-based)

Supports:
  - shorten <url> [--alias ALIAS]
  - resolve <code> [--open]
  - list [--sort {created_at,clicks,code}] [--asc]
  - stats <code>
  - delete <code>
  - export [--format {json,csv}] [--output FILE]
  - interactive (REPL mode)
"""

import sys
import os
import argparse
import webbrowser
import json
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any

from storage import Storage
from shortener import URLShortenerService


def format_table(rows: List[Dict[str, Any]]) -> str:
    """Formats a list of URL mappings as an aligned ASCII table."""
    if not rows:
        return "No shortened URLs found in database."

    headers = ["Short Code", "Clicks", "Created At (UTC)", "Original URL"]
    max_url_len = 45

    table_data = []
    for r in rows:
        url = r["original_url"]
        if len(url) > max_url_len:
            url = url[: max_url_len - 3] + "..."
        created = r["created_at"]
        if "T" in created:
            created = created.replace("T", " ")[:19]
        table_data.append([
            r["code"],
            str(r["clicks"]),
            created,
            url
        ])

    col_widths = [len(h) for h in headers]
    for row in table_data:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    # Build separator and format string
    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_str = "| " + " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))) + " |"

    lines = [sep, header_str, sep]
    for row in table_data:
        line_str = "| " + " | ".join(row[i].ljust(col_widths[i]) for i in range(len(row))) + " |"
        lines.append(line_str)
    lines.append(sep)

    return "\n".join(lines)


def cmd_shorten(service: URLShortenerService, args: argparse.Namespace) -> int:
    success, code, msg = service.shorten(args.url, custom_alias=args.alias)
    if success:
        print(f"[SUCCESS] Short Code: {code}")
        print(f"          Original URL: {args.url}")
        if args.alias:
            print(f"          Custom Alias: Yes")
        return 0
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 1


def cmd_resolve(service: URLShortenerService, args: argparse.Namespace) -> int:
    success, original_url, msg = service.resolve(args.code, increment_clicks=True)
    if success:
        print(f"[RESOLVED] {original_url}")
        if getattr(args, "open", False):
            print(f"Opening '{original_url}' in your default browser...")
            webbrowser.open(original_url)
        return 0
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 1


def cmd_list(service: URLShortenerService, args: argparse.Namespace) -> int:
    sort_by = getattr(args, "sort", "created_at") or "created_at"
    descending = not getattr(args, "asc", False)
    urls = service.list_urls(sort_by=sort_by, descending=descending)
    print(f"\nStored URLs ({len(urls)} total, sorted by {sort_by} {'desc' if descending else 'asc'}):")
    print(format_table(urls))
    print()
    return 0


def cmd_stats(service: URLShortenerService, args: argparse.Namespace) -> int:
    success, stats, msg = service.get_stats(args.code)
    if success and stats:
        created = stats["created_at"].replace("T", " ")[:19] if "T" in stats["created_at"] else stats["created_at"]
        last_acc = stats["last_accessed"]
        last_acc_str = last_acc.replace("T", " ")[:19] if (last_acc and "T" in last_acc) else (last_acc or "Never")

        print("\n" + "=" * 45)
        print(f" Statistics for Code: {stats['code']}")
        print("=" * 45)
        print(f" Original URL  : {stats['original_url']}")
        print(f" Total Clicks  : {stats['clicks']}")
        print(f" Created At    : {created} UTC")
        print(f" Last Accessed : {last_acc_str}")
        print("=" * 45 + "\n")
        return 0
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 1


def cmd_delete(service: URLShortenerService, args: argparse.Namespace) -> int:
    success, msg = service.delete(args.code)
    if success:
        print(f"[SUCCESS] {msg}")
        return 0
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 1


def cmd_export(service: URLShortenerService, args: argparse.Namespace) -> int:
    urls = service.list_urls(sort_by="created_at", descending=False)
    fmt = (getattr(args, "format", "json") or "json").lower()
    default_filename = f"urls_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{fmt}"
    output_file = getattr(args, "output", None) or default_filename

    try:
        if fmt == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(urls, f, indent=2)
        elif fmt == "csv":
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["code", "original_url", "created_at", "clicks", "last_accessed"])
                writer.writeheader()
                writer.writerows(urls)
        else:
            print(f"[ERROR] Unsupported format '{fmt}'. Choose 'json' or 'csv'.", file=sys.stderr)
            return 1

        print(f"[SUCCESS] Exported {len(urls)} entries to '{output_file}'.")
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to export: {e}", file=sys.stderr)
        return 1


def interactive_repl(service: URLShortenerService) -> None:
    """Provides an interactive command loop."""
    print("=" * 60)
    print("  Welcome to Mini URL Shortener (Interactive Shell)")
    print("  Type 'help' for available commands or 'exit' / 'quit' to close.")
    print("=" * 60)

    while True:
        try:
            line = input("\nshortener> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not line:
            continue

        parts = line.split()
        command = parts[0].lower()

        if command in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        elif command == "help":
            print("""
Available Commands:
  shorten <url> [--alias <name>]  Shorten a URL with optional custom alias
  resolve <code> [--open]          Resolve a short code (optionally open in browser)
  list [--sort {clicks,created}]   Display all shortened URLs in a table
  stats <code>                     View click count and timestamps for a code
  delete <code>                    Remove a short code from storage
  export [json|csv] [filename]     Export data to JSON or CSV
  help                             Show this help message
  exit / quit                      Exit interactive mode
""")
        elif command == "shorten":
            if len(parts) < 2:
                print("Usage: shorten <url> [--alias <name>]")
                continue
            url = parts[1]
            alias = None
            if "--alias" in parts:
                idx = parts.index("--alias")
                if idx + 1 < len(parts):
                    alias = parts[idx + 1]
            success, code, msg = service.shorten(url, custom_alias=alias)
            if success:
                print(f"[SUCCESS] Short Code: {code}")
            else:
                print(f"[ERROR] {msg}")

        elif command == "resolve":
            if len(parts) < 2:
                print("Usage: resolve <code> [--open]")
                continue
            code = parts[1]
            open_browser = "--open" in parts
            success, original_url, msg = service.resolve(code, increment_clicks=True)
            if success:
                print(f"[RESOLVED] {original_url}")
                if open_browser:
                    print(f"Opening '{original_url}' in browser...")
                    webbrowser.open(original_url)
            else:
                print(f"[ERROR] {msg}")

        elif command == "list":
            sort_by = "created_at"
            if "--sort" in parts:
                idx = parts.index("--sort")
                if idx + 1 < len(parts) and parts[idx + 1] in ("clicks", "created_at", "code"):
                    sort_by = parts[idx + 1]
            urls = service.list_urls(sort_by=sort_by, descending=True)
            print(format_table(urls))

        elif command == "stats":
            if len(parts) < 2:
                print("Usage: stats <code>")
                continue
            parser_args = argparse.Namespace(code=parts[1])
            cmd_stats(service, parser_args)

        elif command == "delete":
            if len(parts) < 2:
                print("Usage: delete <code>")
                continue
            success, msg = service.delete(parts[1])
            print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")

        elif command == "export":
            fmt = "json"
            out = None
            if len(parts) >= 2:
                fmt = parts[1]
            if len(parts) >= 3:
                out = parts[2]
            parser_args = argparse.Namespace(format=fmt, output=out)
            cmd_export(service, parser_args)

        else:
            print(f"Unknown command: '{command}'. Type 'help' for instructions.")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mini URL Shortener CLI (Python Standard Library)",
        epilog="Run 'python main.py interactive' or run without arguments for interactive shell."
    )
    parser.add_argument(
        "--db",
        default="urls.db",
        help="Path to SQLite database file (default: urls.db)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # shorten
    p_shorten = subparsers.add_parser("shorten", help="Shorten a URL")
    p_shorten.add_argument("url", help="The original long URL to shorten")
    p_shorten.add_argument("--alias", "-a", help="Custom alias for the URL (optional)")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Resolve a short code back to original URL")
    p_resolve.add_argument("code", help="The short code to resolve")
    p_resolve.add_argument("--open", "-o", action="store_true", help="Open the resolved URL in your default browser")

    # list
    p_list = subparsers.add_parser("list", help="List all shortened URLs")
    p_list.add_argument(
        "--sort",
        choices=["created_at", "clicks", "code"],
        default="created_at",
        help="Sort by field (default: created_at)"
    )
    p_list.add_argument("--asc", action="store_true", help="Sort in ascending order (default: descending)")

    # stats
    p_stats = subparsers.add_parser("stats", help="Show usage statistics for a short code")
    p_stats.add_argument("code", help="The short code to inspect")

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a shortened URL mapping")
    p_delete.add_argument("code", help="The short code to delete")

    # export
    p_export = subparsers.add_parser("export", help="Export mappings to JSON or CSV file")
    p_export.add_argument("--format", choices=["json", "csv"], default="json", help="Export format (default: json)")
    p_export.add_argument("--output", "-o", help="Output file path (optional)")

    # interactive
    subparsers.add_parser("interactive", help="Start an interactive command-line session")

    return parser


def main() -> None:
    parser = create_parser()

    # If run with no arguments, launch interactive mode
    if len(sys.argv) == 1:
        storage = Storage(db_path="urls.db")
        service = URLShortenerService(storage)
        interactive_repl(service)
        return

    args = parser.parse_args()
    storage = Storage(db_path=args.db)
    service = URLShortenerService(storage)

    dispatch = {
        "shorten": cmd_shorten,
        "resolve": cmd_resolve,
        "list": cmd_list,
        "stats": cmd_stats,
        "delete": cmd_delete,
        "export": cmd_export,
    }

    if args.command == "interactive":
        interactive_repl(service)
    elif args.command in dispatch:
        exit_code = dispatch[args.command](service, args)
        sys.exit(exit_code)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
