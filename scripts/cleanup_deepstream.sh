#!/bin/bash

# DeepStream Cleanup Script
# Forcefully stops all DeepStream processes and cleans up resources

echo "🧹 DeepStream System Cleanup"
echo "============================"

# Kill all DeepStream related processes
echo "🛑 Stopping DeepStream processes..."
pkill -f "deepstream-app" 2>/dev/null && echo "   ✅ Stopped deepstream-app" || echo "   ℹ️  No deepstream-app processes found"
pkill -f "tracking_deepstream.py" 2>/dev/null && echo "   ✅ Stopped tracking_deepstream.py" || echo "   ℹ️  No tracking_deepstream.py processes found"
pkill -f "tracking_mqtt.py" 2>/dev/null && echo "   ✅ Stopped tracking_mqtt.py" || echo "   ℹ️  No tracking_mqtt.py processes found"
pkill -f "production_deepstream.py" 2>/dev/null && echo "   ✅ Stopped production_deepstream.py" || echo "   ℹ️  No production_deepstream.py processes found"

# Kill any python processes using GStreamer
echo "🐍 Stopping Python GStreamer processes..."
pkill -f "python.*gst" 2>/dev/null && echo "   ✅ Stopped Python GStreamer processes" || echo "   ℹ️  No Python GStreamer processes found"

# Clean up shared memory
echo "💾 Cleaning shared memory..."
rm -f /dev/shm/nvds* 2>/dev/null && echo "   ✅ Cleaned DeepStream shared memory" || echo "   ℹ️  No DeepStream shared memory found"

# Reset GPU if possible
echo "🎮 Resetting GPU resources..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --gpu-reset 2>/dev/null && echo "   ✅ GPU reset completed" || echo "   ⚠️  GPU reset failed (may require sudo)"
else
    echo "   ⚠️  nvidia-smi not available"
fi

# Clear any stuck GStreamer registry
echo "🎬 Cleaning GStreamer registry..."
rm -rf ~/.cache/gstreamer-1.0 2>/dev/null && echo "   ✅ Cleared GStreamer cache" || echo "   ℹ️  No GStreamer cache found"

# Give everything time to cleanup
echo "⏱️  Waiting for cleanup to complete..."
sleep 3

echo ""
echo "✅ Cleanup completed! You can now run the DeepStream application again."
echo "💡 Usage: ./scripts/start_production.sh"
