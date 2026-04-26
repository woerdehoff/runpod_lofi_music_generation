#!/bin/bash
# ============================================================================
#  🎵 ACE-Step Lofi Generator — RunPod Setup Script
#  Author: Adam Woerdehoff
#  Usage:  bash setup_pod.sh
#
#  Safe to run multiple times (idempotent).
#  Designed for RunPod GPU pods with Ubuntu + CUDA pre-installed.
# ============================================================================

set -e  # Exit on error

WORKSPACE="/workspace"
ACE_STEP_DIR="$WORKSPACE/ACE-Step-1.5"
ACE_STEP_REPO="https://github.com/ace-step/ACE-Step-1.5.git"
OUTPUT_DIR="$WORKSPACE/output"
SCRIPTS_DIR="$WORKSPACE"

# ── Colors & Helpers ────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║          🎵  ACE-Step Lofi Generator — Pod Setup  🎵       ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

step()  { echo -e "\n${CYAN}${BOLD}[$1/$TOTAL_STEPS]${NC} $2"; }
ok()    { echo -e "  ${GREEN}✅ $1${NC}"; }
warn()  { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
fail()  { echo -e "  ${RED}❌ $1${NC}"; }
info()  { echo -e "  ${CYAN}ℹ️  $1${NC}"; }

TOTAL_STEPS=8

# ── Start ───────────────────────────────────────────────────────────────────
banner

# ── Step 1: System packages ─────────────────────────────────────────────────
step 1 "Installing system packages..."

apt-get update -qq > /dev/null 2>&1

PACKAGES="ffmpeg git tmux htop nano"
apt-get install -y -qq $PACKAGES > /dev/null 2>&1

ok "Installed: $PACKAGES"

# ── Step 2: Clone ACE-Step 1.5 ──────────────────────────────────────────────
step 2 "Setting up ACE-Step 1.5 repository..."

if [ -d "$ACE_STEP_DIR" ]; then
    ok "ACE-Step repo already exists at $ACE_STEP_DIR"
    cd "$ACE_STEP_DIR"
    git pull --quiet 2>/dev/null || warn "Git pull failed (offline or detached HEAD — no problem)"
else
    info "Cloning ACE-Step 1.5..."
    git clone "$ACE_STEP_REPO" "$ACE_STEP_DIR"
    ok "Cloned to $ACE_STEP_DIR"
    cd "$ACE_STEP_DIR"
fi

# ── Step 3: Python dependencies ─────────────────────────────────────────────
step 3 "Installing Python dependencies..."

if [ -f "$ACE_STEP_DIR/requirements.txt" ]; then
    pip install -q -r "$ACE_STEP_DIR/requirements.txt" 2>/dev/null
    ok "Installed requirements.txt"
else
    warn "No requirements.txt found — skipping (install manually if needed)"
fi

# Extra deps for the pipeline
pip install -q pydub tqdm 2>/dev/null
ok "Installed extras: pydub, tqdm"

# ── Step 4: Create output directories ───────────────────────────────────────
step 4 "Creating output directories..."

mkdir -p "$OUTPUT_DIR/singles"
mkdir -p "$OUTPUT_DIR/albums"

ok "Output dirs ready:"
echo "      $OUTPUT_DIR/singles/"
echo "      $OUTPUT_DIR/albums/"

# ── Step 5: Check for custom scripts ────────────────────────────────────────
step 5 "Checking for your generator scripts..."

SCRIPTS_OK=true

if [ -f "$SCRIPTS_DIR/generate_lofi_runpod_clean.py" ]; then
    ok "generate_lofi_runpod_clean.py found"
else
    warn "generate_lofi_runpod_clean.py NOT found"
    SCRIPTS_OK=false
fi

if [ -f "$SCRIPTS_DIR/prompts.py" ]; then
    ok "prompts.py found"
else
    warn "prompts.py NOT found"
    SCRIPTS_OK=false
fi

if [ "$SCRIPTS_OK" = false ]; then
    echo ""
    warn "Upload your scripts manually. From your LOCAL machine run:"
    echo ""
    echo -e "  ${BOLD}scp -O generate_lofi_runpod_clean.py root@<POD_IP>:/workspace/${NC}"
    echo -e "  ${BOLD}scp -O prompts.py root@<POD_IP>:/workspace/${NC}"
    echo ""
    info "Or set GITHUB_REPO env var to auto-clone (see Step 6)."
fi

# ── Step 6: Auto-pull from GitHub (optional) ────────────────────────────────
step 6 "Checking for GitHub repo (optional)..."

PERSONAL_REPO_DIR="$WORKSPACE/lofi-generator"

if [ -n "$GITHUB_REPO" ]; then
    info "GITHUB_REPO is set: $GITHUB_REPO"
    if [ -d "$PERSONAL_REPO_DIR" ]; then
        cd "$PERSONAL_REPO_DIR"
        git pull --quiet
        ok "Updated $PERSONAL_REPO_DIR"
    else
        git clone "$GITHUB_REPO" "$PERSONAL_REPO_DIR"
        ok "Cloned to $PERSONAL_REPO_DIR"
    fi
    # Symlink scripts into workspace root if they exist in the repo
    for script in generate_lofi_runpod_clean.py prompts.py; do
        if [ -f "$PERSONAL_REPO_DIR/$script" ] && [ ! -f "$SCRIPTS_DIR/$script" ]; then
            ln -sf "$PERSONAL_REPO_DIR/$script" "$SCRIPTS_DIR/$script"
            ok "Symlinked $script → workspace"
        fi
    done
    cd "$WORKSPACE"
else
    info "GITHUB_REPO not set — skipping auto-clone."
    info "To enable, run:  export GITHUB_REPO=https://github.com/youruser/lofi-generator.git"
fi

# ── Step 7: GPU & PyTorch check ─────────────────────────────────────────────
step 7 "Checking GPU and PyTorch..."

echo ""
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1)
    ok "GPU: $GPU_NAME | VRAM: $GPU_VRAM"
