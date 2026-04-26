#!/usr/bin/env python3
"""
generate_lofi_runpod_clean.py
=============================
Cleaner ACE-Step 1.5 lofi generator for RunPod.
Imports prompts from prompts.py so musical content can be
managed separately from generation logic.
"""

import os
import sys
import time
import random
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

try:
    import toml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "toml", "-q"], check=False)
    import toml

from prompts import get_prompt_pack, list_prompt_packs

# -- Paths -------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR   = SCRIPT_DIR / "ACE-Step-1.5"
CLI_PY     = REPO_DIR / "cli.py"
CLIPS_DIR  = SCRIPT_DIR / "acestep_clips"
OUTPUT_DIR = SCRIPT_DIR / "output"

FINAL_MP3  = OUTPUT_DIR / "lofi_album_clean_master.mp3"
FFMPEG     = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE    = shutil.which("ffprobe") or "ffprobe"
MAX_SAFE_DURATION = 480

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# -- Formatting constants ----------------------------------------------------
DASH_LINE = "\u2500" * 68
EQ_LINE   = "=" * 68

# -- Duration defaults -------------------------------------------------------
FULL_DURATION = 240
TEST_DURATION = 60

# -- Disable stale instruction.txt override ----------------------------------
INSTRUCTION_TXT = REPO_DIR / "instruction.txt"
INSTRUCTION_BAK = REPO_DIR / "instruction.txt.bak"
if INSTRUCTION_TXT.exists() and not INSTRUCTION_BAK.exists():
    print("Warning: Renaming stale override: " + str(INSTRUCTION_TXT))
    INSTRUCTION_TXT.rename(INSTRUCTION_BAK)

# -- Sanity checks -----------------------------------------------------------
if not CLI_PY.exists():
    print("ERROR: ACE-Step repo not found at " + str(REPO_DIR))
    print("  Edit REPO_DIR in this script if your folder name differs.")
    sys.exit(1)

if shutil.which("ffmpeg") is None:
    print("ERROR: ffmpeg not found. Install with:")
    print("  apt-get update && apt-get install -y ffmpeg")
    sys.exit(1)


# -- Helper functions --------------------------------------------------------

def write_track_toml(
    track_dir: Path,
    prompt: str,
    duration: int,
    steps: int,
    guidance: float,
    shift: float,
    seed: int,
    thinking: bool,
) -> Path:
    """Write a per-track TOML config for cli.py."""
    config = {
        "project_root":    str(REPO_DIR),
        "checkpoint_dir":  str(REPO_DIR / "checkpoints"),
        "save_dir":        str(track_dir),
        "config_path":     "acestep-v15-sft",
        "lm_model_path":   "acestep-5Hz-lm-0.6B",
        "backend":         "auto",
        "device":          "auto",
        "task_type":       "text2music",
        "caption":         prompt,
        "lyrics":          "[Instrumental]",
        "instrumental":    True,
        "duration":        float(duration),
        "inference_steps": steps,
        "guidance_scale":  guidance,
        "shift":           shift,
        "seed":            seed,
        "thinking":        thinking,
        "use_cot_metas":   thinking,
        "use_cot_caption": thinking,
        "use_cot_language": False,
        "batch_size":      1,
        "audio_format":    "flac",
        "use_random_seed": (seed < 0),
    }
    track_dir.mkdir(parents=True, exist_ok=True)
    toml_path = track_dir / "config.toml"
    with open(toml_path, "w", encoding="utf-8") as f:
        toml.dump(config, f)
    return toml_path


def find_output_audio(track_dir: Path) -> Optional[Path]:
    """Find the generated audio file in a track directory."""
    for ext in ("*.flac", "*.wav", "*.mp3"):
        matches = sorted(track_dir.glob(ext))
        if matches:
            return matches[-1]
    return None


