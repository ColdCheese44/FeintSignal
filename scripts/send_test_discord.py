"""Secret-safe Watchtower delivery test for webhook and bot destinations.

Examples:
    python scripts/send_test_discord.py --list
    python scripts/send_test_discord.py domain_terrorism --dry-run
    python scripts/send_test_discord.py system_status
    python scripts/send_test_discord.py --all --confirm-all

Single-channel and bulk sends honor ``ENABLE_DISCORD_SEND``. ``--all`` requires
the explicit ``--confirm-all`` flag and sends one clearly labeled test message
per configured destination; it never dispatches queued alerts.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from backend.core.discord_routing import channels, resolve_channel  # noqa: E402
from backend.services import discord_service  # noqa: E402


def _list_destinations() -> int:
    status = discord_service.safe_destination_status()
    print("Discord destinations (credentials and IDs are never shown):")
    for item in channels():
        destination = status[item["id"]]
        print(
            f"  {item['id']:28} {item['channel_name']:25} "
            f"available={destination['delivery_available']} "
            f"transport={destination['preferred_transport'] or 'none'}"
        )
    available = sum(item["delivery_available"] for item in status.values())
    print(f"Coverage: {available}/{len(status)}")
    return 0


def _send_one(channel: str, dry_run: bool) -> dict:
    target = resolve_channel(channel)
    payload = discord_service.build_test_payload(target["id"])
    if dry_run:
        return {
            "sent": False,
            "reason": "dry_run",
            "channel": target["channel_name"],
            "transport": discord_service.safe_destination_status()[target["id"]]["preferred_transport"],
        }
    return discord_service.send(payload, channel=target["id"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", nargs="?", default="system_status", help="Route ID or fs-* channel name.")
    parser.add_argument("--list", action="store_true", help="Show safe delivery coverage for all destinations.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve payload and transport without sending.")
    parser.add_argument("--all", action="store_true", help="Target every configured Discord destination.")
    parser.add_argument("--confirm-all", action="store_true", help="Required confirmation for a 32-channel test.")
    args = parser.parse_args(argv)

    if args.list:
        return _list_destinations()
    if args.all and not args.confirm_all:
        print("Bulk test not sent. Re-run with --all --confirm-all to send one test per destination.")
        return 2

    targets = [item["id"] for item in channels()] if args.all else [args.channel]
    failures = 0
    for target in targets:
        try:
            result = _send_one(target, args.dry_run)
        except ValueError as exc:
            print(str(exc))
            return 3
        print(
            f"[{result.get('channel', target)}] sent={result.get('sent', False)} "
            f"transport={result.get('transport', 'none')} "
            f"status={result.get('status_code', result.get('reason', 'unknown'))}"
        )
        failures += int(not result.get("sent") and not args.dry_run)
    return 0 if failures == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
