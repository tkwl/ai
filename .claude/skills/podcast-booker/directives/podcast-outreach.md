# Podcast Outreach SOP
**Directive for the Podcast Booker Agent**

Target: 40 pitches by Feb 28, 2026 | 5 pitches per day | 10-20% expected response rate

---

## Overview

This SOP defines how to run James Ferrer's podcast outreach from start to finish. Follow steps in order each day. The goal is consistent, personalized outreach -- not spray-and-pray.

---

## Step 1: Check Progress (Daily, First Thing)

Before doing anything else, run the progress report.

```bash
cd /home/ubuntu/clawd/skills/podcast-booker
python3 execution/track_pitches.py report
```

Look at:
- Total pitches sent vs. 40 target
- Days remaining
- Needed per day (should be 5 or less)
- Any replies that need follow-up

If there are replies waiting, handle those first (see Step 5).

---

## Step 2: Discover New Podcast Candidates

Run the discovery script to find new shows. Do this at least every other day to keep the pipeline full.

```bash
python3 execution/find_podcasts.py --niche all --limit 10
```

### Niche rotation (cycle through to stay fresh)
- Monday: `--niche ai`
- Tuesday: `--niche entrepreneurship`
- Wednesday: `--niche manufacturing`
- Thursday: `--niche biohacking`
- Friday: `--niche all`

### If no LISTENNOTES_API_KEY is configured

The script will fall back to web search via LLM. This works but is slower. To get the ListenNotes API key:
1. Sign up at listennotes.com/api
2. Add to `/home/ubuntu/clawd/.env`:
   ```
   LISTENNOTES_API_KEY=your_key_here
   ```

### Manual research (supplement the script)

When the script results look thin, manually check:

| Directory | URL | What to look for |
|---|---|---|
| Listen Notes | listennotes.com | Search by topic, filter "Interviews" |
| Podchaser | podchaser.com | Guest history visible, contact info |
| Rephonic | rephonic.com | Audience size estimates, contact email |
| Podmatch | podmatch.com | Hosts actively seeking guests |
| Spotify/Apple | Manually browse | Look at "similar podcasts" on shows you know |

For each candidate you find manually, check:
- When was the last episode? (must be within 30 days)
- Does the show have past guests? (signals they accept guests)
- Is there a contact email or form?
- What specific episode could James reference?

---

## Step 3: Research Each Target (5-10 minutes per show)

Before pitching any show, listen to (or read summaries of) one recent episode. You are looking for:

1. **Specific episode title** to reference in the pitch
2. **The host's name** (get first name for the salutation)
3. **Contact method** (email? contact form? social DM?)
4. **Episode angle** -- what did they talk about that connects to James's background?
5. **Audience fit** -- would James's angles resonate with their listeners?

### Where to find contact info (in order of preference)
1. Podcast website "Contact" or "Be a Guest" page
2. Podchaser profile (often lists contact email)
3. Show notes (hosts sometimes list their email)
4. LinkedIn message to the host
5. Twitter/X DM as last resort

