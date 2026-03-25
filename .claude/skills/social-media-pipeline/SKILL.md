---
name: social-media-pipeline
description: "End-to-end video content pipeline using DOE framework. Takes raw talking-head clips, filters bad ones via transcript analysis, trims silence, overlays TikTok-style text hooks, generates per-platform captions, and optionally posts to Instagram/TikTok/YouTube/LinkedIn. Use when James records content and needs it processed and posted."
---

# Social Media Pipeline (DOE Framework)

Meta-skill that orchestrates the full content pipeline from raw clips to posted content.

## Quick Start — How to Use

When James says **"process these"**, **"run the pipeline"**, or similar:

```bash
# Spawn a sub-agent that runs:
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch --cleanup
```

That's it. The script handles everything: listing Drive files, downloading, processing, filtering bad takes, and cleaning up.

### Command Reference

```bash
# Process all clips from Drive "1-Raw" folder
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch

# Process + delete source files from Drive after
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch --cleanup

# Dry run — show what would happen without doing anything
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch --dry-run

# Force re-process (ignore existing artifacts)
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch --force

# Single file (local)
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py /path/to/video.mp4

# Single file (Drive ID)
python3 /home/ubuntu/clawd/pipeline/run_pipeline.py DRIVE_FILE_ID
```

### Sub-Agent Spawn Template
```
Task: Process video batch pipeline
Run: python3 /home/ubuntu/clawd/pipeline/run_pipeline.py --batch --cleanup
Timeout: (number_of_clips × 15min) seconds — e.g., 4 clips = 3600s
Working directory: /home/ubuntu/clawd
Report: final file paths, rejected clips with reasons, total time
```

## How the Pipeline Works

### James's Side
1. Records clips on iPhone (1080p 30fps preferred)
2. Uploads MOVs to Google Drive "1-Raw" folder
3. Tells Claude "process these"

### Pipeline Steps (per clip, automated by `run_pipeline.py`)

```
Download from Drive
  ↓
Downscale to 1080p 30fps (h264) — delete source MOV
  ↓
Extract audio → Transcribe via Groq Whisper
  ↓
Filter bad takes (< 10s, < 15 words, "let me start over", etc.)
  ↓ REJECTED → skip, log reason
Trim silence via transcript word timestamps (±0.3s padding)
  ↓
Re-transcribe TRIMMED video (timestamps must match trimmed version!)
  ↓
Generate hook PNG (ImageMagick, 3-5 word text from transcript)
  ↓
Generate ASS subtitles (word-level, TikTok style, Roboto Black 62pt)
  ↓
Final render: hook overlay (first 3s) + ASS subs + audio enhancement
  ↓
Cleanup: delete source from Drive (if --cleanup)
```

### Post-Batch Output
The script prints a summary:
- Total clips found
- Clips processed vs rejected (with reasons)
- Final file paths
- Total processing time

## Google Drive Pipeline Folders
```
Content Pipeline/ (ID: 1BWnbCQLLRNsMsrRdWApzETVJzszZU84z)
  1-Raw/           (ID: 1H2IcUnqtXkcfXmQgEilA8g5ROt21EI3I) ← James uploads here
  2-Processing/    (ID: 1mNwPKcCG6uM_P8MRHROw_KoTjXBF_XzN)
  3-Ready to Post/ (ID: 1kB6tWQm8Fj0LHCw2oK_3Pn3_gGeK6_JM)
  4-Posted/        (ID: 1aJlCadzpCutLe5NzgoxURGIO5bgt8mBy)
```

## gog Drive Commands Reference
```bash
# Always prefix: GOG_KEYRING_PASSWORD=clawdbot GOG_ACCOUNT=james@vuiu.co
gog drive ls --parent "<folderId>" --max 50 --json    # List files
gog drive download <fileId> --out /path/              # Download
gog drive delete <fileId> --force                     # Delete (trash)
gog drive upload --parent "<folderId>" /path/file     # Upload
```

