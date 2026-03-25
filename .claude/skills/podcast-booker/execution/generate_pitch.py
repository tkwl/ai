#!/usr/bin/env python3
"""
generate_pitch.py — Podcast Booker Skill
Generates personalized pitch emails for James Ferrer for each podcast candidate.

Usage:
    python3 generate_pitch.py [--candidate NAME] [--angle ANGLE] [--episode EPISODE] [--output FILE]

Arguments:
    --candidate     Podcast name from candidates file (or "next" to use top uncontacted)
    --angle         Force a specific angle: ai | factory | antiaging | doe | auto (default: auto)
    --episode       Specific episode title to reference (optional, will prompt if not set)
    --output        Output JSON file for pitches log (default: ../data/pitches.json)
    --count         How many pitches to generate in one run (default: 5)
    --dry-run       Print pitches without logging them

Requires:
    - ANTHROPIC_API_KEY in /home/ubuntu/clawd/.env
    - podcast_candidates.json to exist (run find_podcasts.py first)
"""

import os
import sys
import json
import time
import argparse
import datetime
import urllib.request
import urllib.error
from pathlib import Path


# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CANDIDATES_FILE = DATA_DIR / "podcast_candidates.json"
DEFAULT_PITCHES_FILE = DATA_DIR / "pitches.json"

JAMES = {
    "name": "James Ferrer",
    "title": "Nuclear Physicist turned AI Growth Partner",
    "cal_link": "cal.com/jamesferrer/ai",
    "location": "Southeast Asia (available for remote recording)",
    "short_bio": (
        "James Ferrer is an American-trained nuclear physicist who built 3 tech companies, "
        "distributed products to 79 countries, and now helps mid-market businesses implement "
        "AI before their competitors do. He uses the DOE (Design of Experiments) framework "
        "from his physics background to run faster, smarter growth experiments."
    ),
}

ANGLES = {
    "ai": {
        "label": "AI Implementation for Business",
        "hook": "Most companies are implementing AI in the wrong order and wasting months. Here's the framework that actually works.",
        "talking_points": [
            "The 3 mistakes businesses make when rolling out AI tools (and how to avoid them)",
            "The DOE framework: how nuclear physicists run experiments faster than startups",
            "How James's clients have reduced operational overhead by 30-50% using AI in 90 days",
        ],
        "best_for": ["ai", "tech", "entrepreneurship", "future of work", "business"],
    },
    "factory": {
        "label": "Factory Closure Lessons",
        "hook": "I shut down a manufacturing operation and it was the best education of my life. Here's what I learned about leading through failure.",
        "talking_points": [
            "The moment James knew the factory had to close and how he told the team",
            "What manufacturing taught him about operational discipline that Silicon Valley ignores",
            "How failure at scale becomes a competitive advantage when you're willing to talk about it",
        ],
        "best_for": ["manufacturing", "entrepreneurship", "leadership", "resilience"],
    },
    "antiaging": {
        "label": "Anti-Aging and Performance at 36",
        "hook": "A nuclear physicist applies scientific rigor to his own biology -- and the results at 36 are measurable.",
        "talking_points": [
            "The longevity stack a physicist uses (bloodwork, microneedling, creatine, sleep protocols)",
            "Why cognitive performance matters more than hustle when you're running multiple companies",
            "The experiment-based approach to self-optimization: how to actually know what's working",
        ],
        "best_for": ["biohacking", "longevity", "performance", "health", "anti-aging"],
    },
    "doe": {
        "label": "The DOE Framework for Business Growth",
        "hook": "Design of Experiments is how nuclear physicists move faster than everyone else. Businesses can steal this method.",
        "talking_points": [
            "What DOE is and why it's 10x better than A/B testing for business decisions",
            "How James used DOE to launch products in 79 countries without a traditional marketing budget",
            "Applying scientific method to sales, marketing, and operations to compress learning cycles",
        ],
        "best_for": ["entrepreneurship", "strategy", "innovation", "growth", "data"],
    },
}

