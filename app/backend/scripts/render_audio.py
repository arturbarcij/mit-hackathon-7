#!/usr/bin/env python3
"""Render Swahili and English answer clips with ElevenLabs. Build time only.

Never import this from the farmer app. Never print the API key.

Reads app/src/content/answers.json. For each id, speaks text.sw and text.en.
Loads ELEVENLABS_API_KEY from app/backend/.env with python-dotenv when that
file exists. If the key is absent, exits 0 and writes no audio.

Output: app/public/audio/<lang>/<id>.mp3
Target: mono, 22050 Hz, 64 kbps.
Manifest: app/public/audio/manifest.json
Clips whose text hash is unchanged are skipped.

Does not call the network when the key is absent.
Confirm the model still lists Swahili (swa) before a real render:
https://elevenlabs.io/docs/overview/models
Default model is eleven_multilingual_v2, which lists swa. Override with
ELEVENLABS_MODEL_ID. One voice per language, from ELEVENLABS_VOICE_ID_SW
and ELEVENLABS_VOICE_ID_EN. If only one of those is set, it is used for both.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANSWERS_PATH = ROOT / "src" / "content" / "answers.json"
ENV_PATH = ROOT / "backend" / ".env"
AUDIO_DIR = ROOT / "public" / "audio"
MANIFEST_PATH = AUDIO_DIR / "manifest.json"

# Newest documented multilingual model that lists Swahili (swa), as of the
# brief. A human should confirm the current model list before spending credits.
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
SAMPLE_RATE_HZ = 22050
BITRATE_KBPS = 64
LANGS = ("sw", "en")


def load_local_env() -> None:
    """Load app/backend/.env if python-dotenv and the file are both present."""
    if not ENV_PATH.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ENV_PATH)


def redact(text: str, secret: str) -> str:
    if secret and secret in text:
        return text.replace(secret, "[redacted]")
    return text


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_answers() -> list[dict]:
    data = json.loads(ANSWERS_PATH.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        rows = []
        for key, item in data.items():
            if key.startswith("_") or not isinstance(item, dict):
                continue
            row = dict(item)
            row.setdefault("id", key)
            rows.append(row)
        return rows
    raise SystemExit("answers.json must be an array or an object keyed by id.")


def load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        return {"clips": []}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"clips": []}
    if not isinstance(data, dict):
        return {"clips": []}
    data.setdefault("clips", [])
    return data


def clip_key(answer_id: str, lang: str) -> str:
    return f"{lang}/{answer_id}"


def previous_hashes(manifest: dict) -> dict[str, str]:
    found: dict[str, str] = {}
    for clip in manifest.get("clips", []):
        if not isinstance(clip, dict):
            continue
        answer_id = clip.get("id")
        lang = clip.get("lang")
        digest = clip.get("text_hash")
        if answer_id and lang and digest:
            found[clip_key(str(answer_id), str(lang))] = str(digest)
    return found


def voice_for(lang: str) -> str | None:
    per_lang = {
        "sw": os.environ.get("ELEVENLABS_VOICE_ID_SW", "").strip(),
        "en": os.environ.get("ELEVENLABS_VOICE_ID_EN", "").strip(),
    }
    shared = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
    chosen = per_lang.get(lang) or shared
    if chosen:
        return chosen
    other = per_lang["en"] if lang == "sw" else per_lang["sw"]
    return other or None


def spoken_text(entry: dict, lang: str) -> str | None:
    text = entry.get("text") or {}
    if not isinstance(text, dict):
        return None
    value = text.get(lang)
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def ffprobe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    raw = result.stdout.strip()
    try:
        return round(float(raw), 3)
    except ValueError:
        return None


def to_target_mp3(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE_HZ),
            "-b:a",
            f"{BITRATE_KBPS}k",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def synthesise(text: str, voice_id: str, model_id: str, key: str, dest: Path) -> None:
    """Call ElevenLabs, then transcode to mono 22050 Hz 64 kbps. Key is never printed."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.75},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = redact(f"ElevenLabs HTTP {exc.code}: {body[:300]}", key)
        raise SystemExit(message) from exc
    except urllib.error.URLError as exc:
        message = redact(f"ElevenLabs request failed: {exc.reason}", key)
        raise SystemExit(message) from exc

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as handle:
        tmp_path = Path(handle.name)
        handle.write(audio)
    try:
        to_target_mp3(tmp_path, dest)
    finally:
        tmp_path.unlink(missing_ok=True)


def collect_jobs(answers: list[dict]) -> list[tuple[str, str, str]]:
    jobs: list[tuple[str, str, str]] = []
    for entry in answers:
        answer_id = str(entry.get("id") or "").strip()
        if not answer_id:
            continue
        for lang in LANGS:
            text = spoken_text(entry, lang)
            if text:
                jobs.append((answer_id, lang, text))
    return jobs


def main() -> int:
    load_local_env()
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        print(
            "Audio skipped because ELEVENLABS_API_KEY is absent. No clips were rendered."
        )
        return 0

    missing_voice = [lang for lang in LANGS if not voice_for(lang)]
    if missing_voice:
        print(
            "Audio skipped because a voice id is absent. "
            "Set ELEVENLABS_VOICE_ID_SW and ELEVENLABS_VOICE_ID_EN. No clips were rendered."
        )
        return 0

    if not ANSWERS_PATH.is_file():
        print(f"Audio skipped because {ANSWERS_PATH} is missing.")
        return 0

    ffmpeg = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
    )
    if ffmpeg.returncode != 0:
        print("Audio skipped because ffmpeg is missing. No clips were rendered.")
        return 0

    model_id = os.environ.get("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID).strip() or DEFAULT_MODEL_ID
    answers = load_answers()
    jobs = collect_jobs(answers)
    manifest = load_manifest()
    known = previous_hashes(manifest)
    old_by_key = {}
    for clip in manifest.get("clips", []):
        if isinstance(clip, dict) and clip.get("id") and clip.get("lang"):
            old_by_key[clip_key(str(clip["id"]), str(clip["lang"]))] = clip

    new_clips = []
    rendered = 0
    skipped = 0
    for answer_id, lang, text in jobs:
        digest = text_hash(text)
        key_name = clip_key(answer_id, lang)
        dest = AUDIO_DIR / lang / f"{answer_id}.mp3"
        previous = old_by_key.get(key_name)
        if (
            previous
            and known.get(key_name) == digest
            and dest.is_file()
        ):
            new_clips.append(previous)
            skipped += 1
            continue
        voice_id = voice_for(lang)
        assert voice_id is not None
        synthesise(text, voice_id, model_id, key, dest)
        new_clips.append(
            {
                "id": answer_id,
                "lang": lang,
                "path": f"{lang}/{answer_id}.mp3",
                "bytes": dest.stat().st_size,
                "duration": ffprobe_duration(dest),
                "engine": "elevenlabs",
                "model": model_id,
                "text_hash": digest,
            }
        )
        rendered += 1

    total_bytes = sum(int(clip.get("bytes") or 0) for clip in new_clips)
    out = {
        "format": {
            "container": "mp3",
            "channels": 1,
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "bitrate_kbps": BITRATE_KBPS,
        },
        "engine": "elevenlabs",
        "model": model_id,
        "clips": new_clips,
        "total_bytes": total_bytes,
    }
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Audio render finished. Rendered {rendered}, skipped {skipped} unchanged. "
        f"Manifest: {MANIFEST_PATH}."
    )
    if total_bytes > 4 * 1024 * 1024:
        print("Warning: audio total is over 4 MB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
