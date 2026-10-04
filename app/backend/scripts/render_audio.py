"""Render the fixed answer bank to audio, once, at build time (C3).

Swahili and English: ElevenLabs, model eleven_v3. Swahili is NOT supported by Multilingual v2 or
Flash v2.5, only by Eleven v3 and later (https://elevenlabs.io/docs/overview/models, checked 3 Oct 2026).
Kikuyu: Meta MMS-TTS facebook/mms-tts-kik, run locally (CC BY-NC 4.0, non-commercial). ElevenLabs has no Kikuyu.

Output: app/public/audio/<lang>/<answer_id>.mp3 (mono, 22.05 kHz, 48 kbit/s) and app/public/audio/manifest.json.
Nudges (kind == "nudge") are SMS text only and get no audio. Result cards speak text + not_sure.
Re-runnable: a clip is skipped when its text, engine, model and voice hash is unchanged and the file exists.
No API key ever ships to the client: this script runs on the build machine only.

Usage (from MIT_Hackathon_7/ or anywhere):
  python app/backend/scripts/render_audio.py --dry-run              # what would render, character count
  python app/backend/scripts/render_audio.py --list-voices          # pick a voice id for ELEVENLABS_VOICE_ID_SW
  python app/backend/scripts/render_audio.py --langs sw             # Swahili only
  python app/backend/scripts/render_audio.py --langs kik            # Kikuyu only (needs torch + transformers)
  python app/backend/scripts/render_audio.py --only rust_low,healthy_all --force

Needs in app/backend/.env: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID_SW (and ELEVENLABS_VOICE_ID_EN for English).
Needs ffmpeg on PATH, or: pip install imageio-ffmpeg
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
ANSWERS = APP / "src" / "content" / "answers.json"
AUDIO = APP / "public" / "audio"
MANIFEST = AUDIO / "manifest.json"
ENV = APP / "backend" / ".env"

BUDGET_BYTES = 4 * 1024 * 1024
SAMPLE_RATE = 22050
BITRATE = "48k"
EL_MODEL = "eleven_v3"
EL_URL = "https://api.elevenlabs.io/v1"
MMS_MODEL = "facebook/mms-tts-kik"
NO_AUDIO_KINDS = {"nudge"}


# ---------- helpers ----------

def load_env() -> dict[str, str]:
    env = dict(os.environ)
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", line)
            if m and m.group(2) and not os.environ.get(m.group(1)):
                env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return env


def find_ffmpeg() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def speakable(answer: dict, lang: str) -> str | None:
    text = (answer.get("text") or {}).get(lang)
    if not text:
        return None
    ns = (answer.get("not_sure") or {}).get(lang)
    return f"{text.strip()} {ns.strip()}" if ns else text.strip()


def clip_hash(engine: str, model: str, voice: str, text: str) -> str:
    return hashlib.sha256(f"{engine}|{model}|{voice}|{text}".encode("utf-8")).hexdigest()


def to_mp3(ffmpeg: str, src: Path, dst: Path) -> float | None:
    """Re-encode any audio file to mono 22.05 kHz CBR mp3. Returns duration in seconds if ffmpeg reports it."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-codec:a", "libmp3lame", "-b:a", BITRATE, "-map_metadata", "-1", str(dst)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {src.name}: {proc.stderr[-400:]}")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", proc.stderr)
    return round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)), 2) if m else None


def http(method: str, url: str, key: str, body: dict | None = None, accept: str = "application/json") -> bytes:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "xi-api-key": key, "Content-Type": "application/json", "Accept": accept})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:500]
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from None
    raise RuntimeError("unreachable")


# ---------- engines ----------

class ElevenLabs:
    engine = "elevenlabs"
    model = EL_MODEL
    licence = "ElevenLabs terms (paid plan output)"

    def __init__(self, key: str, voices: dict[str, str]):
        self.key, self.voices = key, voices
        self.lang_code_ok = True

    def voice(self, lang: str) -> str:
        return self.voices.get(lang, "")

    def render(self, text: str, lang: str, out: Path) -> None:
        url = f"{EL_URL}/text-to-speech/{self.voice(lang)}?output_format=mp3_44100_64"
        body = {"text": text, "model_id": self.model}
        if self.lang_code_ok:
            body["language_code"] = lang
        try:
            audio = http("POST", url, self.key, body, accept="audio/mpeg")
        except RuntimeError as e:
            if self.lang_code_ok and "language" in str(e).lower():
                self.lang_code_ok = False  # model rejects language_code; it auto-detects
                body.pop("language_code")
                audio = http("POST", url, self.key, body, accept="audio/mpeg")
            else:
                raise
        out.write_bytes(audio)