PITCH_TEMPLATE = """Subject: Guest pitch: {angle_label} for {podcast_name}

Hi {host_name},

I came across your episode "{episode_title}" and it hit on exactly what I spend most of my time thinking about: {episode_connection}.

I'm James Ferrer -- American-trained nuclear physicist, built 3 tech companies (one shipped to 79 countries), and now I work as an AI growth partner helping mid-market businesses implement AI before their competitors do.

I think your audience would love an episode on: {topic_hook}

Here's what I'd bring to the conversation:

- {point_1}
- {point_2}
- {point_3}

I've been in the trenches on this -- from running manufacturing operations to closing a factory to now running AI implementations for B2B clients. I talk from experience, not theory.

If this sounds like a fit, you can grab time directly here: {cal_link}

Either way, keep up the great work on {podcast_name}. The {episode_compliment} conversation was genuinely useful.

James
{cal_link}
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env_path = Path("/home/ubuntu/clawd/.env")
    env = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def load_candidates() -> list:
    if not CANDIDATES_FILE.exists():
        print(f"ERROR: candidates file not found at {CANDIDATES_FILE}")
        print("Run find_podcasts.py first.")
        sys.exit(1)
    with open(CANDIDATES_FILE) as f:
        return json.load(f)


def load_pitches(pitches_file: Path) -> list:
    if not pitches_file.exists():
        return []
    try:
        with open(pitches_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_pitches(pitches: list, pitches_file: Path) -> None:
    pitches_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pitches_file, "w") as f:
        json.dump(pitches, f, indent=2)


def get_pitched_names(pitches: list) -> set:
    return {p.get("podcast_name", "").lower() for p in pitches}


def pick_angle(podcast: dict, forced_angle: str = "auto") -> dict:
    """Pick the best angle for a podcast based on its description and niche."""
    if forced_angle != "auto" and forced_angle in ANGLES:
        return ANGLES[forced_angle]

    desc = (podcast.get("description", "") + " " + podcast.get("name", "")).lower()
    query = podcast.get("query_used", "").lower()
    combined = desc + " " + query

    # Score each angle by keyword overlap
    scores = {}
    for angle_key, angle in ANGLES.items():
        score = sum(1 for kw in angle["best_for"] if kw in combined)
        scores[angle_key] = score

    best = max(scores, key=lambda k: scores[k])
    # Default to AI if tied or no match
    if scores[best] == 0:
        best = "ai"

    return ANGLES[best]


def infer_host_name(podcast: dict) -> str:
    """Try to extract or guess the host's first name."""
    host = podcast.get("host", "")
    if host:
        # Get first word (first name)
        first = host.strip().split()[0] if host.strip() else ""
        # Remove common prefixes
        for prefix in ["The", "Dr.", "Mr.", "Ms."]:
            if first == prefix and len(host.split()) > 1:
                first = host.split()[1]
        if first:
            return first
    return "there"  # fallback


# ─── LLM Pitch Generation ─────────────────────────────────────────────────────

