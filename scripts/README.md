# RunPod Lofi Generator

This repo separates **prompt content** from **generation logic** so you can:

- tune prompts without touching the core generator
- maintain multiple prompt packs
- publish the project cleanly to GitHub

## Files

- `generate_lofi_runpod_clean.py` — main RunPod generator
- `prompts.py` — prompt packs and helper functions

## Example usage

```bash
python /workspace/generate_lofi_runpod_clean.py --list
python /workspace/generate_lofi_runpod_clean.py --tracks 1 --duration 180 --prompt-pack diverse_lofi --steps 60 --guidance 5.8 --shift 2.0 --no-thinking
python /workspace/generate_lofi_runpod_clean.py --tracks 2 --duration 180 --prompt-pack focus_room --steps 60 --guidance 5.8 --shift 2.0 --no-thinking