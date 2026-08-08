"""
ARC SDK — Command Line Interface (CLI)
Provides the `arc` terminal command for inspecting, tracing, replaying, recovering, and running ARC sessions.
"""

import sys
import json
import argparse
from typing import Optional

from .version import __version__
from . import init, trace, replay, inspect as inspect_session, recover, verify, Client


def print_json(data: Any):
    """Format and print JSON output nicely to stdout."""
    print(json.dumps(data, indent=2, default=str))


def cmd_init(args: argparse.Namespace):
    """Handle `arc init` subcommand."""
    config_file = ".arc.json"
    config = {
        "server_url": args.server_url or "http://localhost:8000",
        "dashboard_url": args.dashboard_url or "http://localhost:3000",
        "api_key": args.api_key or "",
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"[OK] Initialized ARC SDK configuration in '{config_file}'.")


def cmd_trace(args: argparse.Namespace):
    """Handle `arc trace <session_id>` subcommand."""
    client = Client(server_url=args.server_url)
    res = client.get_trace(args.session_id)
    print_json(res)


def cmd_replay(args: argparse.Namespace):
    """Handle `arc replay <session_id>` subcommand."""
    client = Client(server_url=args.server_url)
    res = client.get_replay(args.session_id)
    print_json(res)


def cmd_inspect(args: argparse.Namespace):
    """Handle `arc inspect <session_id>` subcommand."""
    client = Client(server_url=args.server_url)
    res = client.get_session(args.session_id)
    print_json(res)


def cmd_recover(args: argparse.Namespace):
    """Handle `arc recover <session_id>` subcommand."""
    client = Client(server_url=args.server_url)
    res = client.get_recovery(args.session_id)
    print_json(res)


def cmd_verify(args: argparse.Namespace):
    """Handle `arc verify <session_id>` subcommand."""
    client = Client(server_url=args.server_url)
    res = client.verify_session(args.session_id)
    print_json(res)


def cmd_version(args: argparse.Namespace):
    """Handle `arc version` or `arc --version`."""
    print(f"ARC SDK v{__version__}")


def main():
    """Main CLI entrypoint for `arc` command."""
    parser = argparse.ArgumentParser(
        prog="arc",
        description="Agent Runtime Core (ARC) CLI — Monitoring & Reliability Tooling for Claude Agents",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"ARC SDK v{__version__}"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="ARC Backend server URL (default: http://localhost:8000)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize local ARC configuration file")
    p_init.add_argument("--api-key", help="ARC API Key")
    p_init.add_argument("--server-url", help="ARC Backend server URL")
    p_init.add_argument("--dashboard-url", help="ARC Dashboard URL")

    # trace
    p_trace = subparsers.add_parser("trace", help="Retrieve step execution trace for a session")
    p_trace.add_argument("session_id", help="Session UUID string")

    # replay
    p_replay = subparsers.add_parser("replay", help="Retrieve visual replay object for a session")
    p_replay.add_argument("session_id", help="Session UUID string")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect session status and details")
    p_inspect.add_argument("session_id", help="Session UUID string")

    # recover
    p_recover = subparsers.add_parser("recover", help="Inspect or trigger session recovery")
    p_recover.add_argument("session_id", help="Session UUID string")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify session Context Firewall compliance")
    p_verify.add_argument("session_id", help="Session UUID string")

    # version
    subparsers.add_parser("version", help="Print ARC SDK version")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "trace": cmd_trace,
        "replay": cmd_replay,
        "inspect": cmd_inspect,
        "recover": cmd_recover,
        "verify": cmd_verify,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
