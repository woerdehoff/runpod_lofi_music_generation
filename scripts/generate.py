#!/usr/bin/env python3
"""
generate.py
===========
Production-oriented ACE-Step 1.5 lofi generator for RunPod.

This version focuses on three things:
1. Better prompt quality and safer default inference settings
2. Multi-seed candidate generation with automatic candidate selection
3. Output inspection so it is easier to separate generation issues from mastering issues
"""

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import toml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "toml", "-q"], check=False)
    import toml

from prompts import get_prompt_pack, list_prompt_packs


SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_DIR = SCRIPT_DIR / "ACE-Step-1.5"
CLI_PY = REPO_DIR / "cli.py"
CLIPS_DIR = SCRIPT_DIR / "acestep_clips"
OUTPUT_DIR = SCRIPT_DIR / "output"
SINGLES_DIR = OUTPUT_DIR / "singles"
ALBUM_DIR = OUTPUT_DIR / "albums"
FINAL_MP3 = OUTPUT_DIR / "lofi_album_clean_master.mp3"
REPORT_TXT = OUTPUT_DIR / "generation_report.txt"
REPORT_JSON = OUTPUT_DIR / "generation_report.json"
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

FULL_DURATION = 180
TEST_DURATION = 75
MAX_SAFE_DURATION = 480
DEFAULT_STEPS = 96
DEFAULT_GUIDANCE = 4.5
DEFAULT_SHIFT = 1.55
DEFAULT_TRACKS = 10
INSTRUCTION_TXT = REPO_DIR / "instruction.txt"

DASH_LINE = "-" * 72
EQ_LINE = "=" * 72

CLIPS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
SINGLES_DIR.mkdir(exist_ok=True)
ALBUM_DIR.mkdir(exist_ok=True)


if not CLI_PY.exists():
    print(f"ERROR: ACE-Step repo not found at {REPO_DIR}")
    print("  Edit REPO_DIR in this script if your folder name differs.")
    sys.exit(1)

if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
    print("ERROR: ffmpeg/ffprobe not found. Install with:")
    print("  apt-get update && apt-get install -y ffmpeg")
    sys.exit(1)


def nuke_instruction_txt() -> None:
    if INSTRUCTION_TXT.exists():
        INSTRUCTION_TXT.unlink()


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
    config = {
        "project_root": str(REPO_DIR),
        "checkpoint_dir": str(REPO_DIR / "checkpoints"),
        "save_dir": str(track_dir),
        "config_path": "acestep-v15-sft",
        "lm_model_path": "acestep-5Hz-lm-0.6B",
        "backend": "auto",
        "device": "auto",
        "task_type": "text2music",
        "caption": prompt,
        "lyrics": "[Instrumental]",
        "instrumental": True,
        "duration": float(duration),
        "inference_steps": steps,
        "guidance_scale": guidance,
        "shift": shift,
        "seed": seed,
        "thinking": thinking,
        "use_cot_metas": thinking,
        "use_cot_caption": False,
        "use_cot_language": False,
        "batch_size": 1,
        "audio_format": "flac",
        "use_random_seed": seed < 0,
    }
    track_dir.mkdir(parents=True, exist_ok=True)
    toml_path = track_dir / "config.toml"
    with open(toml_path, "w", encoding="utf-8") as handle:
        toml.dump(config, handle)
    return toml_path


def find_output_audio(track_dir: Path) -> Optional[Path]:
    for ext in ("*.flac", "*.wav", "*.mp3"):
        matches = sorted(track_dir.glob(ext))
        if matches:
            return matches[-1]
    return None


def probe_duration(audio_path: Path) -> Optional[float]:
    cmd = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (TypeError, ValueError):
        return None
    return None


