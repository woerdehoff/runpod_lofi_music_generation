#!/usr/bin/env python3
"""
prompts.py
==========
Prompt packs tuned for better ACE-Step lofi output.

The prompts are intentionally specific about groove, arrangement, texture,
and what should be avoided so the model is less likely to drift into generic,
over-bright, or overly dramatic music.
"""

from typing import Dict, List


_FOUNDATION = (
    "instrumental only, no vocals, no spoken word, no rap, no trap hats, "
    "no EDM risers, no dramatic drops, no abrupt section changes"
)

_GROOVE = (
    "steady pocket, soft swing, stable rhythmic grid, natural timing, "
    "loop-friendly structure, relaxed repetition"
)

_TEXTURE = (
    "warm analog saturation, soft tape compression, slightly muted highs, "
    "round transients, subtle room ambience, gentle stereo width"
)

_ARRANGEMENT = (
    "simple repeating progression, restrained melodic movement, clean intro, "
    "consistent middle section, gentle outro"
)


PROMPT_PACKS: Dict[str, List[str]] = {
    "gold_standard_lofi": [
        f"classic crate-dug lofi hip hop instrumental, 78 BPM, dusty boom bap drums, sampled jazz piano chords, warm sub bass, cassette bloom, barely audible vinyl texture, intimate late-night mood, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"nostalgic soul-sample lofi, 82 BPM, chopped harmony, soft kick and snare, mellow bassline, tape wobble, worn sample edges, cozy apartment ambience, understated melodic phrasing, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"guitar-led dusk lofi instrumental, 74 BPM, muted jazz guitar chords instead of dominant piano, soft boom bap pocket, round bass, tiny room reflections, hazy city-night mood, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"rhodes-and-vibes lofi instrumental, 80 BPM, Rhodes harmony with soft vibraphone accents, light dusty drums, supportive bass, gentle tape smear, reflective and spacious but restrained, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"cassette synth lofi instrumental, 72 BPM, detuned analog keys, sleepy drum machine groove, warm bass pillow, blurred tape hiss, overcast dawn atmosphere, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"underground sampler lofi instrumental, 76 BPM, dusty MPC-style drums, clipped sample fragments, upright-style bass movement, muted cymbals, raw but musical beat-tape character, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
    ],
    "clean_lofi_hiphop": [
        f"clean lofi hip hop instrumental, 80 BPM, warm Rhodes chords, gentle boom bap drums, deep supportive bass, minimal top line, focused study mood, polished but not glossy, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"chillhop instrumental, 78 BPM, electric piano loop, brushed snare texture, warm bass movement, smooth harmonic repetition, calm and unobtrusive atmosphere, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"mellow lofi beat, 74 BPM, piano chord motif, laid-back drums, soft sub bass, slightly softened high end, stable arrangement with no surprises, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
    ],
    "focus_room": [
        f"study lofi instrumental, 72 BPM, soft Rhodes, gentle kick-snare groove, warm bass pad, highly repetitive arrangement, no flashy fills, unobtrusive concentration mood, {_GROOVE}, {_TEXTURE}, {_FOUNDATION}",
        f"coding lofi, 76 BPM, electric piano loop, soft drum machine groove, supportive bassline, quiet room tone, very stable energy, minimal melodic variation, {_GROOVE}, {_TEXTURE}, {_FOUNDATION}",
        f"deep focus chillhop, 80 BPM, muted piano voicings, light boom bap drums, smooth bass anchor, minimal arrangement for long listening, {_GROOVE}, {_TEXTURE}, {_FOUNDATION}",
    ],
    "dusty_jazz_cafe": [
        f"jazzy lofi instrumental, 82 BPM, brushed boom bap drums, smoky electric piano, upright-style bass feel, dim cafe ambience, soft tape flutter, cozy rain-on-window atmosphere, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"late-night cafe lofi, 78 BPM, jazz guitar chords, warm bass, dusty snare, intimate room reflections, understated melody, subtle noir mood, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"vinyl jazzhop instrumental, 84 BPM, piano comping, soft swing drums, mellow bass pocket, worn-record texture, relaxed and tasteful phrasing, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
    ],
    "rainy_tape": [
        f"rainy-day lofi instrumental, 70 BPM, warm piano chords, soft boom bap groove, deep bass, blurred tape haze, distant rain texture, reflective and calm, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"sleepy cassette lofi, 74 BPM, electric piano, soft kick, brushed snare, mellow bass, gentle wow and flutter, muted highs, dreamy but rhythmically steady, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"night-rain chillhop instrumental, 78 BPM, Rhodes motif, dusty drums, round bass, washed ambience, repetitive and soothing structure, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
    ],
    "quality_rotate": [
        f"classic lofi hip hop instrumental, 78 BPM, dusty boom bap drums, sampled jazz piano, warm sub bass, beat-tape feel, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"focus lofi instrumental, 76 BPM, soft Rhodes, minimal drum pocket, supportive bass, unobtrusive study energy, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"jazzy cafe chillhop instrumental, 82 BPM, guitar-led harmony, brushed drums, warm bass, intimate room tone, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"rain-soaked lofi instrumental, 72 BPM, mellow piano, soft drums, deep bass, blurred tape mood, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"sleepy cassette synthhop instrumental, 74 BPM, detuned analog keys, dry drums, thick bass cushion, faded-tape atmosphere, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
        f"night bus lofi instrumental, 84 BPM, plucked electric keys, tighter kick-snare pocket, warm bass, close dry room tone, restrained urban motion, {_GROOVE}, {_TEXTURE}, {_ARRANGEMENT}, {_FOUNDATION}",
    ],
}


def get_prompt_pack(name: str = "gold_standard_lofi") -> List[str]:
    if name not in PROMPT_PACKS:
        valid = ", ".join(sorted(PROMPT_PACKS.keys()))
        raise ValueError(f"Unknown prompt pack '{name}'. Valid options: {valid}")
    return PROMPT_PACKS[name]


def list_prompt_packs() -> List[str]:
    return sorted(PROMPT_PACKS.keys())
