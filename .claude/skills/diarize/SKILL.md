---
name: diarize
description: "Transcribe and diarize audio/video recordings using AssemblyAI. Use when the user asks to diarize, transcribe, or process a meeting recording, Zoom call, audio file, or video file. Handles speaker identification, timestamp formatting, and speaker name mapping. Triggers on: 'diarize', 'transcribe', 'transcription', 'meeting recording', 'who said what', or any request to process audio/video for text output."
---

# Audio Diarization with AssemblyAI

Run `scripts/diarize.py` to transcribe and diarize audio/video files. Uses only stdlib (no pip install needed).

## Usage

```bash
python3 <skill-path>/scripts/diarize.py [FILE] --speakers "Name1,Name2" --output transcript.md
```

- **FILE**: Path to audio/video file. If omitted, auto-finds the latest Zoom recording in `~/Documents/Zoom`.
- **--speakers / -s**: Comma-separated speaker names mapped to Speaker A, B, etc.
- **--output / -o**: Save transcript to file instead of stdout.
- **--search-dir**: Override recording search directory.
- **--json**: Output raw AssemblyAI JSON response.

## API Key

Reads `ASSEMBLYAI_API_KEY` from environment or `~/Dropbox/Express AI/.env`.

## Workflow

1. Auto-detect or accept the audio file path
2. Upload to AssemblyAI
3. Request transcription with `speaker_labels: true`
4. Poll until complete (~1-2 minutes per 10 minutes of audio)
5. Format with speaker names and timestamps

## Output Format

```
[00:00:05] James Ferrer: ...
[00:00:23] Alon Shabo: ...
```

Save transcripts to the relevant project directory alongside the recording or in a `transcripts/` folder.
