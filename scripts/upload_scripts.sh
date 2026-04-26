#!/bin/bash
# Upload scripts to RunPod instance
# Usage: ./upload_scripts.sh <POD_IP>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <POD_IP>"
    echo "Example: $0 123.456.789.0"
    exit 1
fi

POD_IP=$1
SCRIPT_DIR="/Users/adam/Documents/GitHub/runpod_lofi_music_generation/scripts"

echo "Uploading scripts to RunPod instance at $POD_IP..."

# Upload each script
scp -O "$SCRIPT_DIR/generate.py" "root@$POD_IP:/workspace/"
scp -O "$SCRIPT_DIR/prompts.py" "root@$POD_IP:/workspace/"
scp -O "$SCRIPT_DIR/setup_pod.sh" "root@$POD_IP:/workspace/"

echo "Upload complete!"
echo ""
echo "Now SSH into your RunPod instance and run:"
echo "  cd /workspace"
echo "  chmod +x setup_pod.sh"
echo "  bash setup_pod.sh"