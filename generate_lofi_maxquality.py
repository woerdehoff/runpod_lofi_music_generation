#!/usr/bin/env python3
"""
generate_lofi_maxquality.py — MAX QUALITY single-track test
===========================================================
RunPod / Linux CUDA GPU — everything cranked to the max
===========================================================

Settings:
    - 4B language model (biggest available — richest musical blueprints)
    - 100 diffusion steps (maximum detail)
    - Guidance scale 10.0 (strongest prompt adherence)
    - SFT model (full quality DiT)
    - Ad-lib vocals on select tracks

Usage:
    python generate_lofi_maxquality.py                        # 1 track, 2 min
    python generate_lofi_maxquality.py --duration 240         # 1 track, 4 min
    python generate_lofi_maxquality.py --tracks 3             # 3 tracks
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
    subprocess.run([sys.executable, "-m", "pip", "install", "toml", "-q"])
    import toml

# -- Paths -------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
REPO_DIR     = SCRIPT_DIR / "ACE-Step-1.5"
CLI_PY       = REPO_DIR / "cli.py"
CLIPS_DIR    = SCRIPT_DIR / "acestep_clips_maxq"
OUTPUT_DIR   = SCRIPT_DIR / "output"
FINAL_MP3    = OUTPUT_DIR / "lofi_maxquality_test.mp3"

FFMPEG       = shutil.which("ffmpeg") or "ffmpeg"

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

if not CLI_PY.exists():
    print(f"ERROR: ACE-Step repo not found at {REPO_DIR}")
    print("   Clone it:  git clone https://github.com/ace-step/ACE-Step-1.5.git")
    sys.exit(1)

if not shutil.which("ffmpeg"):
    print("ERROR: ffmpeg not found. Install with: apt-get install -y ffmpeg")
    sys.exit(1)

# -- Track configs: mix of instrumental and ad-lib ----------------------------
TRACK_CONFIGS = [
    {
        "caption": "lofi hip hop, chill study beats, 85 BPM, Rhodes electric piano, vinyl crackle, boom bap drums, walking upright bass, warm tape saturation, cozy rainy afternoon, mellow and relaxed, soft whispered vocal ad-libs",
        "lyrics": "[verse]\nyeah... mmm...\nooh, feel the vibe...\n[verse]\nmmm... uh huh...\none more time...\n[outro]\nbreathe... relax...",
        "instrumental": False,
    },
    {
        "caption": "late night lofi jazz, 75 BPM, muted trumpet, brushed snare, upright bass, gentle piano comping, city rain ambience, midnight coffee shop, introspective mood",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "lofi hip hop with Japanese city pop influence, 90 BPM, Fender Rhodes, funky bass line, vinyl noise, soft reverb, nostalgic summer feeling, lo-fi cassette tape warmth, gentle humming vocals",
        "lyrics": "[verse]\nla da da... mmm...\nooh ooh...\n[verse]\nda da da dum...\nmmm yeah...",
        "instrumental": False,
    },
    {
        "caption": "chillhop instrumental, 80 BPM, acoustic guitar picking, laid-back hip hop drums, piano chords, vinyl surface noise, golden hour afternoon, peaceful and contemplative",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "dreamy ambient lofi, 70 BPM, soft piano, distant electric guitar, slow boom bap drums, heavy reverb, ethereal pads, floating feeling, bedroom producer aesthetic, soft spoken word",
        "lyrics": "[intro]\nbreathe in... let go...\n[verse]\nfloating... drifting away...\npeace of mind...",
        "instrumental": False,
    },
    {
        "caption": "lofi hip hop studying beats, 88 BPM, sampled jazz piano, dusty boom bap drums, sub bass, vinyl crackle, old school hip hop feel, head nodding groove",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "rainy day lofi, 78 BPM, soft piano, rain sounds in background, brushed jazz drums, mellow bass, warm chord progressions, introspective, perfect for focus and concentration",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "lofi soul instrumental, 84 BPM, wurlitzer electric piano, vinyl crackle, soft percussion, Rhodes chord stabs, soulful minor key, late night nostalgic vibes",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "Japanese lofi hip hop, 82 BPM, koto samples, Rhodes piano, gentle boom bap drums, upright bass, sakura season ambience, wabi-sabi aesthetic, peaceful and serene, soft vocal ooh",
        "lyrics": "[verse]\nooh... aah...\nmmm...\n[verse]\nooh... yeah...",
        "instrumental": False,
    },
    {
        "caption": "vintage lofi hip hop, 86 BPM, old vinyl record warmth, sampled 1970s soul music, muffled drums, walking bass, dusty golden era hip hop, classic boom bap",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "coffee shop lofi morning, 92 BPM, bright Rhodes piano, jazzy chord changes, light percussion, acoustic bass, cafe ambience, optimistic and energizing, morning productivity",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
    {
        "caption": "lofi hip hop with bossa nova influence, 80 BPM, classical guitar, subtle congas, piano, upright bass, warm Brazilian jazz feel, sophisticated and chill",
        "lyrics": "[Instrumental]",
        "instrumental": True,
    },
]


def write_track_toml(track_dir, caption, lyrics, instrumental, duration):
    """Write a TOML config file for one ACE-Step track generation."""
    config = {
        # Paths
        "project_root":    str(REPO_DIR),
        "checkpoint_dir":  str(REPO_DIR / "checkpoints"),
        "save_dir":        str(track_dir),

        # MAX QUALITY: SFT model + 4B language model
        "config_path":     "acestep-v15-sft",
        "lm_model_path":   "acestep-5Hz-lm-1.7B",
        "backend":         "auto",
        "device":          "auto",

        # Generation
        "task_type":       "text2music",
        "caption":         caption,
        "lyrics":          lyrics,
        "instrumental":    instrumental,
        "duration":        float(duration),

        # MAX QUALITY: 100 steps + strong guidance
        "inference_steps": 50,
        "guidance_scale":  7.0,
        "shift":           3.0,
        "seed":            -1,

        # LM thinking — full blueprint generation
        "thinking":         True,
        "use_cot_metas":    True,
        "use_cot_caption":  True,
        "use_cot_language": False,

        # Output
        "batch_size":      1,
        "audio_format":    "flac",
        "use_random_seed": True,
    }

    toml_path = track_dir / "config.toml"
    track_dir.mkdir(parents=True, exist_ok=True)
    with open(toml_path, "w") as f:
        toml.dump(config, f)
    return toml_path


def find_output_audio(track_dir):
    """Find the generated audio file in the track output directory."""
    for ext in ("*.flac", "*.wav", "*.mp3"):
        matches = sorted(track_dir.glob(ext))
        if matches:
            return matches[-1]
    return None


def generate_track(track_num, total, track_cfg, duration):
    """Generate one track by running cli.py with a TOML config."""
    track_dir = CLIPS_DIR / f"track_{track_num:03d}"

    # Resumable: skip if already generated
    existing = find_output_audio(track_dir)
    if existing and existing.stat().st_size > 100_000:
        size_mb = existing.stat().st_size / 1_048_576
        print(f"  * Track {track_num}/{total} already exists ({size_mb:.1f} MB) -- skipping")
        return existing

    vocal_tag = "AD-LIB" if not track_cfg["instrumental"] else "INSTRUMENTAL"
    print(f"\n{'-'*60}")
    print(f"  Track {track_num}/{total} [{vocal_tag}]")
    print(f"  Prompt: {track_cfg['caption'][:75]}...")
    print(f"  Duration: {duration}s ({duration//60}m {duration%60}s)")
    print(f"{'-'*60}")

    toml_path = write_track_toml(
        track_dir, track_cfg["caption"], track_cfg["lyrics"],
        track_cfg["instrumental"], duration
    )
    t0 = time.time()

    result = subprocess.run(
        [sys.executable, str(CLI_PY), "-c", str(toml_path)],
        cwd=str(REPO_DIR),
    )

    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"\n  ERROR: Track {track_num} failed (exit code {result.returncode})")
        return None

    audio_path = find_output_audio(track_dir)
    if not audio_path:
        print(f"\n  ERROR: Track {track_num}: no audio file found in {track_dir}")
        return None

    size_mb = audio_path.stat().st_size / 1_048_576
    print(f"\n  OK: Track {track_num} done in {elapsed:.0f}s -> {audio_path.name} ({size_mb:.1f} MB)")
    return audio_path


def concat_to_mp3(clip_paths):
    """Concatenate all FLAC clips into a final 320kbps MP3."""
    print(f"\n{'='*60}")
    print("  Concatenating tracks into final MP3...")
    print(f"{'='*60}\n")

    list_file = CLIPS_DIR / "concat_list.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve()}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        "-id3v2_version", "3",
        "-metadata", "title=Lofi Hip Hop Mix - Max Quality Test",
        "-metadata", "artist=ACE-Step 1.5 AI",
        "-metadata", "album=YouTube Lofi Channel",
        str(FINAL_MP3),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR ffmpeg:\n{result.stderr}")
        sys.exit(1)

    size_mb = FINAL_MP3.stat().st_size / 1_048_576
    print(f"OK Final MP3: {FINAL_MP3}")
    print(f"  Size: {size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="ACE-Step 1.5 MAX QUALITY lofi generator")
    parser.add_argument("--tracks",   type=int, default=1,   help="Number of tracks (default 1)")
    parser.add_argument("--duration", type=int, default=120, help="Seconds per track (default 120)")
    args = parser.parse_args()

    num_tracks = args.tracks
    duration   = args.duration
    total_min  = (num_tracks * duration) // 60

    # Pick tracks from our config list (cycles if more tracks than configs)
    track_list = [TRACK_CONFIGS[i % len(TRACK_CONFIGS)] for i in range(num_tracks)]
    adlib_count = sum(1 for t in track_list if not t["instrumental"])

    print(f"""
{'='*60}
  ACE-Step 1.5 Lofi Generator -- MAX QUALITY
{'='*60}
  Tracks      : {num_tracks} ({adlib_count} with ad-libs, {num_tracks - adlib_count} instrumental)
  Duration    : {duration}s each ({duration//60}m)
  Total       : ~{total_min} minutes
  DiT Model   : acestep-v15-sft
  LM Model    : acestep-5Hz-lm-4B (biggest available)
  Steps       : 100 diffusion steps
  Guidance    : 10.0
  Backend     : CUDA (auto-detected)
  Output      : {FINAL_MP3.name}
{'='*60}
""")

    clip_paths = []
    for i, track_cfg in enumerate(track_list, 1):
        path = generate_track(i, num_tracks, track_cfg, duration)
        if path:
            clip_paths.append(path)

    if not clip_paths:
        print("\nERROR: No tracks generated. Check errors above.")
        sys.exit(1)

    concat_to_mp3(clip_paths)

    print(f"""
{'='*60}
  DONE!
  {len(clip_paths)} tracks -> {total_min} minutes of lofi
  Output: {FINAL_MP3}
{'='*60}
""")


if __name__ == "__main__":
    main()

