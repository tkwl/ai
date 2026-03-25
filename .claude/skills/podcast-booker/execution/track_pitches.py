#!/usr/bin/env python3
"""
track_pitches.py — Podcast Booker Skill
Manages the pitch log: mark sent, update status, show progress report.

Usage:
    python3 track_pitches.py report
    python3 track_pitches.py mark-sent PITCH_ID
    python3 track_pitches.py mark-replied PITCH_ID [--response "their reply summary"]
    python3 track_pitches.py mark-booked PITCH_ID [--response "booking details"]
    python3 track_pitches.py mark-declined PITCH_ID
    python3 track_pitches.py list [--status STATUS]
    python3 track_pitches.py init

Commands:
    report          Show progress toward Feb 28 target
    mark-sent       Mark a pitch as sent (updates sent_at timestamp)
    mark-replied    Mark a pitch as replied (podcast responded)
    mark-booked     Mark a booking confirmed
    mark-declined   Mark a pitch as declined
    list            List all pitches, optionally filtered by status
    init            Initialize empty pitches.json
"""

import sys
import json
import argparse
import datetime
from pathlib import Path


# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
PITCHES_FILE = DATA_DIR / "pitches.json"

TARGET_PITCHES = 40
TARGET_DATE = datetime.date(2026, 2, 28)

STATUS_FLOW = ["generated", "sent", "opened", "replied", "booked", "declined"]

STATUS_EMOJI = {
    "generated": "draft",
    "sent": "sent",
    "opened": "opened",
    "replied": "replied",
    "booked": "BOOKED",
    "declined": "declined",
}


# ─── Data Helpers ─────────────────────────────────────────────────────────────

def load_pitches() -> list:
    if not PITCHES_FILE.exists():
        return []
    try:
        with open(PITCHES_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse {PITCHES_FILE}. File may be corrupted.")
        sys.exit(1)


def save_pitches(pitches: list) -> None:
    PITCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PITCHES_FILE, "w") as f:
        json.dump(pitches, f, indent=2)


def find_pitch(pitches: list, pitch_id: str) -> dict | None:
    """Find a pitch by ID or by podcast name substring."""
    # Try exact ID match
    for p in pitches:
        if p.get("id") == pitch_id:
            return p
    # Try name substring match
    for p in pitches:
        if pitch_id.lower() in p.get("podcast_name", "").lower():
            return p
    return None


def now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_init(args):
    """Initialize an empty pitches.json."""
    if PITCHES_FILE.exists():
        print(f"Pitches file already exists at {PITCHES_FILE}")
        print("Use 'report' to see current status.")
        return
    PITCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_pitches([])
    print(f"Initialized empty pitches log: {PITCHES_FILE}")


def cmd_report(args):
    """Print progress report."""
    pitches = load_pitches()

    # Counts by status
    by_status = {}
    for p in pitches:
        s = p.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    sent = sum(by_status.get(s, 0) for s in ["sent", "opened", "replied", "booked", "declined"])
    booked = by_status.get("booked", 0)
    replied = by_status.get("replied", 0) + booked
    declined = by_status.get("declined", 0)
    generated = by_status.get("generated", 0)

    days_left = (TARGET_DATE - datetime.date.today()).days
    remaining = TARGET_PITCHES - sent
    per_day_needed = remaining / max(days_left, 1)

    response_rate = (replied / sent * 100) if sent > 0 else 0
    booking_rate = (booked / sent * 100) if sent > 0 else 0

    print("=" * 50)
    print("PODCAST BOOKER -- PROGRESS REPORT")
    print("=" * 50)
    print(f"Date: {datetime.date.today()} | Target: Feb 28, 2026")
    print()
    print(f"Pitches sent:    {sent:3d} / {TARGET_PITCHES}")
    print(f"Days remaining:  {days_left}")
    print(f"Needed per day:  {per_day_needed:.1f}")
    print()
    print(f"Responses:  {replied} ({response_rate:.0f}% response rate)")
    print(f"Booked:     {booked} ({booking_rate:.0f}% booking rate)")
    print(f"Declined:   {declined}")
    print(f"In draft:   {generated}")
    print()

    if sent >= TARGET_PITCHES:
        print("TARGET REACHED -- 40 pitches sent!")
    elif per_day_needed <= 5:
        print("Status: ON TRACK")
    else:
        print(f"Status: BEHIND PACE -- need {per_day_needed:.1f}/day, target is 5/day")

    print()

    # Recent activity
    recent = sorted(pitches, key=lambda p: p.get("sent_at") or p.get("generated_at") or "", reverse=True)[:5]
    if recent:
        print("RECENT PITCHES:")
        for p in recent:
            name = p.get("podcast_name", "Unknown")
            status = p.get("status", "?")
            sent_at = (p.get("sent_at") or p.get("generated_at") or "")[:10]
            label = STATUS_EMOJI.get(status, status)
            print(f"  {sent_at} | [{label:8s}] {name}")

    print()

    # Booked shows
    booked_list = [p for p in pitches if p.get("status") == "booked"]
    if booked_list:
        print("BOOKINGS CONFIRMED:")
        for p in booked_list:
            print(f"  - {p['podcast_name']}: {p.get('response', 'Details TBD')}")

    print("=" * 50)