def probe_duration(audio_path: Path) -> Optional[float]:
    """Get the duration of an audio file via ffprobe."""
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def generate_track(
    track_num: int,
    total: int,
    prompt: str,
    duration: int,
    steps: int,
    guidance: float,
    shift: float,
    seed_base: int,
    thinking: bool,
) -> Optional[Path]:
    """Generate a single track using ACE-Step cli.py."""
    track_dir = CLIPS_DIR / f"track_{track_num:03d}"

    # Force true random seed per track
    if seed_base < 0:
        seed = random.randint(0, 2**31 - 1)
    else:
        seed = seed_base + track_num

    # Skip if already generated
    existing = find_output_audio(track_dir)
    if existing and existing.stat().st_size > 100_000:
        size_mb = existing.stat().st_size / 1_048_576
        print(f"  [skip] Track {track_num + 1}/{total} already exists ({size_mb:.1f} MB)")
        return existing

    print("")
    print(DASH_LINE)
    print(f"  Track {track_num + 1}/{total}")
    print(f"  Prompt   : {prompt[:90]}...")
    print(f"  Duration : {duration}s | Steps: {steps} | Guidance: {guidance} | Shift: {shift}")
    print(f"  Seed     : {seed} | Thinking: {thinking}")
    print(DASH_LINE)

    toml_path = write_track_toml(
        track_dir=track_dir,
        prompt=prompt,
        duration=duration,
        steps=steps,
        guidance=guidance,
        shift=shift,
        seed=seed,
        thinking=thinking,
    )

    t0 = time.time()
    result = subprocess.run(
        [sys.executable, str(CLI_PY), "-c", str(toml_path)],
        cwd=str(REPO_DIR),
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  FAIL: Track {track_num + 1} exited with code {result.returncode}")
        return None

    audio_path = find_output_audio(track_dir)
    if not audio_path:
        print(f"  FAIL: Track {track_num + 1} -- no audio file found in {track_dir}")
        return None

    size_mb = audio_path.stat().st_size / 1_048_576
    actual_dur = probe_duration(audio_path)
    dur_str = f"{actual_dur:.1f}s" if actual_dur else "unknown"
    print(f"  OK: Track {track_num + 1} done in {elapsed:.0f}s -- {dur_str} -- {size_mb:.1f} MB")

    if actual_dur is not None and abs(actual_dur - duration) > 15:
        print(f"  WARNING: requested {duration}s but file is {actual_dur:.1f}s")

    return audio_path


def concat_to_mp3(clip_paths: List[Path]) -> None:
    """Concatenate clips into one final MP3 with light mastering EQ."""
    print("")
    print(EQ_LINE)
    print("  Concatenating tracks into final MP3...")
    print(EQ_LINE)
    print("")

    list_file = CLIPS_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            line = "file '" + str(p.resolve()) + "'\n"
            f.write(line)

    audio_filter = (
        "highpass=f=28,"
        "equalizer=f=220:t=q:w=1.0:g=-1.5,"
        "equalizer=f=3500:t=q:w=1.0:g=0.5,"
        "lowpass=f=13500,"
        "loudnorm=I=-14:TP=-1.5:LRA=11"
    )

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-af", audio_filter,
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        "-id3v2_version", "3",
        "-metadata", "title=Lofi Hip Hop Mix - Clean Master",
        "-metadata", "artist=ACE-Step 1.5 AI",
        "-metadata", "album=YouTube Lofi Channel",
        str(FINAL_MP3),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: ffmpeg concat failed:")
        print(result.stderr)
        sys.exit(1)

    size_mb = FINAL_MP3.stat().st_size / 1_048_576
    print(f"  Final MP3: {FINAL_MP3}")
    print(f"  Size: {size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Generate cleaner lofi music with ACE-Step 1.5 (RunPod/CUDA)"
    )
    parser.add_argument("--test", action="store_true",
                        help="Quick test: 2 tracks at 60s each")
    parser.add_argument("--tracks", type=int, default=12,
                        help="Number of tracks (default: 12)")
    parser.add_argument("--duration", type=int, default=None,
                        help="Seconds per track")
    parser.add_argument("--list", action="store_true",
                        help="Print prompt packs and exit")
    parser.add_argument("--prompt-pack", type=str, default="diverse_lofi",
                        help="Prompt pack name from prompts.py")
    parser.add_argument("--steps", type=int, default=80,
                        help="Inference steps (default: 80)")
    parser.add_argument("--guidance", type=float, default=5.0,
                        help="CFG guidance scale (default: 5.0)")
    parser.add_argument("--shift", type=float, default=1.9,
                        help="Noise shift (default: 1.9)")
    parser.add_argument("--seed-base", type=int, default=-1,
                        help="Base seed, -1 for random per track")
    parser.add_argument("--no-thinking", action="store_true",
                        help="Disable ACE-Step thinking/reasoning")
    args = parser.parse_args()

    # -- List mode --
    if args.list:
        print("")
        print("Available prompt packs:")
        print("")
        for pack in list_prompt_packs():
            prompts = get_prompt_pack(pack)
            print(f"  {pack} ({len(prompts)} prompts)")
            for i, p in enumerate(prompts, 1):
                print(f"    {i}. {p[:90]}...")
            print()
        return

    # -- Resolve settings --
    duration = args.duration or (TEST_DURATION if args.test else FULL_DURATION)
    if duration > MAX_SAFE_DURATION:
        print(f"  WARNING: {duration}s exceeds safe max ({MAX_SAFE_DURATION}s) -- clamping.")
        duration = MAX_SAFE_DURATION

    prompt_pack = get_prompt_pack(args.prompt_pack)
    num_tracks = 2 if args.test else args.tracks
    thinking = not args.no_thinking
    total_min = (num_tracks * duration) // 60

    # Shuffle prompts, cycle if more tracks than prompts
    shuffled = prompt_pack.copy()
    random.shuffle(shuffled)
    prompts = [shuffled[i % len(shuffled)] for i in range(num_tracks)]

    print("")
    print(EQ_LINE)
    print("  ACE-Step 1.5 Cleaner Lofi Generator")
    print(EQ_LINE)
    print(f"  Prompt pack: {args.prompt_pack} ({len(prompt_pack)} prompts)")
    print(f"  Tracks     : {num_tracks}")
    print(f"  Duration   : {duration}s each")
    print(f"  Total      : ~{total_min} minutes")
    print(f"  Steps      : {args.steps}")
    print(f"  Guidance   : {args.guidance}")
    print(f"  Shift      : {args.shift}")
    print(f"  Thinking   : {thinking}")
    print(f"  Output     : {FINAL_MP3}")
    print(EQ_LINE)
    print("")

    # -- Generate tracks --
    clip_paths: List[Path] = []
    for i, prompt in enumerate(prompts):
        path = generate_track(
            track_num=i,
            total=num_tracks,
            prompt=prompt,
            duration=duration,
            steps=args.steps,
            guidance=args.guidance,
            shift=args.shift,
            seed_base=args.seed_base,
            thinking=thinking,
        )
        if path:
            clip_paths.append(path)

    if not clip_paths:
        print("")
        print("  ERROR: No tracks generated. Check errors above.")
        sys.exit(1)

    # -- Concatenate --
    concat_to_mp3(clip_paths)

    total_dur = sum(probe_duration(p) or 0 for p in clip_paths)
    print("")
    print(EQ_LINE)
    total_dur_min = total_dur / 60
    print(f"  DONE! {len(clip_paths)} tracks -> ~{total_dur_min:.1f} minutes total")
    print(f"  MP3: {FINAL_MP3}")
    print(EQ_LINE)
    print("")


if __name__ == "__main__":
    main()
