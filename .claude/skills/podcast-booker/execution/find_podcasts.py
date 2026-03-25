#!/usr/bin/env python3
"""
find_podcasts.py — Podcast Booker Skill
Searches podcast directories for shows relevant to James Ferrer's pitch angles.

Usage:
    python3 find_podcasts.py [--niche NICHE] [--limit N] [--output FILE]

Arguments:
    --niche     One of: ai, entrepreneurship, manufacturing, biohacking, all (default: all)
    --limit     Max results per query (default: 10)
    --output    Output JSON file (default: ../data/podcast_candidates.json)
    --dry-run   Print results without saving

Requires:
    - requests library (pip install requests)
    - LISTENNOTES_API_KEY in environment (optional but recommended)
    - PERPLEXITY_API_KEY or ANTHROPIC_API_KEY in environment (for web search fallback)
"""

import os
import sys
import json
import time
import argparse
import datetime
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


# ─── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
DEFAULT_OUTPUT = DATA_DIR / "podcast_candidates.json"

JAMES_ANGLES = {
    "ai": [
        "artificial intelligence business podcast",
        "AI implementation entrepreneurs",
        "machine learning business strategy podcast",
        "AI tools productivity podcast",
        "enterprise AI adoption podcast",
    ],
    "entrepreneurship": [
        "serial entrepreneur podcast guest",
        "tech startup founder stories podcast",
        "entrepreneur lessons failure success podcast",
        "building companies podcast interview",
        "innovation growth strategy podcast",
    ],
    "manufacturing": [
        "manufacturing future of work podcast",
        "industry 4.0 automation podcast",
        "factory operations entrepreneur podcast",
        "supply chain manufacturing lessons podcast",
        "industrial entrepreneurship podcast",
    ],
    "biohacking": [
        "longevity biohacking performance podcast",
        "anti-aging science entrepreneur podcast",
        "peak performance optimization podcast",
        "health longevity founders podcast",
        "cognitive performance science podcast",
    ],
}

LISTENNOTES_BASE = "https://listen-api.listennotes.com/api/v2"
PODCHASER_BASE = "https://api.podchaser.com/graphql"

# Minimum days since last episode to consider a show "active"
MAX_DAYS_SINCE_EPISODE = 30


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_env():
    """Load .env from workspace root."""
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


def load_pitches_log(pitches_file: Path) -> set:
    """Return set of podcast names already pitched."""
    if not pitches_file.exists():
        return set()
    try:
        with open(pitches_file) as f:
            pitches = json.load(f)
        return {p.get("podcast_name", "").lower() for p in pitches}
    except (json.JSONDecodeError, KeyError):
        return set()


def days_since(iso_date_str: str) -> int:
    """Return number of days since a date string (ISO 8601 or Unix timestamp)."""
    try:
        if isinstance(iso_date_str, (int, float)):
            ts = float(iso_date_str)
            dt = datetime.datetime.utcfromtimestamp(ts)
        else:
            iso_date_str = str(iso_date_str)[:10]
            dt = datetime.datetime.strptime(iso_date_str, "%Y-%m-%d")
        delta = datetime.datetime.utcnow() - dt
        return delta.days
    except Exception:
        return 9999  # assume stale if we can't parse


def is_active(podcast: dict) -> bool:
    """Return True if the podcast posted an episode in the last 30 days."""
    last_ep = podcast.get("latest_pub_date_ms") or podcast.get("last_episode_date")
    if last_ep is None:
        return False  # no date info, skip
    if isinstance(last_ep, (int, float)):
        # Listen Notes returns milliseconds
        last_ep = last_ep / 1000
        dt = datetime.datetime.utcfromtimestamp(last_ep)
    else:
        try:
            dt = datetime.datetime.strptime(str(last_ep)[:10], "%Y-%m-%d")
        except ValueError:
            return False
    delta = datetime.datetime.utcnow() - dt
    return delta.days <= MAX_DAYS_SINCE_EPISODE


