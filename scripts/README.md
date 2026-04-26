# RunPod Lofi Generator

This repo separates prompt content from generation logic so you can:

- tune prompts without touching the core generator
- maintain multiple prompt packs
- publish the project cleanly to GitHub

## Current status

This project was debugged directly against an active RunPod pod using the real
`/workspace/generate.py` and `ACE-Step-1.5` checkout.

Current conclusions:

- the pod was successfully updated and validated against the real remote files
- prompt packs and hard track lanes are reaching the generated TOML configs
- multi-candidate generation and reporting are working as intended
- ACE-Step `thinking` / COT prompt conditioning caused prompt collapse and made
  different prompts sound more similar than expected
- `thinking` is now disabled by default in `generate.py`

Recommended default: stay on the direct caption path unless you are explicitly
testing ACE-Step reasoning behavior.

## Files

- `generate.py` - main RunPod generator
- `prompts.py` - prompt packs and helper functions
- `setup_pod.sh` - automated setup script for RunPod instances

## Setup

Run the setup script on a fresh RunPod instance:

```bash
bash setup_pod.sh
```

This will:
- install system dependencies
- clone and set up ACE-Step 1.5
- install Python dependencies
- create output directories
- check for your custom scripts

## Example usage

```bash
python /workspace/generate.py --list
python /workspace/generate.py --test --prompt-pack focus_room --clean
python /workspace/generate.py --tracks 3 --duration 180 --prompt-pack gold_standard_lofi --candidates 3 --clean
```

Recommended real-world commands:

```bash
python /workspace/generate.py --test --prompt-pack quality_rotate --clean
python /workspace/generate.py --tracks 6 --duration 180 --prompt-pack quality_rotate --candidates 3 --clean
python /workspace/generate.py --tracks 6 --duration 180 --prompt-pack gold_standard_lofi --candidates 3 --seed-base 1000 --clean
```

Only enable ACE-Step reasoning if you are deliberately comparing it:

```bash
python /workspace/generate.py --test --prompt-pack quality_rotate --thinking --clean
```

The generator now:

- uses stronger lofi-oriented default settings
- can render multiple candidates per track and auto-pick the best one
- rotates through hard track profiles so adjacent tracks are pushed into more distinct lanes
- writes selected tracks to `output/singles/`
- writes a master to `output/lofi_album_clean_master.mp3`
- writes an inspection report to `output/generation_report.txt`

## What changed during debugging

The recent debugging work focused on the difference between "better prompt
wording" and "actual pod behavior".

Changes made:

- prompt packs were broadened beyond nearly identical piano boom-bap prompts
- candidate generation now varies prompt phrasing and generation settings per candidate
- hard track profiles were added to force more separation between tracks
- reuse is opt-in via `--resume` instead of happening implicitly
- generation reports and per-candidate configs are used as the ground-truth debug surface

The important outcome was that the remote pod really was using the updated
prompts and settings, but ACE-Step's COT/reasoning path still rewrote them into
more generic lofi descriptions. That is why `thinking` now defaults to off.

## Outputs and inspection

After a run, inspect these locations:

- `output/singles/` - selected exported tracks
- `output/lofi_album_clean_master.mp3` - concatenated mastered album
- `output/generation_report.txt` - human-readable summary
- `output/generation_report.json` - machine-readable summary
- `acestep_clips/track_XXX/candidate_YY/config.toml` - exact per-candidate ACE-Step config used

When a run sounds wrong, inspect the candidate TOML and report before changing
mastering settings. That tells you whether the failure is in prompting,
generation, or post-processing.

## Troubleshooting

### Everything sounds the same

Check these in order:

1. Confirm you are not unintentionally reusing old clips. Use `--clean` and do not pass `--resume`.
2. Confirm the selected prompts and settings in `output/generation_report.txt` are actually different.
3. Inspect `acestep_clips/track_XXX/candidate_YY/config.toml` to verify the lane constraint text is present.
4. Keep `--thinking` off unless you are explicitly testing it.

If prompts differ in the report and TOML but audio still collapses, the bottleneck
is the model behavior rather than the wrapper script.

### The pod does not seem to have the latest script

Normal transfer methods on some RunPod pods can fail. In this project, the most
reliable fallback was base64-over-SSH into `/workspace/generate.py` and
`/workspace/prompts.py`, followed immediately by:

```bash
cd /workspace
python3 -m py_compile generate.py prompts.py
python3 generate.py --list
```

### ACE-Step pauses waiting for edited instructions

ACE-Step may emit:

```text
Final Draft Saved
Edit the file now. Press Enter when ready to continue.
```

The wrapper already sends a newline automatically when invoking `cli.py`, so you
do not need to edit `instruction.txt` during normal runs.
