r"""Build one game's Howler audio sprite from its ingested clips (docs/10 plan v3.3, slice 10.6c).

Usage (from stake\):  .venv-assets\Scripts\python.exe tools\assets\audio.py --game <gameId>

Input:  skins\<skin>\audio\<slot>.ogg (tools\assets\ingest.py), mapped to the core sound names by the
        catalogue's `feeds` (core\assets\slots.v1.json). Slots with pitchSteps give names ending _1.._5
        rising pitch.
Output: build\<id>\web\static-gen\assets\audio\sounds.{ogg,m4a,json} (gen_web_static.py layer 4).
The sprite starts with a 100 ms silent segment; every sound name the skin has not filled points at it,
so a game with no audio at all still loads and plays silently (no console errors).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, Catalog  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

SILENCE_MS = 100
GAP_MS = 500
PITCH_STEP = 1.06
RATE = 44100
BITEXACT = ["-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact"]


def run(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def duration_ms(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out) * 1000


def main():
    gid = game_arg()
    cat = Catalog(gid)
    out_dir = cat.game.gen_web / "static-gen" / "assets" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_slots = [s for s in cat.slots if s["kind"] in ("music", "sfx")]
    sprite, config = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        silence = tmp / "000_silence.wav"
        run("-f", "lavfi", "-i", f"anullsrc=r={RATE}:cl=stereo", "-t", str(SILENCE_MS / 1000), "-c:a", "pcm_s16le", str(silence))
        parts.append(silence)
        offset = SILENCE_MS + GAP_MS
        filled = 0
        for slot in sorted(audio_slots, key=lambda s: s["id"]):
            src = cat.game.skin / "audio" / f"{slot['id']}.ogg"
            loop = slot["kind"] == "music" or bool(slot.get("loop"))
            for name in slot.get("feeds", []):
                if not src.exists():
                    sprite[name] = [0, SILENCE_MS, loop]
                    config[name] = {"volume": 1}
                    continue
                pitch = 1.0
                if slot.get("pitchSteps") and name[-2] == "_" and name[-1].isdigit():
                    pitch = PITCH_STEP ** (int(name[-1]) - 1)
                clip = tmp / f"{len(parts):03d}_{name}.wav"
                af = f"asetrate={RATE}*{pitch:.6f},aresample={RATE}" if pitch != 1.0 else f"aresample={RATE}"
                run("-i", str(src), "-af", af, "-ac", "2", "-c:a", "pcm_s16le", str(clip))
                gap = tmp / f"{len(parts):03d}_gap.wav"
                run("-f", "lavfi", "-i", f"anullsrc=r={RATE}:cl=stereo", "-t", str(GAP_MS / 1000), "-c:a", "pcm_s16le", str(gap))
                dur = duration_ms(clip)
                sprite[name] = [round(offset), round(dur, 3), loop]
                config[name] = {"volume": 1}
                parts += [clip, gap]
                offset += dur + GAP_MS
                filled += 1
        listing = tmp / "list.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        joined = tmp / "joined.wav"
        run("-f", "concat", "-safe", "0", "-i", str(listing), "-c:a", "pcm_s16le", str(joined))
        run("-i", str(joined), *BITEXACT, "-c:a", "libvorbis", "-q:a", "4", str(out_dir / "sounds.ogg"))
        run("-i", str(joined), *BITEXACT, "-c:a", "aac", "-b:a", "128k", str(out_dir / "sounds.m4a"))
    data = {"src": ["./assets/audio/sounds.ogg", "./assets/audio/sounds.m4a"], "sprite": dict(sorted(sprite.items())), "config": dict(sorted(config.items()))}
    (out_dir / "sounds.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"ok    build/{gid}/web/static-gen/assets/audio: {len(sprite)} sound names, {filled} from skin clips, "
          f"{len(sprite) - filled} on the silent segment")


if __name__ == "__main__":
    main()
