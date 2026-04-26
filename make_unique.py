#!/usr/bin/env python3
"""Simple unique lofi generator"""
import random
import subprocess
import sys
from pathlib import Path

random.seed()
REPO = Path("/workspace/ACE-Step-1.5")
OUTPUT = Path("/workspace/output")
OUTPUT.mkdir(exist_ok=True)

# Random extreme parameters
seed = random.randint(1, 999999999)
steps = random.randint(90, 130)
guidance = round(random.uniform(3.5, 6.5), 2)
shift = round(random.uniform(1.1, 1.9), 2)

# Wild prompts
prompts = [
    "abstract experimental lofi with detuned Rhodes, broken cassette warble, irregular drums, 68 BPM",
    "glitchy beat with pitched-down samples, analog synth drone, off-kilter hi-hats, 77 BPM",
    "midnight lofi study beat with muted trumpet, wobbly piano, brush snare, 71 BPM, rain layer",
    "cyberpunk lofi with filtered vocal chops, metallic percussion, dark bass, 83 BPM, neon atmosphere",
    "nature lofi with field recordings, kalimba melody, soft hand drums, 66 BPM, forest ambience",
    "retro arcade lofi with 8-bit bleeps, chiptune bass, dusty breakbeat, 74 BPM, cassette flutter",
    "jazz club lofi after hours, smoky upright bass, muted piano, soft brush kit, 79 BPM, intimate",
]

prompt = random.choice(prompts)

print(f"\n{'='*70}")
print(f"🎵 GENERATING UNIQUE 2-MINUTE LOFI")
print(f"{'='*70}")
print(f"Style: {prompt}")
print(f"Steps: {steps} | Guidance: {guidance} | Shift: {shift} | Seed: {seed}")
print(f"{'='*70}\n")

import toml
config = {
    "project_root": str(REPO),
    "checkpoint_dir": str(REPO / "checkpoints"),
    "save_dir": str(OUTPUT),
    "config_path": "acestep-v15-sft",
    "lm_model_path": "acestep-5Hz-lm-0.6B",
    "backend": "auto",
    "device": "auto",
    "task_type": "text2music",
    "caption": prompt,
    "lyrics": "[Instrumental]",
    "instrumental": True,
    "duration": 120.0,
    "inference_steps": steps,
    "guidance_scale": guidance,
    "shift": shift,
    "seed": seed,
    "thinking": False,
    "batch_size": 1,
    "audio_format": "flac",
}

toml_path = OUTPUT / "config.toml"
with open(toml_path, "w") as f:
    toml.dump(config, f)

print("⏳ Generating (several minutes)...\n")
result = subprocess.run(
    [sys.executable, str(REPO / "cli.py"), "-c", str(toml_path)],
    cwd=str(REPO),
    input="\n",
    text=True,
)

if result.returncode != 0:
    print("❌ Failed!")
    sys.exit(1)

generated = list(OUTPUT.glob("*.flac"))
if generated:
    output_file = generated[-1]
    final = OUTPUT / "unique_lofi_2min.flac"
    if final.exists():
        final.unlink()
    output_file.rename(final)
    print(f"\n✅ DONE: {final} ({final.stat().st_size/1024/1024:.1f} MB)\n")
else:
    print("❌ No output found!")