## Pipeline Artifacts (per clip)
All stored in `/home/ubuntu/clawd/.tmp/pipeline/` with IMG_XXXX prefix:
- `IMG_XXXX_1080p.mp4` — Normalized 1080p version
- `IMG_XXXX_audio.mp3` — Extracted audio (for initial transcription)
- `IMG_XXXX_transcript.json` — Pre-trim transcript (for filtering)
- `IMG_XXXX_trimmed.mp4` — Silence-trimmed version
- `IMG_XXXX_trimmed_audio.mp3` — Trimmed audio
- `IMG_XXXX_trimmed_transcript.json` — Re-transcribed trimmed version (timestamps match!)
- `IMG_XXXX_hook.png` — Hook text overlay image
- `IMG_XXXX.ass` — ASS subtitle file (word-level, TikTok style)
- `IMG_XXXX_final.mp4` — Final rendered video (ready to post)

## Bad Take Filter Criteria
Clips are REJECTED if:
- Duration < 10 seconds
- Word count < 15
- Contains "let me start over", "wait wait", "sorry sorry", etc. near beginning
- Average word length < 2 chars (gibberish/incoherence)

## Operational Constraints
- **VPS max: 1080p 30fps.** 4K HEVC causes OOM. Script always downscales first.
- **RAM: ~1-2GB free.** Script processes ONE clip at a time, sequentially.
- **Disk: ~24GB free.** Source MOVs deleted after downscaling to save space.
- **Telegram can't receive videos > 20MB.** Use Google Drive for delivery.
- **Groq audio limit: 25MB.** Script auto-re-extracts at lower quality if exceeded.
- **Sub-agent timeout:** Set to (number_of_clips × 15min) as safe estimate.

## Audio Enhancement
- **DO NOT USE AUPHONIC.** Free tier adds watermarks. Completely unusable.
- ffmpeg filters applied in final render: `highpass=f=80,lowpass=f=12000,loudnorm=I=-16:LRA=11:TP=-1.5`

## Prerequisites
- Groq API key — loaded from auth-profiles.json (`profiles.groq:manual.token`)
- ffmpeg — installed
- ImageMagick (`convert`) — installed
- gog CLI v0.9.0 — installed
- Font: Roboto Black (`/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf`)
- Font: DejaVu Sans Bold (`/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`)

## Learnings
- Groq Whisper mishears "N8N" as "innate", "Claude" as "Clawed" — needs post-processing corrections
- **ALWAYS transcribe the TRIMMED video**, not the original. Timestamps must match trimmed version.
- Hook stays on screen for first 3 seconds (overlaid at top)
- ASS subtitles: Roboto Black 62pt, white text, lower third (MarginV: 300)
- Full render takes ~90s for 40s 1080p video at CRF 23
- ffmpeg render polling generates massive context bloat. The script handles this internally.
- Large MOV files (1GB+) take 5-10min to download from Drive.
- Sub-agent approach keeps main session responsive while batch runs in background.

## Status (updated Jan 30, 2026)
- [x] Batch mode (`--batch`) — process all Drive clips in one command
- [x] Cleanup mode (`--cleanup`) — delete processed files from Drive
- [x] Dry run mode (`--dry-run`) — preview without executing
- [x] Downscale/normalize to 1080p 30fps
- [x] Transcription via Groq Whisper (word-level timestamps)
- [x] Bad take filtering via transcript analysis
- [x] Silence trimming via transcript word timestamps
- [x] Re-transcription of trimmed video (fixes subtitle sync bug!)
- [x] Hook overlay PNG generation (ImageMagick)
- [x] ASS subtitle generation (word-level, TikTok style)
- [x] Final render (hook + subs + audio enhancement)
- [x] Batch summary report
- [x] Caption generation (per-platform: IG, TikTok, YouTube, LinkedIn) — DONE

## Caption Generation Rules

When generating captions for any platform:

**FIRST LINE must always be the CTA.** If there's a lead magnet or deliverable, the very first line is:
`Comment "[KEYWORD]" to get [deliverable description]`

Examples:
- `Comment "WORKFLOW" to get the free agentic workflow setup guide`
- `Comment "AI" to get the free AI assistant setup guide`

If no specific deliverable exists for this video, use a generic engagement CTA:
- `Comment "[relevant keyword]" if you want to learn more`

**The rest of the caption follows after the CTA line.** Hook, value, hashtags.
- [ ] Upload finals to Drive "3-Ready to Post" — TODO
- [ ] Filler word removal (cut "um", "uh", "like") — FUTURE
- [ ] Automated posting — FUTURE
