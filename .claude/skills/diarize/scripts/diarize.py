#!/usr/bin/env python3
"""Diarize and transcribe audio/video files using AssemblyAI."""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


ASSEMBLYAI_BASE = "https://api.assemblyai.com/v2"


def get_api_key():
    key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not key:
        # Try loading from .env files
        for env_path in [
            os.path.expanduser("~/Dropbox/Express AI/.env"),
            os.path.expanduser("~/.env"),
        ]:
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ASSEMBLYAI_API_KEY="):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            if key:
                break
    if not key:
        print("ERROR: ASSEMBLYAI_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(endpoint, api_key, method="GET", data=None, content_type="application/json"):
    url = f"{ASSEMBLYAI_BASE}/{endpoint}" if not endpoint.startswith("http") else endpoint
    headers = {"authorization": api_key}
    body = None
    if data and content_type == "application/json":
        headers["content-type"] = "application/json"
        body = json.dumps(data).encode()
    elif data:
        headers["content-type"] = content_type
        body = data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def upload_file(file_path, api_key):
    print(f"Uploading {os.path.basename(file_path)}...")
    file_size = os.path.getsize(file_path)
    print(f"  File size: {file_size / (1024*1024):.1f} MB")

    with open(file_path, "rb") as f:
        file_data = f.read()

    result = api_request("upload", api_key, method="POST", data=file_data, content_type="application/octet-stream")
    print(f"  Upload complete.")
    return result["upload_url"]


def request_transcription(upload_url, api_key):
    print("Requesting transcription with speaker diarization...")
    data = {
        "audio_url": upload_url,
        "speaker_labels": True,
    }
    result = api_request("transcript", api_key, method="POST", data=data)
    return result["id"]


def poll_transcription(transcript_id, api_key):
    print("Waiting for transcription to complete...")
    while True:
        result = api_request(f"transcript/{transcript_id}", api_key)
        status = result["status"]
        if status == "completed":
            print("  Transcription complete!")
            return result
        elif status == "error":
            print(f"  ERROR: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"  Status: {status}...")
            time.sleep(5)


def format_timestamp(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"


def format_transcript(result, speaker_names=None):
    utterances = result.get("utterances", [])
    if not utterances:
        return result.get("text", "No transcript available.")

    # Build speaker map
    speakers = sorted(set(u["speaker"] for u in utterances))
    speaker_map = {}
    if speaker_names:
        name_list = [n.strip() for n in speaker_names.split(",")]
        for i, speaker in enumerate(speakers):
            if i < len(name_list):
                speaker_map[speaker] = name_list[i]
            else:
                speaker_map[speaker] = f"Speaker {speaker}"
    else:
        for speaker in speakers:
            speaker_map[speaker] = f"Speaker {speaker}"

    lines = []
    for u in utterances:
        name = speaker_map.get(u["speaker"], f"Speaker {u['speaker']}")
        ts = format_timestamp(u["start"])
        lines.append(f"[{ts}] {name}: {u['text']}")

    return "\n\n".join(lines)


def find_latest_recording(search_dir=None):
    if not search_dir:
        search_dir = os.path.expanduser("~/Documents/Zoom")

    audio_exts = {".m4a", ".mp3", ".wav", ".mp4", ".webm", ".ogg", ".flac"}
    candidates = []

    for root, dirs, files in os.walk(search_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in audio_exts:
                full = os.path.join(root, f)
                candidates.append((os.path.getmtime(full), full))

    if not candidates:
        print(f"No audio/video files found in {search_dir}", file=sys.stderr)
        sys.exit(1)

    candidates.sort(reverse=True)
    # Prefer .m4a (audio-only) over .mp4 (video) from same session
    latest_dir = os.path.dirname(candidates[0][1])
    for _, path in candidates:
        if os.path.dirname(path) == latest_dir and path.endswith(".m4a"):
            return path
    return candidates[0][1]


def main():
    parser = argparse.ArgumentParser(description="Diarize audio using AssemblyAI")
    parser.add_argument("file", nargs="?", help="Path to audio/video file (auto-detects latest Zoom recording if omitted)")
    parser.add_argument("--speakers", "-s", help="Comma-separated speaker names in order (e.g. 'James Ferrer,Alon Shabo')")
    parser.add_argument("--search-dir", help="Directory to search for recordings (default: ~/Documents/Zoom)")
    parser.add_argument("--output", "-o", help="Output file path (default: prints to stdout)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    args = parser.parse_args()

    file_path = args.file or find_latest_recording(args.search_dir)
    print(f"File: {file_path}")

    api_key = get_api_key()
    upload_url = upload_file(file_path, api_key)
    transcript_id = request_transcription(upload_url, api_key)
    result = poll_transcription(transcript_id, api_key)

    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_transcript(result, args.speakers)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Transcript saved to {args.output}")
    else:
        print("\n" + "=" * 80)
        print("TRANSCRIPT")
        print("=" * 80 + "\n")
        print(output)


if __name__ == "__main__":
    main()
