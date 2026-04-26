#!/bin/bash
# ============================================================================
#  🎵 ACE-Step Lofi Generator — RunPod Setup Script
#  Author: Adam Woerdehoff
#  Usage:  bash setup_pod.sh
#
#  Safe to run multiple times (idempotent).
#  Designed for RunPod GPU pods with Ubuntu + CUDA pre-installed.
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

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

# Enhanced error handling
error_exit() {
    echo -e "\n${RED}❌ Setup failed at step $1: $2${NC}" >&2
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Safe package installation (check if already installed)
install_if_missing() {
    local package=$1
    if dpkg -l | grep -q "^ii  $package "; then
        info "$package already installed"
    else
        info "Installing $package..."
        if ! apt-get install -y -qq "$package" >/dev/null 2>&1; then
            fail "Failed to install $package"
        fi
    fi
}

TOTAL_STEPS=8

# ── Start ───────────────────────────────────────────────────────────────────
banner

# ── Step 1: System packages ─────────────────────────────────────────────────
step 1 "Installing system packages..."

# Update package list quietly
info "Updating package list..."
if ! apt-get update -qq >/dev/null 2>&1; then
    warn "apt-get update failed, but continuing..."
fi

# Install required packages
PACKAGES="ffmpeg git tmux htop nano"
for pkg in $PACKAGES; do
    install_if_missing "$pkg"
done

ok "All system packages ready"

# ── Step 2: Clone ACE-Step 1.5 ──────────────────────────────────────────────
step 2 "Setting up ACE-Step 1.5 repository..."

if [ -d "$ACE_STEP_DIR" ]; then
    ok "ACE-Step repo already exists at $ACE_STEP_DIR"
    cd "$ACE_STEP_DIR"
    if git pull --quiet 2>/dev/null; then
        ok "Repository updated"
    else
        warn "Git pull failed (offline or detached HEAD — no problem)"
    fi
else
    info "Cloning ACE-Step 1.5..."
    if git clone "$ACE_STEP_REPO" "$ACE_STEP_DIR" 2>/dev/null; then
        ok "Cloned to $ACE_STEP_DIR"
        cd "$ACE_STEP_DIR"
    else
        fail "Failed to clone ACE-Step repository"
    fi
fi

# Verify the repository structure
if [ ! -f "$ACE_STEP_DIR/cli.py" ]; then
    fail "ACE-Step repository appears incomplete (missing cli.py)"
fi

# ── Step 3: Python dependencies ─────────────────────────────────────────────
step 3 "Installing Python dependencies..."

# Check if Python 3 is available
if ! command_exists python3; then
    fail "Python 3 not found"
fi

info "Python version: $(python3 --version)"

cd "$ACE_STEP_DIR"

if [ -f "requirements.txt" ]; then
    info "Installing ACE-Step requirements..."
    if pip install -q -r requirements.txt 2>/dev/null; then
        ok "ACE-Step requirements installed"
    else
        fail "Failed to install ACE-Step requirements"
    fi
else
    warn "No requirements.txt found in ACE-Step repo"
fi

# Install additional dependencies
info "Installing additional dependencies..."
EXTRA_PACKAGES="pydub tqdm"
if pip install -q $EXTRA_PACKAGES 2>/dev/null; then
    ok "Extra packages installed: $EXTRA_PACKAGES"
else
    fail "Failed to install extra packages"
fi

# ── Step 4: Create output directories ───────────────────────────────────────
step 4 "Creating output directories..."

mkdir -p "$OUTPUT_DIR/singles"
mkdir -p "$OUTPUT_DIR/albums"

if [ -d "$OUTPUT_DIR/singles" ] && [ -d "$OUTPUT_DIR/albums" ]; then
    ok "Output directories ready:"
    echo "      $OUTPUT_DIR/singles/"
    echo "      $OUTPUT_DIR/albums/"
else
    fail "Failed to create output directories"
fi

# ── Step 5: Check for custom scripts ────────────────────────────────────────
step 5 "Checking for your generator scripts..."

SCRIPTS_OK=true
MISSING_SCRIPTS=""

check_script() {
    local script=$1
    if [ -f "$SCRIPTS_DIR/$script" ]; then
        ok "$script found"
    else
        warn "$script NOT found"
        SCRIPTS_OK=false
        MISSING_SCRIPTS="$MISSING_SCRIPTS $script"
    fi
}

check_script "generate.py"
check_script "prompts.py"

if [ "$SCRIPTS_OK" = false ]; then
    echo ""
    warn "Missing scripts:$MISSING_SCRIPTS"
    echo ""
    info "Upload your scripts manually. From your LOCAL machine run:"
    echo ""
    for script in $MISSING_SCRIPTS; do
        echo -e "  ${BOLD}scp -O $script root@<POD_IP>:/workspace/${NC}"
    done
    echo ""
    info "Or set GITHUB_REPO env var to auto-clone (see Step 6)."
fi

# ── Step 6: Auto-pull from GitHub (optional) ────────────────────────────────
step 6 "Checking for GitHub repo (optional)..."

PERSONAL_REPO_DIR="$WORKSPACE/lofi-generator"

if [ -n "${GITHUB_REPO:-}" ]; then
    info "GITHUB_REPO is set: $GITHUB_REPO"
    if [ -d "$PERSONAL_REPO_DIR" ]; then
        cd "$PERSONAL_REPO_DIR"
        if git pull --quiet 2>/dev/null; then
            ok "Updated $PERSONAL_REPO_DIR"
        else
            warn "Failed to update personal repo"
        fi
    else
        if git clone "$GITHUB_REPO" "$PERSONAL_REPO_DIR" 2>/dev/null; then
            ok "Cloned personal repo to $PERSONAL_REPO_DIR"
        else
            warn "Failed to clone personal repo"
        fi
    fi

    # Symlink scripts into workspace root if they exist in the repo
    if [ -d "$PERSONAL_REPO_DIR" ]; then
        for script in generate.py prompts.py; do
            if [ -f "$PERSONAL_REPO_DIR/$script" ] && [ ! -f "$SCRIPTS_DIR/$script" ]; then
                ln -sf "$PERSONAL_REPO_DIR/$script" "$SCRIPTS_DIR/$script"
                ok "Symlinked $script → workspace"
            fi
        done
    fi
    cd "$WORKSPACE"
else
    info "GITHUB_REPO not set — skipping auto-clone."
    info "To enable, run:  export GITHUB_REPO=https://github.com/youruser/lofi-generator.git"
fi

# ── Step 7: GPU & PyTorch check ─────────────────────────────────────────────
step 7 "Checking GPU and PyTorch..."

echo ""
if command_exists nvidia-smi; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU_NAME" ]; then
        ok "GPU: $GPU_NAME | VRAM: $GPU_VRAM"
    else
        warn "GPU detected but unable to query details"
    fi
else
    fail "nvidia-smi not found — no GPU detected!"
fi

# Check PyTorch installation
if python3 -c "import torch; print('PyTorch available')" 2>/dev/null; then
    PYTORCH_INFO=$(python3 -c "
import torch
cuda = torch.cuda.is_available()
ver = torch.__version__
dev = torch.cuda.get_device_name(0) if cuda else 'N/A'
print(f'PyTorch {ver} | CUDA available: {cuda} | Device: {dev}')
" 2>/dev/null) || PYTORCH_INFO="PyTorch check failed"
    ok "$PYTORCH_INFO"
else
    fail "PyTorch not properly installed"
fi

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

# Final validation
echo ""
info "Running final validation..."

# Check that all critical components are in place
VALIDATION_PASSED=true

if [ ! -d "$ACE_STEP_DIR" ] || [ ! -f "$ACE_STEP_DIR/cli.py" ]; then
    warn "ACE-Step repository validation failed"
    VALIDATION_PASSED=false
fi

if ! python3 -c "import torch; import pydub; import tqdm" 2>/dev/null; then
    warn "Python dependencies validation failed"
    VALIDATION_PASSED=false
fi

if ! command_exists ffmpeg; then
    warn "ffmpeg validation failed"
    VALIDATION_PASSED=false
fi

if [ "$VALIDATION_PASSED" = true ]; then
    ok "All validations passed!"
else
    warn "Some validations failed, but setup completed"
fi

echo ""
echo -e "${BOLD}🎧 Quick test (1 track, 2 min, focus_room):${NC}"
echo ""
echo -e "  ${GREEN}python /workspace/generate.py \\
    --test \\
    --prompt-pack focus_room \\
    --clean${NC}"
echo ""

echo -e "${BOLD}🎶 Full album (10 tracks, 3 min each, 3 candidates):${NC}"
echo ""
echo -e "  ${GREEN}python /workspace/generate.py \\
    --tracks 10 \\
    --duration 180 \\
    --prompt-pack quality_rotate \\
    --candidates 3 \\
    --clean${NC}"
echo ""

echo -e "${BOLD}📂 Available prompt packs:${NC}"
echo "    gold_standard_lofi — strongest default beat-tape style"
echo "    clean_lofi_hiphop  — balanced and production-safe"
echo "    focus_room         — ultra clean study beats"
echo "    dusty_jazz_cafe    — warmer jazz-cafe mood"
echo "    rainy_tape         — softer tape-haze mood"
echo "    quality_rotate     — curated rotation of styles"
echo ""

echo -e "${BOLD}⚡ Safe defaults reminder:${NC}"
echo "    --steps 96"
echo "    --guidance 4.5"
echo "    --shift 1.55"
echo "    Default candidates: 3 (2 in --test)"
echo "    Clip duration <= 480s"
echo ""
echo -e "${CYAN}Happy generating! 🎵${NC}"
