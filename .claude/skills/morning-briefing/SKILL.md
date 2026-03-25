---
name: morning-briefing
description: Daily morning identity alignment and briefing for James. Use when running the 6 AM cron job or when James asks for his morning briefing, identity alignment, scorecard, or daily plan check. Presents identity vision, scores 8 dimensions /100, evaluates the day's plan against identity game criteria, and scans email/tasks.
---

# Morning Briefing

Run this briefing in exact order. No fluff. Co-founder energy.

## Part 1: Who I Want to Be (display every time)

Read `memory/identity-vision.md` and present in full:

1. **2026 Core Vision** — quote it verbatim
2. **Pius Archetype** — list all 5 traits
3. **Game Structure** — How to Win, What's at Stake, 1-Year Mission
4. **Daily Rule** — One business video before any fulfillment work

## Part 2: Identity Game Scorecard (morning baseline)

Score each dimension 0-100 based on yesterday's performance and current trajectory. Check `memory/YYYY-MM-DD.md` (yesterday) for evidence. No inflation.

Format as bullet list (NO markdown tables, Telegram can't render them):

```
📊 IDENTITY SCORECARD
• Entrepreneur (not IC): X/100
• Sharing Value Publicly: X/100
• Relationships & Networking: X/100
• Kind/Patient/Not Anxious (Pius): X/100
• Fun & People Want to Be Around: X/100
• Stability (emotional, financial, actions): X/100
• Father (present, safety net): X/100
• Health Protocol: X/100
═══════════════
OVERALL: X/100
```

Scoring guide: see `references/scoring-guide.md`

Save morning baseline scores to today's `memory/YYYY-MM-DD.md`.

## Part 3: Today's Plan Alignment

Check today's calendar:
```bash
GOG_KEYRING_PASSWORD=clawdbot GOG_ACCOUNT=james@vuiu.co gog cal list
```

For each calendar item, evaluate against identity game:
- ✅ **Aligned** — moves toward vision
- ⚠️ **Neutral** — necessary but not identity-building
- ❌ **Misaligned** — busywork, avoidance, or working against vision

Flag gaps: no content creation scheduled? No outreach? No relationship-building? Propose additions.

Suggest reordering if high-identity items are buried behind low-value ones.

## Part 4: Email + Tasks

Scan unread emails:
```bash
GOG_KEYRING_PASSWORD=clawdbot GOG_ACCOUNT=james@vuiu.co gog gmail list --unread
```

Summarize top items needing response. Check recent memory files for open tasks.

## Tone

Direct, motivating, entrepreneurial. Frame the day through the identity game, not just productivity. This is about who James is becoming, not what he's checking off.
