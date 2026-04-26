#!/usr/bin/env python3
"""
generate_lofi_runpod_clean.py
=============================
Clearer / cleaner ACE-Step 1.5 lofi generator for RunPod

What changed vs your original:
- Prompts are less "degraded" and more "clean/chill"
- Slightly adjusted generation settings for clarity
- Gentle mastering pass at final export
- Optional seed base for reproducibility
- Outputs both final FLAC master and MP3
"""

import os
import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path

try:
    import toml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "toml", "-q"], check=False)
    import toml


# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
REPO_DIR     = SCRIPT_DIR / "ACE-Step-1.5"
CLI_PY       = REPO_DIR / "cli.py"
CLIPS_DIR    = SCRIPT_DIR / "acestep_clips"
OUTPUT_DIR   = SCRIPT_DIR / "output"

FINAL_FLAC   = OUTPUT_DIR / "lofi_album_clean_master.flac"
FINAL_MP3    = OUTPUT_DIR / "lofi_album_clean_master.mp3"

FFMPEG       = shutil.which("ffmpeg") or "ffmpeg"

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Sanity checks ──────────────────────────────────────────────────────────────
if not CLI_PY.exists():
    print(f"❌ ACE-Step repo not found at {REPO_DIR}")
    print("   Clone it with:")
    print("   git clone https://github.com/ACE-Step/ACE-Step-v1-5.git ACE-Step-1.5")
    sys.exit(1)

if not shutil.which("ffmpeg"):
    print("❌ ffmpeg not found. Install with: apt-get update && apt-get install -y ffmpeg")
    sys.exit(1)


# ── Cleaner prompts ────────────────────────────────────────────────────────────
# These are still lofi/chill, but intentionally less degraded.
LOFI_PROMPTS = [
    "lofi hip hop instrumental, 84 BPM, clean Rhodes piano, crisp boom bap drums, defined warm bass, subtle tape warmth, clean mix, calm focus mood, minimal noise, clear and smooth",
    "late night chillhop, 78 BPM, soft piano, brushed drums, warm upright bass, intimate jazz harmony, clean stereo image, subtle room ambience, reflective and focused, clear mix",
    "japanese-inspired lofi instrumental, 88 BPM, Rhodes chords, mellow bass groove, gentle drums, nostalgic but hi-fi, minimal vinyl texture, clean arrangement, peaceful evening mood",
    "chill study beats, 82 BPM, acoustic guitar picking, soft drums, warm electric piano, smooth bass, relaxed groove, clean production, cozy atmosphere, focused and unobtrusive",
    "dreamy ambient lofi, 72 BPM, soft piano, gentle electric guitar textures, restrained drums, lush but controlled reverb, clear low end, clean mix, floating and calm",
    "lofi jazz hop, 86 BPM, jazzy piano chords, dusty-style drums but clear transients, warm bass, subtle analog color, minimal background noise, mellow and focused",
    "rainy window study music, 80 BPM, soft piano, light rain ambience, warm bass, gentle drums, restrained reverb, clean mix, introspective and peaceful",
    "neo-soul lofi instrumental, 88 BPM, Rhodes licks, soft live-feel drums, supportive bass, rich chords, clean mix, smooth and warm, modern hi-fi chill",
    "midnight jazz lofi, 74 BPM, vibraphone accents, piano, brushed drums, acoustic bass, classy and understated, spacious but clear, cinematic city-night feeling",
    "coffee shop lofi, 90 BPM, bright Rhodes, jazzy chords, light percussion, acoustic bass, uplifting but mellow, clear mix, warm and productive morning feel",
    "bossa lofi instrumental, 82 BPM, nylon guitar, subtle percussion, soft piano, warm bass, relaxed groove, elegant harmony, clean and polished, no harsh distortion",
    "deep focus chillhop, 85 BPM, ambient piano motifs, simple drum groove, warm bass, minimal arrangement, clean mix, smooth transients, calm flow-state energy",
]

FULL_DURATION = 600
TEST_DURATION = 60