def deduplicate(candidates: list) -> list:
    """Remove duplicate podcasts by name (case-insensitive)."""
    seen = set()
    unique = []
    for c in candidates:
        key = c.get("name", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


# ─── Source: Listen Notes API ─────────────────────────────────────────────────

def search_listennotes(query: str, api_key: str, limit: int = 10) -> list:
    """Search Listen Notes API for podcast shows."""
    if not api_key:
        return []

    params = urllib.parse.urlencode({
        "q": query,
        "type": "podcast",
        "interviews_only": 1,
        "language": "English",
        "len_min": 15,
        "sort_by_date": 0,
        "safe_mode": 0,
    })
    url = f"{LISTENNOTES_BASE}/search?{params}"

    req = urllib.request.Request(url, headers={"X-ListenAPI-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  [ListenNotes] HTTP {e.code} for query: {query}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  [ListenNotes] Error: {e}", file=sys.stderr)
        return []

    results = []
    for item in data.get("results", [])[:limit]:
        pod = item.get("podcast") or item
        latest_ms = pod.get("latest_pub_date_ms", 0)
        candidate = {
            "name": pod.get("title_original", pod.get("title", "Unknown")),
            "description": (pod.get("description_original") or pod.get("description", ""))[:300],
            "host": pod.get("publisher_original", pod.get("publisher", "")),
            "website": pod.get("website", ""),
            "rss": pod.get("rss", ""),
            "latest_pub_date_ms": latest_ms,
            "episode_count": pod.get("total_episodes", 0),
            "language": pod.get("language", "English"),
            "listennotes_url": f"https://www.listennotes.com/podcasts/{pod.get('id', '')}",
            "source": "listennotes",
            "query_used": query,
            "discovered_at": datetime.datetime.utcnow().isoformat(),
            "status": "candidate",
        }
        results.append(candidate)

    return results


# ─── Source: Web Search Fallback ──────────────────────────────────────────────

def search_web_fallback(query: str, env: dict) -> list:
    """
    Fallback: use Perplexity/Anthropic to find podcasts via web search.
    Returns a structured list of podcast candidates.

    This is called when ListenNotes API is unavailable.
    """
    api_key = env.get("PERPLEXITY_API_KEY") or env.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"  [WebFallback] No API key available for web search.", file=sys.stderr)
        return []

    # If using Perplexity
    if env.get("PERPLEXITY_API_KEY"):
        return _perplexity_search(query, api_key)

    # Anthropic web search
    return _anthropic_search(query, api_key)


def _perplexity_search(query: str, api_key: str) -> list:
    """Use Perplexity API (sonar model) to find podcast candidates."""
    prompt = (
        f"Find 5 active podcasts that regularly interview guests and are relevant to: '{query}'. "
        "For each podcast, provide: name, host name, website URL, approximate episode count, "
        "and why it's relevant. Format as a JSON array with keys: name, host, website, relevance. "
        "Only include shows that posted new episodes in the last 30 days."
    )

    payload = json.dumps({
        "model": "sonar",
        "messages": [{"role": "user", "content": prompt}],
        "return_citations": False,
    }).encode()

    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        return _parse_llm_podcast_response(content, "perplexity", query)
    except Exception as e:
        print(f"  [Perplexity] Error: {e}", file=sys.stderr)
        return []


def _anthropic_search(query: str, api_key: str) -> list:
    """Use Anthropic API to suggest podcast candidates."""
    prompt = (
        f"Find 5 active podcasts that regularly interview guests and are relevant to: '{query}'. "
        "For each podcast, provide: name, host name, website URL, approximate episode count, "
        "and why it's relevant. Format as a JSON array with keys: name, host, website, relevance. "
        "Only include shows that posted new episodes in the last 30 days. "
        "Return ONLY the JSON array, no other text."
    )

    payload = json.dumps({
        "model": "claude-haiku-20240307",
        "max_tokens": 1024,
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        content = data["content"][0]["text"]
        return _parse_llm_podcast_response(content, "anthropic", query)
    except Exception as e:
        print(f"  [Anthropic] Error: {e}", file=sys.stderr)
        return []


def _parse_llm_podcast_response(content: str, source: str, query: str) -> list:
    """Parse JSON from LLM response into candidate dicts."""
    # Strip markdown fences if present
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON array in the response
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            try:
                raw = json.loads(match.group())
            except json.JSONDecodeError:
                return []
        else:
            return []

    candidates = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        candidates.append({
            "name": item.get("name", "Unknown"),
            "description": item.get("relevance", item.get("description", ""))[:300],
            "host": item.get("host", ""),
            "website": item.get("website", ""),
            "rss": "",
            "latest_pub_date_ms": 0,
            "episode_count": item.get("episode_count", 0),
            "language": "English",
            "listennotes_url": "",
            "source": source,
            "query_used": query,
            "discovered_at": datetime.datetime.utcnow().isoformat(),
            "status": "candidate",
            "active_unverified": True,  # LLM says active, not confirmed
        })

    return candidates


# ─── Filter & Score ───────────────────────────────────────────────────────────

def score_candidate(podcast: dict) -> int:
    """
    Score a podcast candidate 0-100.
    Higher = better fit for James.
    """
    score = 50  # base

    # Activity bonus (verified recent episode)
    if podcast.get("latest_pub_date_ms", 0) > 0:
        if is_active(podcast):
            score += 20
        else:
            score -= 30  # penalize stale shows

    # Episode count (more = established show)
    ep_count = podcast.get("episode_count", 0)
    if ep_count > 200:
        score += 15
    elif ep_count > 50:
        score += 10
    elif ep_count > 10:
        score += 5

    # Has website (easier to find contact)
    if podcast.get("website"):
        score += 5

    # LLM-sourced (unverified activity)
    if podcast.get("active_unverified"):
        score += 5  # LLM suggested it's active

    return max(0, min(100, score))


def filter_candidates(candidates: list, already_pitched: set) -> list:
    """Remove already-pitched shows and obviously stale ones. Score and sort rest."""
    filtered = []
    for c in candidates:
        name_lower = c.get("name", "").lower()
        # Skip already pitched
        if name_lower in already_pitched:
            c["status"] = "already_pitched"
            continue
        # Score it
        c["score"] = score_candidate(c)
        # Skip very stale shows (ListenNotes data only — LLM fallback skips this)
        if c.get("latest_pub_date_ms", 0) > 0 and not is_active(c):
            c["status"] = "stale"
            continue
        c["status"] = "ready"
        filtered.append(c)

    # Sort by score descending
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
    return filtered


# ─── Load / Save ──────────────────────────────────────────────────────────────

def load_existing_candidates(output_path: Path) -> list:
    """Load existing candidates file if it exists."""
    if not output_path.exists():
        return []
    try:
        with open(output_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_candidates(candidates: list, output_path: Path) -> None:
    """Save candidates to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(candidates, f, indent=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Find podcast candidates for James Ferrer")
    parser.add_argument("--niche", default="all",
                        choices=["ai", "entrepreneurship", "manufacturing", "biohacking", "all"],
                        help="Niche to search (default: all)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max results per query (default: 10)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Output JSON file path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print results without saving")
    parser.add_argument("--force", action="store_true",
                        help="Include already-stale candidates anyway")
    args = parser.parse_args()

    env = load_env()
    listennotes_key = env.get("LISTENNOTES_API_KEY", "")

    # Load already-pitched shows to avoid duplicates
    pitches_file = DATA_DIR / "pitches.json"
    already_pitched = load_pitches_log(pitches_file)
    print(f"Already pitched: {len(already_pitched)} shows")

    # Determine which niches to search
    niches = list(JAMES_ANGLES.keys()) if args.niche == "all" else [args.niche]
    print(f"Searching niches: {', '.join(niches)}")
    print(f"ListenNotes API: {'available' if listennotes_key else 'not configured, using web fallback'}")
    print()

    all_candidates = []
    total_queries = 0

    for niche in niches:
        queries = JAMES_ANGLES[niche]
        print(f"--- Niche: {niche.upper()} ({len(queries)} queries) ---")

        for query in queries:
            print(f"  Searching: '{query}'")
            results = []

            # Primary: ListenNotes API
            if listennotes_key:
                results = search_listennotes(query, listennotes_key, args.limit)
                if results:
                    print(f"    ListenNotes: {len(results)} results")

            # Fallback: web search via LLM
            if not results:
                results = search_web_fallback(query, env)
                if results:
                    print(f"    Web fallback: {len(results)} results")
                else:
                    print(f"    No results found")

            all_candidates.extend(results)
            total_queries += 1

            # Rate limiting
            time.sleep(0.5)

    print()
    print(f"Total raw results: {len(all_candidates)} from {total_queries} queries")

    # Deduplicate
    unique = deduplicate(all_candidates)
    print(f"After deduplication: {len(unique)}")

    # Filter and score
    if args.force:
        for c in unique:
            c["score"] = score_candidate(c)
        filtered = unique
    else:
        filtered = filter_candidates(unique, already_pitched)

    print(f"After filtering (active + not pitched): {len(filtered)}")
    print()

    # Load existing candidates and merge
    if not args.dry_run:
        existing = load_existing_candidates(args.output)
        existing_names = {c.get("name", "").lower() for c in existing}
        new_only = [c for c in filtered if c.get("name", "").lower() not in existing_names]
        merged = existing + new_only
        print(f"New candidates this run: {len(new_only)}")
        print(f"Total in candidates file: {len(merged)}")
    else:
        merged = filtered
        print(f"(Dry run: not saving)")

    # Print top candidates
    print()
    print("=== TOP 10 CANDIDATES ===")
    for i, c in enumerate(filtered[:10], 1):
        score = c.get("score", "?")
        name = c.get("name", "Unknown")
        host = c.get("host", "Unknown host")
        website = c.get("website", "no website")
        source = c.get("source", "?")
        print(f"  {i:2d}. [{score:3}] {name}")
        print(f"       Host: {host} | {website} | via {source}")
        if c.get("description"):
            print(f"       {c['description'][:100]}...")
        print()

    # Save
    if not args.dry_run:
        save_candidates(merged, args.output)
        print(f"Saved to: {args.output}")
    else:
        print("Dry run complete. Use without --dry-run to save.")

    # Summary for heartbeat
    print()
    print(f"SUMMARY: Found {len(filtered)} fresh candidates ({len(new_only) if not args.dry_run else '?'} new)")
    print(f"Run generate_pitch.py to create pitches for top candidates.")


if __name__ == "__main__":
    main()