def generate_pitch_with_llm(podcast: dict, angle: dict, episode_title: str, api_key: str) -> str:
    """
    Use Claude to generate a personalized pitch email.
    Falls back to template if API call fails.
    """
    host_name = infer_host_name(podcast)
    podcast_name = podcast.get("name", "your show")
    desc = podcast.get("description", "")

    prompt = f"""You are writing a podcast guest pitch email for James Ferrer.

JAMES'S PROFILE:
{json.dumps(JAMES, indent=2)}

SELECTED ANGLE: {angle['label']}
HOOK: {angle['hook']}
TALKING POINTS:
{chr(10).join(f'- {p}' for p in angle['talking_points'])}

TARGET PODCAST:
Name: {podcast_name}
Host: {host_name}
Description: {desc[:400]}
Episode to reference: {episode_title or "their most popular recent episode"}

WRITE A PITCH EMAIL that:
1. Opens by referencing the specific episode "{episode_title}" and connecting it to James's angle
2. Introduces James briefly (2 sentences max)
3. Proposes the episode topic using the angle hook
4. Lists the 3 talking points as bullets
5. Ends with a soft CTA linking to cal.com/jamesferrer/ai
6. Keeps total length under 200 words
7. Uses warm, direct tone -- one entrepreneur to another
8. Uses NO em dashes (use commas or periods instead)
9. Subject line: "Guest pitch: {angle['label']} for {podcast_name}"

Return ONLY the email (subject line + body), nothing else."""

    payload = json.dumps({
        "model": "claude-haiku-20240307",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"  [LLM] Error generating pitch: {e}", file=sys.stderr)
        return None


def generate_pitch_from_template(podcast: dict, angle: dict, episode_title: str) -> str:
    """Generate pitch from template (no LLM required)."""
    host_name = infer_host_name(podcast)
    podcast_name = podcast.get("name", "your show")

    return PITCH_TEMPLATE.format(
        angle_label=angle["label"],
        podcast_name=podcast_name,
        host_name=host_name,
        episode_title=episode_title or "your recent episode",
        episode_connection="how to actually get results from AI and new technology",
        topic_hook=angle["hook"],
        point_1=angle["talking_points"][0],
        point_2=angle["talking_points"][1],
        point_3=angle["talking_points"][2],
        cal_link=JAMES["cal_link"],
        episode_compliment="framework-focused",
    )


# ─── Contact Info Lookup ──────────────────────────────────────────────────────

def get_contact_info(podcast: dict) -> dict:
    """Extract or infer contact email from podcast data."""
    website = podcast.get("website", "")
    name = podcast.get("name", "")

    # Try to construct contact from website
    contact = {
        "email": "",
        "contact_url": "",
        "twitter": "",
    }

    if website:
        # Common podcast contact page patterns
        domain = website.rstrip("/")
        contact["contact_url"] = f"{domain}/contact"

    return contact


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate podcast pitch emails for James Ferrer")
    parser.add_argument("--candidate", default="next",
                        help="Podcast name or 'next' for top uncontacted (default: next)")
    parser.add_argument("--angle", default="auto",
                        choices=["ai", "factory", "antiaging", "doe", "auto"],
                        help="Angle to use for pitch (default: auto)")
    parser.add_argument("--episode", default="",
                        help="Specific episode title to reference in pitch")
    parser.add_argument("--output", type=Path, default=DEFAULT_PITCHES_FILE,
                        help="Pitches log file path")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of pitches to generate (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print pitches without saving to log")
    args = parser.parse_args()

    env = load_env()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("WARNING: No ANTHROPIC_API_KEY found. Will use template fallback.")

    candidates = load_candidates()
    pitches = load_pitches(args.output)
    pitched_names = get_pitched_names(pitches)

    print(f"Candidates available: {len(candidates)}")
    print(f"Already pitched: {len(pitched_names)}")
    print()

    # Filter to ready candidates only
    ready = [c for c in candidates if c.get("status") == "ready"
             and c.get("name", "").lower() not in pitched_names]
    ready.sort(key=lambda x: x.get("score", 0), reverse=True)

    if not ready:
        print("No ready candidates found. Run find_podcasts.py to discover more shows.")
        sys.exit(0)

    # Select targets
    if args.candidate.lower() == "next":
        targets = ready[:args.count]
    else:
        targets = [c for c in ready if args.candidate.lower() in c.get("name", "").lower()]
        if not targets:
            print(f"Candidate '{args.candidate}' not found in ready list.")
            print("Available candidates:")
            for c in ready[:10]:
                print(f"  - {c['name']} (score: {c.get('score', '?')})")
            sys.exit(1)

    print(f"Generating pitches for {len(targets)} podcast(s)...")
    print()

    new_pitches = []
    for podcast in targets:
        podcast_name = podcast.get("name", "Unknown")
        host = podcast.get("host", "Unknown")
        website = podcast.get("website", "")
        print(f"--- {podcast_name} ---")
        print(f"    Host: {host}")
        print(f"    Website: {website}")

        # Pick angle
        angle = pick_angle(podcast, args.angle)
        print(f"    Angle: {angle['label']}")

        # Episode reference
        episode = args.episode
        if not episode:
            episode = f"a recent episode on {podcast.get('query_used', 'the topic').replace(' podcast', '')}"
        print(f"    Episode ref: {episode}")

        # Generate pitch
        if api_key:
            pitch_body = generate_pitch_with_llm(podcast, angle, episode, api_key)
            method = "llm"
        else:
            pitch_body = None
            method = "template"

        if not pitch_body:
            pitch_body = generate_pitch_from_template(podcast, angle, episode)
            method = "template"

        print(f"    Generated via: {method}")

        # Contact info
        contact = get_contact_info(podcast)

        # Build pitch record
        pitch_record = {
            "id": f"pitch_{int(time.time())}_{len(new_pitches)}",
            "podcast_name": podcast_name,
            "host": host,
            "website": website,
            "contact_email": contact.get("email", ""),
            "contact_url": contact.get("contact_url", ""),
            "angle_used": angle["label"],
            "episode_referenced": episode,
            "pitch_body": pitch_body,
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "sent_at": None,
            "status": "generated",  # generated | sent | opened | replied | booked | declined
            "response": None,
            "notes": "",
            "source": podcast.get("source", ""),
            "generation_method": method,
        }

        new_pitches.append(pitch_record)

        # Print the pitch
        print()
        print("=" * 60)
        print(pitch_body)
        print("=" * 60)
        print()

        # Rate limit LLM calls
        if api_key:
            time.sleep(1)

    # Save all pitches
    if not args.dry_run:
        all_pitches = pitches + new_pitches
        save_pitches(all_pitches, args.output)

        # Update candidates status
        pitched_this_run = {p["podcast_name"].lower() for p in new_pitches}
        for c in candidates:
            if c.get("name", "").lower() in pitched_this_run:
                c["status"] = "pitched"
        with open(CANDIDATES_FILE, "w") as f:
            json.dump(candidates, f, indent=2)

        print(f"Saved {len(new_pitches)} pitch(es) to {args.output}")
        print(f"Updated {CANDIDATES_FILE}")
    else:
        print(f"(Dry run: {len(new_pitches)} pitches generated, not saved)")

    # Progress report
    total_pitched = len(pitches) + (len(new_pitches) if not args.dry_run else 0)
    target = 40
    days_left = (datetime.date(2026, 2, 28) - datetime.date.today()).days
    remaining = target - total_pitched
    per_day_needed = remaining / max(days_left, 1)

    print()
    print("=== PROGRESS REPORT ===")
    print(f"  Total pitched to date: {total_pitched} / {target}")
    print(f"  Remaining: {remaining}")
    print(f"  Days until Feb 28: {days_left}")
    print(f"  Needed per day: {per_day_needed:.1f}")
    if total_pitched >= target:
        print("  TARGET REACHED!")
    elif per_day_needed <= 5:
        print("  On track.")
    else:
        print("  BEHIND PACE -- increase daily pitch volume.")


if __name__ == "__main__":
    main()