def probe_volume(audio_path: Path) -> Dict[str, Optional[float]]:
    cmd = [FFMPEG, "-i", str(audio_path), "-af", "volumedetect", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stderr = result.stderr or ""

    mean_match = re.search(r"mean_volume:\s*(-?[0-9]+(?:\.[0-9]+)?) dB", stderr)
    max_match = re.search(r"max_volume:\s*(-?[0-9]+(?:\.[0-9]+)?) dB", stderr)

    return {
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
        "max_volume_db": float(max_match.group(1)) if max_match else None,
    }


def analyze_audio(audio_path: Path) -> Dict[str, Optional[float]]:
    stats: Dict[str, Optional[float]] = {
        "path": str(audio_path),
        "size_mb": round(audio_path.stat().st_size / 1_048_576, 2),
        "duration_sec": probe_duration(audio_path),
        "mean_volume_db": None,
        "max_volume_db": None,
    }
    stats.update(probe_volume(audio_path))
    return stats


def candidate_score(stats: Dict[str, Optional[float]], target_duration: int) -> float:
    score = 0.0
    duration = stats.get("duration_sec")
    mean_volume = stats.get("mean_volume_db")
    max_volume = stats.get("max_volume_db")
    size_mb = stats.get("size_mb") or 0.0

    if duration is None:
        score -= 40.0
    else:
        score -= abs(duration - target_duration) * 1.8
        if duration < target_duration * 0.85:
            score -= 15.0

    if size_mb < 0.4:
        score -= 10.0

    if mean_volume is None:
        score -= 6.0
    elif -24.0 <= mean_volume <= -12.0:
        score += 8.0
    elif -28.0 <= mean_volume <= -10.0:
        score += 2.0
    else:
        score -= 5.0

    if max_volume is None:
        score -= 3.0
    elif max_volume > -0.3:
        score -= 8.0
    elif -3.0 <= max_volume <= -0.8:
        score += 3.0

    return round(score, 2)


def resolve_seed(seed_base: int, track_num: int, candidate_num: int) -> int:
    if seed_base < 0:
        return random.randint(0, 2**31 - 1)
    return seed_base + (track_num * 100) + candidate_num


def candidate_dir(track_num: int, candidate_num: int, total_candidates: int) -> Path:
    track_dir = CLIPS_DIR / f"track_{track_num:03d}"
    if total_candidates <= 1:
        return track_dir
    return track_dir / f"candidate_{candidate_num:02d}"


def format_db(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} dB"


def generate_candidate(
    track_num: int,
    total_tracks: int,
    candidate_num: int,
    total_candidates: int,
    prompt: str,
    duration: int,
    steps: int,
    guidance: float,
    shift: float,
    seed_base: int,
    thinking: bool,
    resume_existing: bool,
) -> Optional[Dict[str, object]]:
    track_path = candidate_dir(track_num, candidate_num, total_candidates)
    seed = resolve_seed(seed_base, track_num, candidate_num)
    existing = find_output_audio(track_path)

    print("")
    print(DASH_LINE)
    print(f"Track {track_num + 1}/{total_tracks} | Candidate {candidate_num + 1}/{total_candidates}")
    print(f"Prompt   : {prompt[:110]}...")
    print(f"Settings : duration={duration}s steps={steps} guidance={guidance} shift={shift} seed={seed}")
    print(DASH_LINE)

    if resume_existing and existing and existing.stat().st_size > 100_000:
        stats = analyze_audio(existing)
        stats["score"] = candidate_score(stats, duration)
        duration_value = stats.get("duration_sec") or 0.0
        print(f"  [reuse] {existing.name} | duration={duration_value:.1f}s | score={stats['score']}")
        return {
            "candidate_index": candidate_num,
            "seed": seed,
            "audio_path": existing,
            "stats": stats,
            "reused": True,
        }

    toml_path = write_track_toml(
        track_dir=track_path,
        prompt=prompt,
        duration=duration,
        steps=steps,
        guidance=guidance,
        shift=shift,
        seed=seed,
        thinking=thinking,
    )

    nuke_instruction_txt()
    start_time = time.time()
    result = subprocess.run(
        [sys.executable, str(CLI_PY), "-c", str(toml_path)],
        cwd=str(REPO_DIR),
        input="\n",
        text=True,
        check=False,
    )
    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"  FAIL: candidate exited with code {result.returncode}")
        return None

    audio_path = find_output_audio(track_path)
    if not audio_path:
        print(f"  FAIL: no audio file found in {track_path}")
        return None

    stats = analyze_audio(audio_path)
    stats["score"] = candidate_score(stats, duration)
    duration_value = stats.get("duration_sec")
    duration_str = "unknown" if duration_value is None else f"{duration_value:.1f}s"
    print(
        f"  OK: {audio_path.name} in {elapsed:.0f}s | duration={duration_str} "
        f"| mean={format_db(stats['mean_volume_db'])} | peak={format_db(stats['max_volume_db'])} "
        f"| score={stats['score']}"
    )

    return {
        "candidate_index": candidate_num,
        "seed": seed,
        "audio_path": audio_path,
        "stats": stats,
        "reused": False,
    }