### Red flags -- skip these shows
- No new episodes in 30+ days (stale)
- Zero guest history (host-only format)
- Fewer than 10 episodes total (too new, low value)
- Episodes are short (under 20 minutes) -- not enough time for James's depth
- Non-English or heavily regional (outside James's audience)

---

## Step 4: Generate and Send Pitches

### Generate pitches

```bash
python3 execution/generate_pitch.py --count 5
```

This will pull the top 5 ready candidates and generate pitch emails using Claude.

To generate for a specific show:
```bash
python3 execution/generate_pitch.py --candidate "AI for Entrepreneurs" --episode "Ep 142: The future of AI in operations"
```

To force a specific angle:
```bash
python3 execution/generate_pitch.py --angle factory --count 5
```

### Review before sending

ALWAYS read each pitch before sending. Check for:
- Is the episode reference specific and accurate?
- Is the angle a good fit for this show's audience?
- Is there an em dash in the text? (Remove it -- house rule)
- Is it under 200 words (body only, not counting subject)?
- Does the CTA include cal.com/jamesferrer/ai?

### Send the pitch

Use James's email or approved outreach tool. Do NOT send from automation without James's approval.

**Email:** Use james@getexpressai.com (daily driver, check with James first)
**Contact forms:** Fill out manually; paste the pitch text
**LinkedIn:** If no email -- send a connection request with a short intro, then follow up with pitch

### After sending, log it

```bash
python3 execution/track_pitches.py mark-sent "PITCH_ID_OR_PODCAST_NAME"
```

Or log with notes:
```bash
python3 execution/track_pitches.py mark-sent "AI for Entrepreneurs" --notes "Sent via contact form, not email"
```

---

## Step 5: Handle Replies

Check for replies every day. When a podcast responds:

### If they say yes / ask for more info

```bash
python3 execution/track_pitches.py mark-replied "PODCAST_NAME" --response "Interested, wants topics list"
```

Then:
1. Reply promptly (same day ideally)
2. Send James's full bio, headshot, and sample talking points
3. Point them to cal.com/jamesferrer/ai for scheduling
4. Once episode is confirmed:
   ```bash
   python3 execution/track_pitches.py mark-booked "PODCAST_NAME" --response "Recording Feb 25 at 2 PM"
   ```

### If they decline

```bash
python3 execution/track_pitches.py mark-declined "PODCAST_NAME" --response "Not taking guests right now"
```

No hard feelings. Some shows are just closed. Move on.

### If no reply after 7 days

Send ONE follow-up. Keep it very short:

> "Hi [Name], just circling back on my pitch from [date]. Happy to share more about James's background if helpful. Still think [topic] would land well with your audience. Let me know either way!"

After the follow-up, wait 7 more days. If still no reply, mark as declined and move on.

---

## Step 6: Daily Wrap-Up

At end of each outreach session:

1. Run the progress report again:
   ```bash
   python3 execution/track_pitches.py report
   ```

2. Note in James's daily file (`memory/YYYY-MM-DD.md`):
   - How many pitches sent today
   - Any notable replies or bookings
   - Pipeline health (candidates remaining before next discovery run needed)

3. If pipeline is thin (fewer than 10 ready candidates), run discovery:
   ```bash
   python3 execution/find_podcasts.py --niche all
   ```

---

## Angle Selection Guide

| If the podcast is about... | Use this angle |
|---|---|
| AI, tech, automation, future of work | AI implementation (`--angle ai`) |
| Entrepreneurship, startups, founders | Factory closure lessons OR DOE framework |
| Manufacturing, operations, industry | Factory closure lessons (`--angle factory`) |
| Health, biohacking, longevity, performance | Anti-aging at 36 (`--angle antiaging`) |
| Data, strategy, experimentation | DOE framework (`--angle doe`) |
| Mixed / unclear | Auto-select (let the script decide) |

---

## Pitch Quality Checklist

Before sending any pitch, verify:

- [ ] Episode title is specific and real (not generic like "recent episode")
- [ ] Host name is correct (not misspelled)
- [ ] Angle matches the show's audience
- [ ] Body is under 200 words
- [ ] No em dashes in the text
- [ ] CTA includes cal.com/jamesferrer/ai
- [ ] Tone is warm and peer-to-peer (not desperate or formal)
- [ ] Contact info is correct (right email or form URL)

---

## Tracking Schema Reference

Each pitch in `data/pitches.json` has these fields:

```json
{
  "id": "pitch_1708200000_0",
  "podcast_name": "The AI for Entrepreneurs Show",
  "host": "Sarah Chen",
  "website": "aiforentrepreneurs.com",
  "contact_email": "hello@aiforentrepreneurs.com",
  "contact_url": "aiforentrepreneurs.com/contact",
  "angle_used": "AI Implementation for Business",
  "episode_referenced": "Ep 142: Using AI to 10x your sales team",
  "pitch_body": "Subject: ...\n\nHi Sarah,...",
  "generated_at": "2026-02-18T10:00:00",
  "sent_at": "2026-02-18T11:30:00",
  "status": "sent",
  "response": null,
  "notes": "Sent via contact form",
  "source": "listennotes",
  "generation_method": "llm"
}
```

**Status flow:** `generated` > `sent` > `opened` > `replied` > `booked` or `declined`

---

## Feb 28 Target Breakdown

| Week | Pitches Needed | Notes |
|---|---|---|
| Feb 18-21 | 20 | Front-load while energy is high |
| Feb 22-25 | 12 | Maintain pace |
| Feb 26-28 | 8 | Final push |
| **Total** | **40** | |

If James is traveling or busy, double up the day before to stay ahead of pace.

---

## Key Resources

| Resource | Path / URL |
|---|---|
| James's booking calendar | cal.com/jamesferrer/ai |
| Pitch log | `data/pitches.json` |
| Podcast candidates | `data/podcast_candidates.json` |
| Agent specification | `SKILL.md` |
| Find podcasts script | `execution/find_podcasts.py` |
| Generate pitch script | `execution/generate_pitch.py` |
| Track pitches script | `execution/track_pitches.py` |

---

*Last updated: 2026-02-17*
*Version: 1.0*