class MMS:
    engine = "meta-mms-tts"
    model = MMS_MODEL
    licence = "CC-BY-NC-4.0"
    VOICE = "mms-single-speaker"

    def __init__(self):
        try:
            import torch  # noqa: F401
            from transformers import AutoTokenizer, VitsModel  # noqa: F401
        except ImportError:
            sys.exit("Kikuyu needs torch and transformers: pip install torch transformers (the conda env 'jani' has torch)")
        import torch
        from transformers import AutoTokenizer, VitsModel
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MMS_MODEL)
        self.net = VitsModel.from_pretrained(MMS_MODEL).eval()
        self.vocab = set(self.tok.get_vocab().keys())

    def voice(self, lang: str) -> str:
        return self.VOICE

    def unknown_chars(self, text: str) -> set[str]:
        norm = text.lower()
        return {c for c in norm if c not in self.vocab and not c.isspace()}

    def render(self, text: str, lang: str, out: Path) -> None:
        unk = self.unknown_chars(text)
        if unk:
            print(f"    warn: MMS vocab drops characters {sorted(unk)}; listen to this clip", flush=True)
        inputs = self.tok(text, return_tensors="pt")
        self.torch.manual_seed(0)  # VITS is stochastic; fix it so re-runs match
        with self.torch.no_grad():
            wav = self.net(**inputs).waveform[0].cpu().numpy()
        pcm = (wav.clip(-1, 1) * 32767).astype("<i2").tobytes()
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.net.config.sampling_rate)
            w.writeframes(pcm)


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--langs", default="sw,en,kik")
    ap.add_argument("--only", default="", help="comma-separated answer ids")
    ap.add_argument("--force", action="store_true", help="re-render even if the hash is unchanged")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    env = load_env()
    key = env.get("ELEVENLABS_API_KEY", "")

    if a.list_voices:
        if not key:
            sys.exit("ELEVENLABS_API_KEY is empty in app/backend/.env")
        voices = json.loads(http("GET", f"{EL_URL}/voices", key))["voices"]
        for v in voices:
            labels = v.get("labels") or {}
            print(f"{v['voice_id']}  {v['name']:<28} {labels.get('accent', ''):<14} {labels.get('language', '')}  {labels.get('gender', '')}")
        print("\nPick one calm, clear voice. A Kenyan Swahili voice from the Voice Library is best (add it to 'My voices' first).")
        return 0

    langs = [l.strip() for l in a.langs.split(",") if l.strip()]
    only = {i.strip() for i in a.only.split(",") if i.strip()}
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    if isinstance(answers, dict):
        answers = list(answers.values())

    old = {}
    if MANIFEST.exists():
        for c in json.loads(MANIFEST.read_text(encoding="utf-8")).get("clips", []):
            old[(c["id"], c["lang"])] = c

    # Plan
    plan = []
    for ans in answers:
        if ans.get("kind") in NO_AUDIO_KINDS or (only and ans["id"] not in only):
            continue
        for lang in langs:
            text = speakable(ans, lang)
            if text:
                plan.append((ans, lang, text))

    el_chars = sum(len(t) for _, l, t in plan if l != "kik")
    print(f"{len(plan)} clips planned ({', '.join(langs)}); ElevenLabs characters if all render: {el_chars}")
    if a.dry_run:
        for ans, lang, text in plan:
            print(f"  {lang:<3} {ans['id']:<24} {len(text):>4} chars")
        return 0

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit("ffmpeg not found. Install it or run: pip install imageio-ffmpeg")

    engines: dict[str, object] = {}
    if any(l != "kik" for l in langs):
        voices = {"sw": env.get("ELEVENLABS_VOICE_ID_SW", ""), "en": env.get("ELEVENLABS_VOICE_ID_EN", "") or env.get("ELEVENLABS_VOICE_ID_SW", "")}
        if not key or not voices["sw"]:
            sys.exit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID_SW in app/backend/.env (see --list-voices)")
        engines["el"] = ElevenLabs(key, voices)

    clips = dict(old)
    rendered = skipped = failed = 0
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        for ans, lang, text in plan:
            if lang == "kik":
                h = clip_hash(MMS.engine, MMS.model, MMS.VOICE, text)
            else:
                eng = engines["el"]
                h = clip_hash(eng.engine, eng.model, eng.voice(lang), text)
            out = AUDIO / lang / f"{ans['id']}.mp3"
            prev = old.get((ans["id"], lang))
            if not a.force and prev and prev.get("text_sha256") == h and out.exists():
                skipped += 1
                continue
            if lang == "kik":  # load the model only when a Kikuyu clip actually needs rendering
                if "mms" not in engines:
                    print("loading MMS-TTS Kikuyu (first run downloads about 145 MB)...", flush=True)
                    engines["mms"] = MMS()
                eng = engines["mms"]
            raw = tmp / f"{lang}_{ans['id']}.{'wav' if lang == 'kik' else 'mp3'}"
            try:
                print(f"  render {lang} {ans['id']}", flush=True)
                eng.render(text, lang, raw)
                dur = to_mp3(ffmpeg, raw, out)
            except Exception as e:  # keep going; report at the end
                print(f"  FAILED {lang} {ans['id']}: {e}", flush=True)
                failed += 1
                continue
            clips[(ans["id"], lang)] = {
                "id": ans["id"], "lang": lang, "file": f"/audio/{lang}/{ans['id']}.mp3",
                "bytes": out.stat().st_size, "duration_s": dur,
                "engine": eng.engine, "model": eng.model, "voice": eng.voice(lang), "licence": eng.licence,
                "synthetic_voice": True,
                "review_status": (ans.get("review_status") or {}).get(lang, "draft" if lang != "en" else "source_text"),
                "text_sha256": h, "rendered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            rendered += 1

    # Drop manifest rows whose file no longer exists
    clips = {k: v for k, v in clips.items() if (AUDIO / v["lang"] / f"{v['id']}.mp3").exists()}
    total = sum((AUDIO / v["lang"] / f"{v['id']}.mp3").stat().st_size for v in clips.values())
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "format": f"mp3 mono {SAMPLE_RATE} Hz {BITRATE}bit/s",
        "budget_bytes": BUDGET_BYTES, "total_bytes": total,
        "note": "All voices are synthetic. Kikuyu (MMS-TTS, CC BY-NC 4.0) is a machine voice pending native speaker review.",
        "clips": sorted(clips.values(), key=lambda c: (c["lang"], c["id"])),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\nrendered {rendered}, skipped {skipped} (unchanged), failed {failed}")
    print(f"audio total {total / 1024:.0f} KB of {BUDGET_BYTES / 1024:.0f} KB budget -> {MANIFEST.relative_to(APP)}")
    if total > BUDGET_BYTES:
        print("OVER BUDGET: lower BITRATE to 32k or drop English audio")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
