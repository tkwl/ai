# Podcast Booker Skill

## Purpose

Find relevant podcasts and pitch James Ferrer as a guest. Target: 5 personalized pitches per day, 40 pitches total by Feb 28, 2026.

## Guest Profile

**Name:** James Ferrer
**Title:** Nuclear Physicist turned Serial Entrepreneur | AI Growth Partner
**One-liner:** American-trained nuclear physicist who built 3 tech companies (one shipped to 79 countries), shut down a factory, and now helps businesses implement AI before their competitors do.

### Core Angles (pick 1-2 per pitch)
| Angle | Hook | Best for... |
|---|---|---|
| AI for business | Most companies are implementing AI wrong — here's the DOE framework that actually works | AI/tech, entrepreneurship, future of work |
| Factory closure | What shutting down a factory taught me about leading through failure | Manufacturing, entrepreneurship, leadership |
| Anti-aging at 36 | The longevity protocol a physicist uses to stay sharp and build companies | Health, biohacking, performance |
| DOE framework | How nuclear physicists design experiments — and how businesses can steal it for growth | Entrepreneurship, strategy, innovation |

### Bio Options
**Short (1 sentence):**
James Ferrer is an American-trained nuclear physicist turned serial entrepreneur who has built 3 tech companies, shipped product to 79 countries, and now partners with businesses to implement AI that drives real revenue.

**Medium (2-3 sentences):**
James Ferrer spent years as a nuclear physicist before pivoting into tech entrepreneurship, building 3 companies and distributing products to 79 countries. After closing a manufacturing operation and turning the lessons into a framework, he now works as an AI growth partner helping mid-market companies implement AI before their competitors do. He uses the same DOE (Design of Experiments) methodology from his physics background to help businesses run faster, smarter growth experiments.

**Long (full pitch):**
See `generate_pitch.py` — the script generates a full contextual bio based on angle selected.

### Contact / CTAs
- **Booking calendar:** cal.com/jamesferrer/ai
- **LinkedIn:** linkedin.com/in/jamesferrer (verify before pitching)
- **Based in:** Southeast Asia (Bangkok / Chiang Mai), available for remote recording

---

## Activation Instructions

Read this file top-to-bottom. Then:
1. Run `execution/find_podcasts.py` to discover new shows
2. Review the shortlist it produces
3. Run `execution/generate_pitch.py` to generate personalized pitches
4. Send pitches manually or via email client
5. Log results with `execution/track_pitches.py`
6. Repeat daily. Track progress against the Feb 28 deadline.

Full SOP: `directives/podcast-outreach.md`

---

## File Map

| File | Purpose |
|---|---|
| `SKILL.md` | This file. Agent spec and guest profile. |
| `execution/find_podcasts.py` | Search podcast directories for relevant shows |
| `execution/generate_pitch.py` | Generate personalized pitch emails per show |
| `execution/track_pitches.py` | Log pitches sent, track responses, show progress |
| `directives/podcast-outreach.md` | Step-by-step SOP for the full outreach process |
| `data/pitches.json` | Pitch log (auto-created by track_pitches.py) |
| `data/podcast_candidates.json` | Discovered shows awaiting pitch (auto-created) |

---

## Targets

| Metric | Target |
|---|---|
| Daily pitches sent | 5 |
| Total pitches by Feb 28 | 40 |
| Expected response rate | 10-20% |
| Expected bookings | 4-8 from 40 pitches |

---

## Search Strategy

### Primary Directories (in order of reliability)
1. **Listen Notes** (listennotes.com) - largest podcast search engine, guest-friendly filter available
2. **Podchaser** (podchaser.com) - contact info, guest history visible
3. **Rephonic** (rephonic.com) - audience size estimates, pitch contact info
4. **Podmatch** (podmatch.com) - dedicated guest-host matching platform

### Search Queries by Niche
```
AI/Tech:
  "artificial intelligence business" podcast
  "AI implementation" podcast guests
  "machine learning entrepreneurs" podcast

Entrepreneurship:
  "serial entrepreneur" podcast
  "startup founder" podcast interview
  "tech entrepreneur" podcast 2025 2026

Manufacturing / Future of Work:
  "manufacturing future" podcast
  "industry 4.0" podcast
  "automation jobs" podcast

Biohacking / Anti-aging:
  "longevity biohacking" podcast
  "peak performance" podcast
  "anti-aging science" podcast
```

### Filter Criteria
- **Active:** Last episode posted within 30 days
- **English language only**
- **Accepts guests:** Visible past guest history
- **Audience size:** 500+ listeners (don't filter too hard — micro-niche shows convert well)
- **NOT already contacted:** Check pitches.json before pitching

---

## Pitch Quality Standards

Every pitch email must:
1. Reference a **specific episode by name** (shows you actually listened)
2. State **James's relevant angle** for THAT show's audience
3. Include **concrete talking points** (3 bullets)
4. Keep body under **200 words**
5. End with a **soft CTA** (no hard sell, just a booking link)
6. Use **no em dashes** (house rule — humanizer style)

### Tone
Warm, direct, confident. Not begging. Not overly formal. One founder to another.

---

## Dependencies

- Python 3.x (standard library only for core functions)
- `requests` library for web search calls
- `.env` file at `/home/ubuntu/clawd/.env` with:
  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` for pitch generation
  - `LISTENNOTES_API_KEY` (optional — enhances search quality)

---

## Error Handling Rules

- If a directory returns no results, try next directory in list
- If pitch generation fails, log the show to candidates list and skip
- Never send a pitch without a specific episode reference
- If pitches.json is missing, create it fresh (schema in track_pitches.py)

---

## Session Handoff Protocol

At end of each session, the agent MUST:
1. Update `data/pitches.json` with all pitches sent
2. Note any shows that declined or bounced
3. Report: X pitches sent today, Y total, Z remaining to hit Feb 28 target
4. Flag any high-value shows that deserve a follow-up

---

*Last updated: 2026-02-17*
*Version: 1.0*
