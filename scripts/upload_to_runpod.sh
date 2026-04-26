#!/bin/bash
# Upload scripts to RunPod instance using your SSH config
# Usage: ./upload_to_runpod.sh

SCRIPT_DIR="/Users/adam/Documents/GitHub/runpod_lofi_music_generation/scripts"
RUNPOD_HOST="3xe0mj6mj61o51-64411507@ssh.runpod.io"
SSH_KEY="~/.ssh/id_ed25519"

echo "Uploading scripts to RunPod instance..."
echo "Host: $RUNPOD_HOST"
echo "Key: $SSH_KEY"
echo ""

# Upload each script using your SSH config
echo "Uploading generate.py..."
scp -i "$SSH_KEY" "$SCRIPT_DIR/generate.py" "$RUNPOD_HOST:/workspace/"

echo "Uploading prompts.py..."
scp -i "$SSH_KEY" "$SCRIPT_DIR/prompts.py" "$RUNPOD_HOST:/workspace/"

echo "Uploading setup_pod.sh..."
scp -i "$SSH_KEY" "$SCRIPT_DIR/setup_pod.sh" "$RUNPOD_HOST:/workspace/"

echo ""
echo "✅ Upload complete!"
echo ""
echo "Now SSH into your RunPod instance:"
echo "ssh -i ~/.ssh/id_ed25519 $RUNPOD_HOST"
echo ""
echo "Then run the setup:"
echo "cd /workspace && chmod +x setup_pod.sh && bash setup_pod.sh"