def write_track_toml(track_dir: Path, prompt: str, duration: int, steps: int,
                     guidance: float, shift: float, seed: int, thinking: bool) -> Path:
    """
    Write a TOML config for one ACE-Step generation.
    Tuned for cleaner lofi / less degraded output.
    """
    config = {
        # Paths
        "project_root":    str(REPO_DIR),
        "checkpoint_dir":  str(REPO_DIR / "checkpoints"),
        "save_dir":        str(track_dir),

        # Model
        "config_path":     "acestep-v15-sft",
        "lm_model_path":   "acestep-5Hz-lm-0.6B",
        "backend":         "auto",
        "device":          "auto",

        # Generation
        "task_type":       "text2music",
        "caption":         prompt,
        "lyrics":          "[Instrumental]",
        "instrumental":    True,
        "duration":        float(duration),

        # Slightly adjusted for clarity
        "inference_steps": steps,       # was 50
        "guidance_scale":  guidance,    # try 6.0–6.5 instead of 7.0
        "shift":           shift,       # try 2.0 instead of 3.0
        "seed":            seed,

        # Prompt expansion
        # Keeping these configurable because sometimes "thinking"
        # helps musicality, but it can also overcomplicate the result.
        "thinking":         thinking,
        "use_cot_metas":    thinking,
        "use_cot_caption":  thinking,
        "use_cot_language": False,

        # Output
        "batch_size":      1,
        "audio_format":    "flac",
        "use_random_seed": False if seed >= 0 else True,
    }

    toml_path = track_dir / "config.toml"
    track_dir.mkdir(parents=True, exist_ok=True)
    with open(toml_path, "w") as f:
        toml.dump(config, f)
    return toml_path


def find_output_audio(track_dir: Path):
    """Find generated audio in the track directory."""
    for ext in ("*.flac", "*.wav", "*.mp3"):
        matches = sorted(track_dir.glob(ext))
        if matches:
            return matches[-1]
    return None


def generate_track(track_num: int, total: int, prompt: str, duration: int,
                   steps: int, guidance: float, shift: float,
                   seed_base: int, thinking: bool):
    """
    Generate one track by invoking ACE-Step cli.py with a TOML config.
    """
    track_dir = CLIPS_DIR / f"track_{track_num:03d}"

    # Stable reproducible seed per track if requested
    seed = -1 if seed_base < 0 else (seed_base + track_num)

    existing = find_output_audio(track_dir)
    if existing and existing.stat().st_size > 100_000:
        size_mb = existing.stat().st_size / 1_048_576
        print(f"  ✓ Track {track_num}/{total} already exists ({size_mb:.1f} MB) — skipping")
        return existing

    print(f"\n{'─'*68}")
    print(f"  Track {track_num}/{total}")
    print(f"  Prompt   : {prompt}")
    print(f"  Duration : {duration}s ({duration//60}m {duration%60}s)")
    print(f"  Steps    : {steps}")
    print(f"  Guidance : {guidance}")
    print(f"  Shift    : {shift}")
    print(f"  Seed     : {seed}")
    print(f"  Thinking : {thinking}")
    print(f"{'─'*68}")

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
        print(f"\n  ❌ Track {track_num} failed (exit code {result.returncode})")
        return None

    audio_path = find_output_audio(track_dir)
    if not audio_path:
        print(f"\n  ❌ Track {track_num}: no audio file found in {track_dir}")
        return None

    size_mb = audio_path.stat().st_size / 1_048_576
    print(f"\n  ✓ Track {track_num} done in {elapsed:.0f}s → {audio_path.name} ({size_mb:.1f} MB)")
    return audio_path


