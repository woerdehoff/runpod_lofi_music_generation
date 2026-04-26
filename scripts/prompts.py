#!/usr/bin/env python3
"""
prompts.py
==========
High-quality prompt packs for ACE-Step lofi generation.
Optimized for:
- Musical structure (no chaos)
- Warm analog feel (no MIDI)
- Stable rhythm (no drift)
"""

from typing import List, Dict

# ── Balanced texture system (NOT too clean, NOT too chaotic) ───────────────
_TEXTURE_WARM = (
    "warm analog saturation, soft tape compression, "
    "natural velocity dynamics, round transients, "
    "subtle pitch variation, slight tape character, "
    "not perfectly clean digital audio"
)

_TEXTURE_ROOM = (
    "intimate room reverb, close-miked instrument tones, "
    "subtle stereo width"
)

_RHYTHM_LOCK = (
    "stable rhythmic grid, tight pocket, drums locked to tempo, "
    "consistent timing with slight natural feel, no drift"
)

# ── Prompt Packs ───────────────────────────────────────────────────────────
PROMPT_PACKS: Dict[str, List[str]] = {

    # ✅ MAIN PACK — Use this for production
    "clean_lofi_hiphop": [
        f"lofi hip hop instrumental, 78 BPM, warm Rhodes chords, boom bap drums with soft swing, deep steady bassline, simple repeating chord progression, smooth groove, melodic but minimal, clear structure, no randomness, no chaotic changes, {_TEXTURE_WARM}, {_TEXTURE_ROOM}, {_RHYTHM_LOCK}, no bright highs",

        f"chillhop instrumental, 80 BPM, electric piano chords, tight drum groove, warm bass, simple loop-based structure, consistent progression, calm and musical, smooth transitions, {_TEXTURE_WARM}, {_TEXTURE_ROOM}, {_RHYTHM_LOCK}",

        f"classic lofi beat, 76 BPM, piano chord loop, boom bap drums, warm bass, repetitive structure, simple melody, relaxed groove, balanced mix, slightly softened highs, {_TEXTURE_WARM}, {_RHYTHM_LOCK}, not overly processed"
    ],

    # ✅ Slightly dirtier version but still controlled
    "traditional_adlibs": [
        f"classic lofi hip hop, 85 BPM, dusty boom bap drums, vinyl texture low in mix, sampled jazz chords with warmth, deep bass, subtle vocal chops low volume, {_TEXTURE_WARM}, {_TEXTURE_ROOM}, {_RHYTHM_LOCK}, no lyrics",

        f"old school chillhop, 80 BPM, MPC-style drums with soft swing, warm Rhodes loop, analog-style compression, mellow bass, subtle texture noise, {_TEXTURE_WARM}, {_RHYTHM_LOCK}, not digital sounding"
    ],

    # ✅ Clean focus (safest, most stable)
    "focus_room": [
        f"focus lofi beat, 78 BPM, soft Rhodes chords, tight drum groove, warm bass, minimal arrangement, calm and consistent, clean structure, {_TEXTURE_WARM}, {_TEXTURE_ROOM}, {_RHYTHM_LOCK}, unobtrusive",

        f"coding lofi, 80 BPM, electric piano loop, steady drums, supportive bassline, repetitive and relaxed, no sudden changes, {_TEXTURE_WARM}, {_RHYTHM_LOCK}, smooth and focused"
    ],
}


# ── Helpers ────────────────────────────────────────────────────────────────
def get_prompt_pack(name: str = "clean_lofi_hiphop") -> List[str]:
    """Return a named prompt pack."""
    if name not in PROMPT_PACKS:
        valid = ", ".join(sorted(PROMPT_PACKS.keys()))
        raise ValueError(f"Unknown prompt pack '{name}'. Valid options: {valid}")
    return PROMPT_PACKS[name]


def list_prompt_packs() -> List[str]:
    """Return available prompt pack names."""
    return sorted(PROMPT_PACKS.keys())
