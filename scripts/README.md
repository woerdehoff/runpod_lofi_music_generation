# RunPod Lofi Generator

This repo separates prompt content from generation logic so you can:

- tune prompts without touching the core generator
- maintain multiple prompt packs
- publish the project cleanly to GitHub

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

The generator now:

- uses stronger lofi-oriented default settings
- can render multiple candidates per track and auto-pick the best one
- writes selected tracks to `output/singles/`
- writes a master to `output/lofi_album_clean_master.mp3`
- writes an inspection report to `output/generation_report.txt`