def concat_to_flac_and_mp3(clip_paths):
    """
    Concatenate all clips into:
    1) FLAC master
    2) MP3 delivery file with gentle mastering
    """
    print(f"\n{'='*68}")
    print("  Concatenating tracks...")
    print(f"{'='*68}\n")

    list_file = CLIPS_DIR / "concat_list.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve()}'\n")

    # First: create a lossless FLAC master
    flac_cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "flac",
        "-metadata", "title=Lofi Hip Hop Mix - Clean Master",
        "-metadata", "artist=ACE-Step 1.5 AI",
        "-metadata", "album=YouTube Lofi Channel",
        str(FINAL_FLAC),
    ]

    flac_result = subprocess.run(flac_cmd, capture_output=True, text=True)
    if flac_result.returncode != 0:
        print(f"❌ FLAC concat error:\n{flac_result.stderr}")
        sys.exit(1)

    # Then create MP3 with a gentle cleanup/mastering pass
    # Light mud cut + slight presence boost + loudness normalization
    audio_filter = (
        "highpass=f=28,"
        "equalizer=f=220:t=q:w=1.0:g=-2,"
        "equalizer=f=3500:t=q:w=1.0:g=1.2,"
        "loudnorm=I=-14:TP=-1.5:LRA=11"
    )

    mp3_cmd = [
        FFMPEG, "-y",
        "-i", str(FINAL_FLAC),
        "-af", audio_filter,
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        "-id3v2_version", "3",
        "-metadata", "title=Lofi Hip Hop Mix - Clean Master",
        "-metadata", "artist=ACE-Step 1.5 AI",
        "-metadata", "album=YouTube Lofi Channel",
        str(FINAL_MP3),
    ]

    mp3_result = subprocess.run(mp3_cmd, capture_output=True, text=True)
    if mp3_result.returncode != 0:
        print(f"❌ MP3 encode/mastering error:\n{mp3_result.stderr}")
        sys.exit(1)

    flac_size = FINAL_FLAC.stat().st_size / 1_048_576
    mp3_size  = FINAL_MP3.stat().st_size / 1_048_576

    print(f"✓ FLAC master: {FINAL_FLAC} ({flac_size:.1f} MB)")
    print(f"✓ MP3 output : {FINAL_MP3} ({mp3_size:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Generate cleaner lofi music with ACE-Step 1.5 (RunPod/CUDA)")
    parser.add_argument("--test", action="store_true", help="Generate 2 short tracks (1 min each)")
    parser.add_argument("--tracks", type=int, default=12, help="Number of tracks (default 12)")
    parser.add_argument("--duration", type=int, default=None, help="Seconds per track (default 600)")
    parser.add_argument("--list", action="store_true", help="Print prompts and exit")

    # New tunables
    parser.add_argument("--steps", type=int, default=60, help="Inference steps (default 60)")
    parser.add_argument("--guidance", type=float, default=6.2, help="Guidance scale (default 6.2)")
    parser.add_argument("--shift", type=float, default=2.0, help="Shift value (default 2.0)")
    parser.add_argument("--seed-base", type=int, default=1000, help="Base seed for reproducibility; use -1 for random")
    parser.add_argument("--no-thinking", action="store_true", help="Disable ACE-Step prompt expansion/thinking")

    args = parser.parse_args()

    if args.list:
        for i, p in enumerate(LOFI_PROMPTS, 1):
            print(f"{i:2d}. {p}")
        return

    duration   = args.duration or (TEST_DURATION if args.test else FULL_DURATION)
    num_tracks = 2 if args.test else args.tracks
    prompts    = [LOFI_PROMPTS[i % len(LOFI_PROMPTS)] for i in range(num_tracks)]
    total_min  = (num_tracks * duration) // 60
    thinking   = not args.no_thinking

    print(f"""
{'='*68}
  ACE-Step 1.5 Cleaner Lofi Generator
  Tracks   : {num_tracks}
  Duration : {duration}s each ({duration//60}m)
  Total    : ~{total_min} minutes
  Model    : acestep-v15-sft
  Steps    : {args.steps}
  Guidance : {args.guidance}
  Shift    : {args.shift}
  Thinking : {thinking}
  Output   : {FINAL_MP3.name}
{'='*68}
Note: First run downloads model weights.
""")

    clip_paths = []
    for i, prompt in enumerate(prompts, 1):
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
        print("\n❌ No tracks generated. Check errors above.")
        sys.exit(1)

    concat_to_flac_and_mp3(clip_paths)

    print(f"""
{'='*68}
  ✅ Done!
  {len(clip_paths)} tracks → ~{total_min} minutes total
  FLAC: {FINAL_FLAC}
  MP3 : {FINAL_MP3}
{'='*68}
""")


if __name__ == "__main__":
    main()