def cmd_mark_sent(args):
    """Mark a pitch as sent."""
    pitches = load_pitches()
    pitch = find_pitch(pitches, args.pitch_id)

    if not pitch:
        print(f"Pitch not found: {args.pitch_id}")
        print("Use 'list' to see available pitches.")
        sys.exit(1)

    pitch["status"] = "sent"
    pitch["sent_at"] = now_iso()
    if args.notes:
        pitch["notes"] = args.notes

    save_pitches(pitches)
    print(f"Marked as SENT: {pitch['podcast_name']}")
    print(f"Sent at: {pitch['sent_at']}")


def cmd_mark_replied(args):
    """Mark a pitch as replied."""
    pitches = load_pitches()
    pitch = find_pitch(pitches, args.pitch_id)

    if not pitch:
        print(f"Pitch not found: {args.pitch_id}")
        sys.exit(1)

    pitch["status"] = "replied"
    pitch["replied_at"] = now_iso()
    if args.response:
        pitch["response"] = args.response
    if args.notes:
        pitch["notes"] = args.notes

    save_pitches(pitches)
    print(f"Marked as REPLIED: {pitch['podcast_name']}")
    if args.response:
        print(f"Response: {args.response}")


def cmd_mark_booked(args):
    """Mark a pitch as booked (episode confirmed)."""
    pitches = load_pitches()
    pitch = find_pitch(pitches, args.pitch_id)

    if not pitch:
        print(f"Pitch not found: {args.pitch_id}")
        sys.exit(1)

    pitch["status"] = "booked"
    pitch["booked_at"] = now_iso()
    if args.response:
        pitch["response"] = args.response
    if args.notes:
        pitch["notes"] = args.notes

    save_pitches(pitches)
    print(f"BOOKED: {pitch['podcast_name']}")
    print("Congratulations on the booking!")
    if args.response:
        print(f"Details: {args.response}")


def cmd_mark_declined(args):
    """Mark a pitch as declined."""
    pitches = load_pitches()
    pitch = find_pitch(pitches, args.pitch_id)

    if not pitch:
        print(f"Pitch not found: {args.pitch_id}")
        sys.exit(1)

    pitch["status"] = "declined"
    pitch["declined_at"] = now_iso()
    if args.response:
        pitch["response"] = args.response
    if args.notes:
        pitch["notes"] = args.notes

    save_pitches(pitches)
    print(f"Marked as DECLINED: {pitch['podcast_name']}")


def cmd_list(args):
    """List pitches, optionally filtered by status."""
    pitches = load_pitches()

    if not pitches:
        print("No pitches logged yet. Run generate_pitch.py first.")
        return

    filtered = pitches
    if args.status:
        filtered = [p for p in pitches if p.get("status") == args.status]

    # Sort by date
    filtered.sort(
        key=lambda p: p.get("sent_at") or p.get("generated_at") or "",
        reverse=True
    )

    print(f"{'ID':<30} {'Status':<12} {'Date':<12} {'Podcast'}")
    print("-" * 80)

    for p in filtered:
        pid = p.get("id", "?")[:28]
        status = p.get("status", "?")[:10]
        date = (p.get("sent_at") or p.get("generated_at") or "?")[:10]
        name = p.get("podcast_name", "Unknown")[:35]
        print(f"{pid:<30} {status:<12} {date:<12} {name}")

    print()
    print(f"Total: {len(filtered)} pitches")
    if args.status:
        print(f"(filtered by status: {args.status})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Track podcast pitches for James Ferrer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # report
    subparsers.add_parser("report", help="Show progress report")

    # init
    subparsers.add_parser("init", help="Initialize empty pitches.json")

    # list
    list_parser = subparsers.add_parser("list", help="List all pitches")
    list_parser.add_argument("--status", help="Filter by status (generated|sent|replied|booked|declined)")

    # mark-sent
    sent_parser = subparsers.add_parser("mark-sent", help="Mark a pitch as sent")
    sent_parser.add_argument("pitch_id", help="Pitch ID or podcast name substring")
    sent_parser.add_argument("--notes", default="", help="Optional notes")

    # mark-replied
    replied_parser = subparsers.add_parser("mark-replied", help="Mark a pitch as replied")
    replied_parser.add_argument("pitch_id", help="Pitch ID or podcast name substring")
    replied_parser.add_argument("--response", default="", help="Summary of their response")
    replied_parser.add_argument("--notes", default="", help="Optional notes")

    # mark-booked
    booked_parser = subparsers.add_parser("mark-booked", help="Mark an episode as booked")
    booked_parser.add_argument("pitch_id", help="Pitch ID or podcast name substring")
    booked_parser.add_argument("--response", default="", help="Booking details (date, format, etc.)")
    booked_parser.add_argument("--notes", default="", help="Optional notes")

    # mark-declined
    declined_parser = subparsers.add_parser("mark-declined", help="Mark a pitch as declined")
    declined_parser.add_argument("pitch_id", help="Pitch ID or podcast name substring")
    declined_parser.add_argument("--response", default="", help="Summary of their response")
    declined_parser.add_argument("--notes", default="", help="Optional notes")

    args = parser.parse_args()

    commands = {
        "report": cmd_report,
        "init": cmd_init,
        "list": cmd_list,
        "mark-sent": cmd_mark_sent,
        "mark-replied": cmd_mark_replied,
        "mark-booked": cmd_mark_booked,
        "mark-declined": cmd_mark_declined,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
