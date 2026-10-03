#!/usr/bin/env python3
"""Kikuyu clips, when a native-reviewed text exists. This script does not invent audio.

Model: facebook/mms-tts-kik (Meta MMS-TTS), via transformers VitsModel, on CPU.
Licence: CC-BY-NC-4.0 (non-commercial). Machine voice only.
Every clip is pending native speaker review before it may be shown as Kikuyu.

The eight answer ids still waiting for Kikuyu text:
how_to_pick_leaves, healthy_all, rust_high_pre_rains, too_many_unsure,
ask_officer, decision_act, decision_wait, decision_ask.

If transformers or ffmpeg is missing, this script exits 0 and writes nothing.
If answers.json has no Kikuyu text (kik is null or empty), it exits 0 and
writes nothing. It does not download a model and it does not synthesise
placeholder speech.

Output, once text exists and the tools exist:
app/public/audio/kik/<id>.mp3, mono, 22050 Hz, 64 kbps.
Manifest entries are merged into app/public/audio/manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANSWERS_PATH = ROOT / "src" / "content" / "answers.json"
AUDIO_DIR = ROOT / "public" / "audio"
MANIFEST_PATH = AUDIO_DIR / "manifest.json"
MODEL_ID = "facebook/mms-tts-kik"
LICENCE = "CC-BY-NC-4.0"
SAMPLE_RATE_HZ = 22050
BITRATE_KBPS = 64

PENDING_IDS = (
    "how_to_pick_leaves",
    "healthy_all",
    "rust_high_pre_rains",
    "too_many_unsure",
    "ask_officer",
    "decision_act",
    "decision_wait",
    "decision_ask",
)


def log(message: str) -> None:
    print(message)


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


def kikuyu_jobs(answers: list[dict]) -> list[tuple[str, str]]:
    jobs: list[tuple[str, str]] = []
    for entry in answers:
        answer_id = str(entry.get("id") or "").strip()
        text = entry.get("text") or {}
        if not answer_id or not isinstance(text, dict):
            continue
        value = text.get("kik")
        if isinstance(value, str) and value.strip():
            jobs.append((answer_id, value.strip()))
    return jobs


def tools_ready() -> bool:
    if shutil.which("ffmpeg") is None:
        log(
            "Kikuyu audio skipped because ffmpeg is missing. "
            f"No clips were invented. Model when used: {MODEL_ID}, licence {LICENCE}. "
            "Pending native speaker review."
        )
        return False
    try:
        import transformers  # noqa: F401
    except ImportError:
        log(
            "Kikuyu audio skipped because transformers is missing. "
            f"No clips were invented. Model when used: {MODEL_ID}, licence {LICENCE}. "
            "Pending native speaker review."
        )
        return False
    return True


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    try:
        return round(float(result.stdout.strip()), 3)
    except ValueError:
        return None


def write_mp3(waveform, sample_rate: int, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        wav_path = Path(handle.name)
    try:
        import scipy.io.wavfile as wavfile

        wavfile.write(wav_path, sample_rate, waveform)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav_path),
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
    finally:
        wav_path.unlink(missing_ok=True)


def synthesise(text: str, dest: Path) -> None:
    """Run MMS-TTS locally. Called only when Kikuyu text and tools both exist."""
    import numpy as np
    import torch
    from transformers import AutoTokenizer, VitsModel

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID)
    model.eval()
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform
    audio = output.squeeze().cpu().numpy()
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767.0).astype("int16")
    rate = int(getattr(model.config, "sampling_rate", 16000))
    write_mp3(pcm, rate, dest)


def main() -> int:
    if not ANSWERS_PATH.is_file():
        log(
            "Kikuyu audio skipped because answers.json is missing. "
            "No clips were invented. Pending native speaker review."
        )
        return 0

    answers = load_answers()
    jobs = kikuyu_jobs(answers)
    if not jobs:
        log(
            "Kikuyu audio skipped. No Kikuyu answer text is translated yet "
            "(translation_status.kik is not_translated, text.kik is null). "
            f"Pending native speaker review. Model when used: {MODEL_ID}, "
            f"licence {LICENCE}. This script does not invent audio. "
            "Core ids still needed: " + ", ".join(PENDING_IDS) + "."
        )
        return 0

    if not tools_ready():
        return 0

    manifest = load_manifest()
    kept = []
    for clip in manifest.get("clips", []):
        if isinstance(clip, dict) and clip.get("lang") != "kik":
            kept.append(clip)
    old_kik = {
        str(clip.get("id")): clip
        for clip in manifest.get("clips", [])
        if isinstance(clip, dict) and clip.get("lang") == "kik"
    }

    rendered = 0
    skipped = 0
    for answer_id, text in jobs:
        digest = text_hash(text)
        dest = AUDIO_DIR / "kik" / f"{answer_id}.mp3"
        previous = old_kik.get(answer_id)
        if previous and previous.get("text_hash") == digest and dest.is_file():
            kept.append(previous)
            skipped += 1
            continue
        synthesise(text, dest)
        kept.append(
            {
                "id": answer_id,
                "lang": "kik",
                "path": f"kik/{answer_id}.mp3",
                "bytes": dest.stat().st_size,
                "duration": ffprobe_duration(dest),
                "engine": MODEL_ID,
                "licence": LICENCE,
                "review": "pending native speaker review",
                "text_hash": digest,
            }
        )
        rendered += 1

    manifest["clips"] = kept
    manifest["kikuyu"] = {
        "model": MODEL_ID,
        "licence": LICENCE,
        "review": "pending native speaker review",
        "format": {
            "container": "mp3",
            "channels": 1,
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "bitrate_kbps": BITRATE_KBPS,
        },
    }
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log(
        f"Kikuyu render finished. Rendered {rendered}, skipped {skipped} unchanged. "
        "Pending native speaker review. Machine voice is not a native speaker."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
