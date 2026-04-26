# RunPod Lofi Generator

This repo separates **prompt content** from **generation logic** so you can:

- tune prompts without touching the core generator
- maintain multiple prompt packs
- publish the project cleanly to GitHub

## Files

- `generate.py` — main RunPod generator
- `prompts.py` — prompt packs and helper functions
- `setup_pod.sh` — automated setup script for RunPod instances

## Setup

Run the setup script on a fresh RunPod instance:

```bash
bash setup_pod.sh
```

This will:
- Install system dependencies (ffmpeg, git, tmux, etc.)
- Clone and set up ACE-Step 1.5
- Install Python dependencies
- Create output directories
- Check for your custom scripts

## Example usage

```bash
python /workspace/generate.py --list
python /workspace/generate.py --tracks 1 --duration 180 --prompt-pack diverse_lofi --steps 60 --guidance 5.8 --shift 2.0 --no-thinking
python /workspace/generate.py --tracks 2 --duration 180 --prompt-pack focus_room --steps 60 --guidance 5.8 --shift 2.0 --no-thinking