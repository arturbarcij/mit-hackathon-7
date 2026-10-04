# EC4 results: MMS-TTS fallback audio bank

Date: 3 Oct 2026, late evening. Lane: engine-cowork helper EC4.

## Outcome in one line

No clips were rendered. The model weights could not be downloaded from this environment. Everything else is built and tested, so the render is a one-command job on any machine that can reach huggingface.co.

## What is blocked, exactly

The egress proxy denies the CONNECT for every host that serves the weights. The denial is an organisation policy 403, not a timeout.

| Host | Result (container) | Result (Arthur's Cowork VM) |
|---|---|---|
| huggingface.co | `CONNECT tunnel failed, response 403` | `Received HTTP code 403 from proxy after CONNECT` |
| hf.co, cdn-lfs.huggingface.co, cdn-lfs-us-1.huggingface.co | 403 | not tested |
| hf-mirror.com | 403 | not tested |
| dl.fbaipublicfiles.com (Meta's original MMS checkpoints) | 403 | not tested |
| www.modelscope.cn | 403 | not tested |
| download.pytorch.org (CPU wheel index) | 403 | not tested |
| github.com, raw.githubusercontent.com, pypi.org | open | github.com open |

transformers error, both models:
`OSError: Can't load the configuration of 'facebook/mms-tts-swh'. If you were trying to load it from 'https://huggingface.co/models', make sure you don't have a local directory with the same name...` (same text for `facebook/mms-tts-kik`). The proxy log shows 13 rejected connections to huggingface.co:443 during that attempt.

A web search found no GitHub mirror of either checkpoint. The GitHub API in this session is scoped to configured repositories, so repository search is not available either.

## What was installed and tested

- torch 2.14.1 from PyPI (the CPU-only index is blocked; the PyPI wheel runs on CPU fine), transformers 5.18.0, scipy, numpy. ffmpeg present at /usr/bin/ffmpeg.
- `render.py` runs end to end in `--dry-run` mode against the real `answers.json`: 37 manifest rows (28 sw, 9 kik), text preprocessing applied, no audio.
- The wav write, ffmpeg mp3 encode (libmp3lame, mono, 32 kbps, 16 kHz), peak and silence stats, and the 3-clip concat for spot checks were exercised with a synthetic 1.5 s tone. All pass. A 1.5 s clip came out at 6561 bytes, so the codec costs about 4.4 KB per second.

## Counts

- Swahili: 28 answers have `text.sw`. All queued.
- Kikuyu: 9 answers have `text.kik`, not 8. The ninth is `language_name` ("Gĩkũyũ"). It is in the queue; drop it if the UI does not voice the language name.
- Nudges (3): the content-voice brief says SMS only, no audio. They are still in the Swahili queue because the lane brief asked for all 28, and each is flagged `nudge_is_sms_only_in_spec` in the manifest. Delete `sw/nudge_*.mp3` after rendering if you want to follow the brief.

## Budget estimate (not measured)

At 32 kbps mono the codec costs about 4.4 KB per second. Swahili text averages about 105 characters per answer. MMS Swahili usually speaks at roughly 0.07 to 0.09 s per character, so about 8 s per clip, about 225 s in total, about 1.0 MB. Kikuyu: 9 clips, about 70 s, about 0.3 MB. Expected total about 1.3 MB against the 4 MB budget for all audio. ElevenLabs Swahili at 48 to 64 kbps would roughly double the Swahili share and still fit.

## Tokenizer findings

Not verified, because the tokenizers could not be downloaded. What is known and what the script does:

- MMS tokenizers are character level. The script normalises to NFC and leaves case to the tokenizer.
- Kikuyu ĩ and ũ: `render.py` reads the vocab at run time. If both characters are in the vocab it keeps them (`tilde_strategy: keep`). If not, it maps ĩ to i and ũ to u and records every mapping in `substitutions` (`tilde_strategy: map`). The choice is written to `manifest.json` under `report.tokenizer.kik`. Every clip also records `unk_tokens` so a bad strategy is visible without listening. The person who runs it should listen to `how_to_pick_leaves` under both strategies once if `unk_tokens` is non-zero; the `--force` flag re-renders.
- Digits: only two appear in the bank. "10" in `how_to_pick_leaves` (sw and kik) and `nudge_leaf_check` (sw); "1" in `nudge_officer_visit` (sw). Mapped to kumi, ikũmi, moja. Any other digit is left in place and flagged `unmapped_digits`.
- Seed: `torch.manual_seed(42)` before each clip. VITS `speaking_rate` and `noise_scale` left at model defaults.

## Quality checks built in

Per clip: bytes, duration, chars, seconds per character (flag outside 0.04 to 0.20), peak dBFS, silence ratio (20 ms frames under -40 dBFS), unknown-token count. Spot-check files: `_work/spot_<lang>.mp3`, `_work/spot_<lang>_1.mp3`, `_work/spot_<lang>_2.mp3` (3 clips each), with the first copied to `SPOTCHECK_<lang>.mp3`.

## Model download sizes and render time

Not measured here. From the model cards, each MMS-TTS checkpoint is about 145 MB (safetensors) plus a few KB of config and vocab, so about 290 MB for both. CPU render time for 37 short clips is expected to be well under five minutes on a laptop; the script records it per language in `report.render_seconds`.

## How to unblock

Run on any machine with access to huggingface.co (Arthur's laptop outside the Cowork VM proxy should work):

```
pip install torch transformers scipy numpy
python3 render.py app/src/content/answers.json --out <this folder> --hf-home <cache dir>
```

Or download once and copy the cache folder (`hf/hub/models--facebook--mms-tts-swh` and `...-kik`) into `_work/hf` here, then re-run the same command. The script skips clips whose text hash has not changed, so later text fixes re-render only what moved.