def choose_best_candidate(candidates: List[Dict[str, object]]) -> Dict[str, object]:
    return max(candidates, key=lambda item: float(item["stats"]["score"]))


def export_selected_track(track_num: int, clip_path: Path) -> Path:
    destination = SINGLES_DIR / f"track_{track_num + 1:02d}{clip_path.suffix}"
    shutil.copy2(clip_path, destination)
    return destination


def concat_to_mp3(clip_paths: List[Path]) -> Dict[str, Optional[float]]:
    print("")
    print(EQ_LINE)
    print("Concatenating selected tracks into the final MP3...")
    print(EQ_LINE)

    list_file = CLIPS_DIR / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as handle:
        for path in clip_paths:
            handle.write(f"file '{path.resolve()}'\n")

    audio_filter = (
        "highpass=f=28,"
        "equalizer=f=180:t=q:w=1.0:g=-1.0,"
        "equalizer=f=3200:t=q:w=1.0:g=0.4,"
        "lowpass=f=13800,"
        "loudnorm=I=-14:TP=-1.5:LRA=10"
    )

    cmd = [
        FFMPEG,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-af",
        audio_filter,
        "-c:a",
        "libmp3lame",
        "-b:a",
        "320k",
        "-id3v2_version",
        "3",
        "-metadata",
        "title=Lofi Hip Hop Mix - Clean Master",
        "-metadata",
        "artist=ACE-Step 1.5 AI",
        "-metadata",
        "album=YouTube Lofi Channel",
        str(FINAL_MP3),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("ERROR: ffmpeg concat failed:")
        print(result.stderr)
        sys.exit(1)

    album_copy = ALBUM_DIR / FINAL_MP3.name
    shutil.copy2(FINAL_MP3, album_copy)
    stats = analyze_audio(FINAL_MP3)
    duration_value = stats.get("duration_sec") or 0.0
    print(
        f"  Final MP3: {FINAL_MP3} | duration={duration_value:.1f}s "
        f"| mean={format_db(stats['mean_volume_db'])} | peak={format_db(stats['max_volume_db'])}"
    )
    return stats


def write_report(report: Dict[str, object]) -> None:
    with open(REPORT_JSON, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    lines = [
        "ACE-Step Lofi Generation Report",
        EQ_LINE,
        f"Prompt pack : {report['settings']['prompt_pack']}",
        f"Tracks      : {report['settings']['tracks']}",
        f"Candidates  : {report['settings']['candidates_per_track']}",
        f"Duration    : {report['settings']['duration_sec']}s",
        f"Steps       : {report['settings']['steps']}",
        f"Guidance    : {report['settings']['guidance']}",
        f"Shift       : {report['settings']['shift']}",
        "",
        "Track selections",
        DASH_LINE,
    ]

    for track in report["tracks"]:
        selected = track["selected_candidate"]
        stats = selected["stats"]
        duration_value = stats.get("duration_sec") or 0.0
        lines.append(
            f"Track {track['track_number']:02d} | candidate {selected['candidate_index'] + 1} "
            f"| seed={selected['seed']} | score={stats['score']} | duration={duration_value:.1f}s "
            f"| mean={format_db(stats['mean_volume_db'])} | peak={format_db(stats['max_volume_db'])}"
        )
        lines.append(f"  Prompt: {track['prompt']}")

    final_stats = report["final_master"]
    final_duration = final_stats.get("duration_sec") or 0.0
    lines.extend(
        [
            "",
            "Master output",
            DASH_LINE,
            f"Path        : {final_stats['path']}",
            f"Duration    : {final_duration:.1f}s",
            f"Mean volume : {format_db(final_stats['mean_volume_db'])}",
            f"Peak volume : {format_db(final_stats['max_volume_db'])}",
        ]
    )

    with open(REPORT_TXT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def clean_outputs() -> None:
    if CLIPS_DIR.exists():
        shutil.rmtree(CLIPS_DIR)
    CLIPS_DIR.mkdir(exist_ok=True)

    if SINGLES_DIR.exists():
        shutil.rmtree(SINGLES_DIR)
    SINGLES_DIR.mkdir(exist_ok=True)

    for path in (FINAL_MP3, ALBUM_DIR / FINAL_MP3.name, REPORT_TXT, REPORT_JSON):
        if path.exists():
            path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate stronger lofi music with ACE-Step 1.5 on RunPod"
    )
    parser.add_argument("--test", action="store_true", help="Quick test mode: 2 short tracks")
    parser.add_argument("--tracks", type=int, default=DEFAULT_TRACKS, help=f"Number of tracks (default: {DEFAULT_TRACKS})")
    parser.add_argument("--duration", type=int, default=None, help="Seconds per track")
    parser.add_argument("--list", action="store_true", help="Print prompt packs and exit")
    parser.add_argument(
        "--prompt-pack",
        type=str,
        default="gold_standard_lofi",
        help="Prompt pack name from prompts.py (default: gold_standard_lofi)",
    )
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help=f"Inference steps (default: {DEFAULT_STEPS})")
    parser.add_argument(
        "--guidance",
        type=float,
        default=DEFAULT_GUIDANCE,
        help=f"CFG guidance scale (default: {DEFAULT_GUIDANCE})",
    )
    parser.add_argument("--shift", type=float, default=DEFAULT_SHIFT, help=f"Noise shift (default: {DEFAULT_SHIFT})")
    parser.add_argument("--seed-base", type=int, default=-1, help="Base seed, -1 for random per candidate")
    parser.add_argument("--thinking", action="store_true", help="Enable ACE-Step thinking/reasoning")
    parser.add_argument("--clean", action="store_true", help="Wipe old clips and reports before generating")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing candidate audio from the clip directories instead of regenerating",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=None,
        help="Candidates per track. Default: 3 for full runs, 2 for --test",
    )
    args = parser.parse_args()

    if args.list:
        print("")
        print("Available prompt packs:")
        print("")
        for pack_name in list_prompt_packs():
            prompts = get_prompt_pack(pack_name)
            print(f"  {pack_name} ({len(prompts)} prompts)")
            for index, prompt in enumerate(prompts, start=1):
                print(f"    {index}. {prompt[:95]}...")
            print("")
        return

    if args.clean:
        print("Cleaning old clips and reports...")
        clean_outputs()

    duration = args.duration or (TEST_DURATION if args.test else FULL_DURATION)
    if duration > MAX_SAFE_DURATION:
        print(f"WARNING: {duration}s exceeds safe max ({MAX_SAFE_DURATION}s) and will be clamped.")
        duration = MAX_SAFE_DURATION

    prompt_pack = get_prompt_pack(args.prompt_pack)
    num_tracks = 2 if args.test else args.tracks
    candidates_per_track = args.candidates or (2 if args.test else 3)
    total_min = (num_tracks * duration) / 60

    shuffled_prompts = prompt_pack.copy()
    random.shuffle(shuffled_prompts)
    prompts = [shuffled_prompts[index % len(shuffled_prompts)] for index in range(num_tracks)]

    print("")
    print(EQ_LINE)
    print("ACE-Step 1.5 Lofi Generator")
    print(EQ_LINE)
    print(f"Prompt pack : {args.prompt_pack} ({len(prompt_pack)} prompts)")
    print(f"Tracks      : {num_tracks}")
    print(f"Candidates  : {candidates_per_track} per track")
    print(f"Duration    : {duration}s each (~{total_min:.1f} min total before curation)")
    print(f"Steps       : {args.steps}")
    print(f"Guidance    : {args.guidance}")
    print(f"Shift       : {args.shift}")
    print(f"Thinking    : {args.thinking}")
    print(f"Master      : {FINAL_MP3}")
    print(EQ_LINE)

    selected_clip_paths: List[Path] = []
    track_reports: List[Dict[str, object]] = []

    for track_index, prompt in enumerate(prompts):
        candidates: List[Dict[str, object]] = []
        for candidate_index in range(candidates_per_track):
            candidate = generate_candidate(
                track_num=track_index,
                total_tracks=num_tracks,
                candidate_num=candidate_index,
                total_candidates=candidates_per_track,
                prompt=prompt,
                duration=duration,
                steps=args.steps,
                guidance=args.guidance,
                shift=args.shift,
                seed_base=args.seed_base,
                thinking=args.thinking,
                resume_existing=args.resume,
            )
            if candidate:
                candidates.append(candidate)

        if not candidates:
            print(f"ERROR: all candidates failed for track {track_index + 1}")
            continue

        selected = choose_best_candidate(candidates)
        selected_path = export_selected_track(track_index, selected["audio_path"])
        selected_clip_paths.append(selected_path)
        print(
            f"Selected track {track_index + 1}: candidate {selected['candidate_index'] + 1} "
            f"with score={selected['stats']['score']} -> {selected_path.name}"
        )

        track_reports.append(
            {
                "track_number": track_index + 1,
                "prompt": prompt,
                "selected_candidate": {
                    "candidate_index": selected["candidate_index"],
                    "seed": selected["seed"],
                    "audio_path": str(selected["audio_path"]),
                    "stats": selected["stats"],
                },
                "candidates": [
                    {
                        "candidate_index": candidate["candidate_index"],
                        "seed": candidate["seed"],
                        "audio_path": str(candidate["audio_path"]),
                        "stats": candidate["stats"],
                        "reused": candidate["reused"],
                    }
                    for candidate in candidates
                ],
            }
        )

    if not selected_clip_paths:
        print("ERROR: no tracks generated. Check the failures above.")
        sys.exit(1)

    final_stats = concat_to_mp3(selected_clip_paths)
    report = {
        "settings": {
            "prompt_pack": args.prompt_pack,
            "tracks": num_tracks,
            "candidates_per_track": candidates_per_track,
            "duration_sec": duration,
            "steps": args.steps,
            "guidance": args.guidance,
            "shift": args.shift,
            "thinking": args.thinking,
        },
        "tracks": track_reports,
        "final_master": final_stats,
    }
    write_report(report)

    total_selected_duration = sum(probe_duration(path) or 0 for path in selected_clip_paths)
    print("")
    print(EQ_LINE)
    print(
        f"DONE: {len(selected_clip_paths)} tracks selected -> ~{total_selected_duration / 60:.1f} minutes "
        f"| report={REPORT_TXT.name}"
    )
    print(EQ_LINE)


if __name__ == "__main__":
    main()