else
    fail "nvidia-smi not found — no GPU detected!"
fi

PYTORCH_INFO=$(python3 -c "
import torch
cuda = torch.cuda.is_available()
ver = torch.__version__
dev = torch.cuda.get_device_name(0) if cuda else 'N/A'
print(f'PyTorch {ver} | CUDA available: {cuda} | Device: {dev}')
" 2>/dev/null) || PYTORCH_INFO="PyTorch check failed"

ok "$PYTORCH_INFO"

# ── Step 8: Summary ─────────────────────────────────────────────────────────
step 8 "All done!"

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                   ✅  Setup Complete!                       ║"
echo "  ╠══════════════════════════════════════════════════════════════╣"
echo "  ║                                                              ║"
echo "  ║  ACE-Step repo:  /workspace/ACE-Step-1.5/                    ║"
echo "  ║  Output dir:     /workspace/output/                          ║"
echo "  ║  Scripts dir:    /workspace/                                 ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BOLD}🎧 Quick test (1 track, 2 min, focus_room):${NC}"
echo ""
echo -e "  ${GREEN}python /workspace/generate_lofi_runpod_clean.py \\
    --tracks 1 \\
    --duration 120 \\
    --prompt-pack focus_room \\
    --steps 80 \\
    --guidance 5.0 \\
    --shift 1.9${NC}"
echo ""

echo -e "${BOLD}🎶 Full album (12 tracks, 10 min each → ~2 hour mix):${NC}"
echo ""
echo -e "  ${GREEN}python /workspace/generate_lofi_runpod_clean.py \\
    --tracks 12 \\
    --duration 600 \\
    --prompt-pack quality_rotate \\
    --steps 80 \\
    --guidance 5.0 \\
    --shift 1.85${NC}"
echo ""

echo -e "${BOLD}📂 Available prompt packs:${NC}"
echo "    diverse_lofi       — mixed lofi styles"
echo "    focus_room         — ultra clean study beats"
echo "    traditional_adlibs — classic lofi hip hop"
echo "    quality_rotate     — curated rotation of styles"
echo ""

echo -e "${BOLD}⚡ Safe defaults reminder:${NC}"
echo "    --steps 80"
echo "    --guidance 5.0"
echo "    --shift 1.8–1.9"
echo "    Clip duration ≤ 600s"
echo ""
echo -e "${CYAN}Happy generating! 🎵${NC}"

mv /workspace/ACE-Step-1.5/instruction.txt /workspace/ACE-Step-1.5/instruction.txt.bak
