#!/bin/bash

# Production DeepStream Object Counter Launch Script
# Starts DeepStream application with MQTT broadcasting for industrial IoT monitoring

set -e  # Exit on any error

echo "🏭 Production DeepStream Object Counter"
echo "==============================================="
echo "$(date): Initializing production environment..."

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MQTT_CONFIG="$PROJECT_DIR/configs/components/mqtt_broker_config.txt"
PRODUCTION_CONFIG="$PROJECT_DIR/configs/environments/config_sources_production.txt"

# Set environment variables
export CUDA_VER=12.2
export LD_LIBRARY_PATH=/opt/nvidia/deepstream/deepstream/lib:$LD_LIBRARY_PATH

# Set MQTT broker environment variables for external broker
export MQTT_BROKER_HOST=mqtt-proxy.ad.dicodrink.com
export MQTT_BROKER_PORT=1883
export MQTT_BROKER_USER="r_vmays"
export MQTT_BROKER_PASS="csYr9xH&WTfAvMj2"

# Change to project directory
cd "$PROJECT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Clean up any existing processes from previous runs
echo "🧹 Cleaning up previous instances..."
pkill -f "deepstream-app" 2>/dev/null || true
pkill -f "tracking_deepstream.py" 2>/dev/null || true
pkill -f "tracking_mqtt.py" 2>/dev/null || true
pkill -f "production_deepstream.py" 2>/dev/null || true
sleep 2

# Verify prerequisites
echo "🔍 Verifying system requirements..."

# Check DeepStream installation
if [ ! -d "/opt/nvidia/deepstream/deepstream" ]; then
    echo "❌ DeepStream SDK not found. Please install DeepStream 7.x"
    exit 1
fi

# Check GPU availability
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA GPU not detected. Please install NVIDIA drivers"
    exit 1
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
python3 -c "import paho.mqtt.client as mqtt; import psutil" 2>/dev/null || {
    echo "❌ Missing Python dependencies. Run: pip3 install paho-mqtt psutil"
    exit 1
}

# Verify configuration files
echo "⚙️  Verifying configuration files..."
if [ ! -f "$MQTT_CONFIG" ]; then
    echo "❌ MQTT configuration not found: $MQTT_CONFIG"
    echo "Please configure MQTT broker settings"
    exit 1
fi

if [ ! -f "$PRODUCTION_CONFIG" ]; then
    echo "❌ Production configuration not found: $PRODUCTION_CONFIG"
    echo "Please configure camera sources"
    exit 1
fi

# Check YOLO model
if [ ! -f "models/model_b1_gpu0_fp32.engine" ]; then
    echo "❌ YOLO engine model not found: models/model_b1_gpu0_fp32.engine"
    if [ -f "models/yolo11s.onnx" ]; then
        echo "📦 ONNX model found, TensorRT engine will be generated automatically"
    else
        echo "❌ No YOLO model found. Please ensure a YOLO model is available"
        exit 1
    fi
fi

# Create data directory if needed
mkdir -p data/persistence

# Clean up any stuck shared memory or GPU resources
echo "🔧 Ensuring GPU resources are available..."
nvidia-smi --gpu-reset 2>/dev/null || true

# Test camera connectivity and choose appropriate config
echo "📷 Testing camera connectivity..."

if timeout 3 ping -c 1 10.20.100.102 >/dev/null 2>&1 && timeout 3 ping -c 1 10.20.100.103 >/dev/null 2>&1; then
    echo "✅ Both RTSP cameras (10.20.100.102, 10.20.100.103) are accessible"
    
    # Ask user for mode selection
    echo ""
    echo "🔧 Configuration Options:"
    echo "1) Basic mode (display only, no MQTT)"
    echo "2) Production mode (with MQTT and persistent counting)"
    echo ""
    read -p "Choose mode (1/2) [default: 2]: " mode_choice
    mode_choice=${mode_choice:-2}  # Default to production mode
    
    if [ "$mode_choice" = "2" ]; then
        echo "🔄 Enabling production mode with MQTT and persistent counting..."
        
        # Test MQTT broker connectivity
        echo "📡 Testing MQTT broker connectivity..."
        echo "   Broker: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"
        
        timeout 5 bash -c "</dev/tcp/$MQTT_BROKER_HOST/$MQTT_BROKER_PORT" 2>/dev/null && \
            echo "✅ MQTT broker reachable" || \
            echo "⚠️  MQTT broker not reachable (will continue without MQTT)"
    else
        echo "📺 Running in basic display mode"
    fi
else
    echo "⚠️  RTSP cameras not accessible - please check camera connections"
    echo "🔧 Continuing with production config (cameras may auto-reconnect)"
    mode_choice="2"  # Default to production mode even without cameras
fi

# Display system information
echo "💻 System Information:"
echo "   GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "   Memory: $(free -h | awk '/^Mem:/ {print $2}') total"
echo "   Disk: $(df -h . | awk 'NR==2 {print $4}') available"

# Start MQTT publisher in background (only if full production mode is selected)
MQTT_PID=""
if [ "$mode_choice" = "2" ]; then
    echo "🚀 MQTT publisher will start alongside DeepStream GUI..."
else
    echo "📺 Skipping MQTT publisher (basic mode selected)"
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [--mode MODE]"
    echo "Modes:"
    echo "  1 - Basic GUI Mode"
    echo "  2 - Production Mode (GUI + MQTT + Persistent Counting)"  
    echo "  infinite - Infinite Runner with Auto-restart (Production Mode)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Interactive mode selection"
    echo "  $0 --mode infinite    # Run with infinite auto-restart"
    exit 0
}

# Parse command line arguments  
INFINITE_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            if [ "$2" = "infinite" ]; then
                INFINITE_MODE=true
            fi
            shift 2
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            echo "Unknown option $1"
            show_usage
            ;;
    esac
done

# If infinite mode requested, hand off to infinite runner
if [ "$INFINITE_MODE" = true ]; then
    echo "♾️  Starting Infinite Runner Mode..."
    exec "$PROJECT_DIR/scripts/run_tracking_indefinitely.sh"
fi
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."
    
    # Kill all related processes
    pkill -f "deepstream-app" 2>/dev/null || true
    pkill -f "tracking_deepstream.py" 2>/dev/null || true
    pkill -f "tracking_mqtt.py" 2>/dev/null || true
    
    if [ -n "$MQTT_PID" ]; then
        kill $MQTT_PID 2>/dev/null || true
        echo "   Stopped MQTT publisher"
    fi
    
    # Clean up any GPU resources
    nvidia-smi --gpu-reset 2>/dev/null || true
    
    # Give processes time to cleanup
    sleep 2
    
    echo "✅ Production session completed"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start DeepStream application
echo "🎥 Starting DeepStream application..."
echo "   Configuration: $(basename "$PRODUCTION_CONFIG")"
echo "   Press Ctrl+C to stop"
echo ""

# Run DeepStream application with tracking-based counter
if [ "$mode_choice" = "2" ]; then
    echo "🎯 Running DeepStream with Production Mode..."
    echo "📊 Features: Live video + MQTT broadcasting + Persistent counting"
    echo "� Using tracking-based object counter for maximum accuracy"
    echo ""
    
    python3 src/tracking_deepstream.py "$PRODUCTION_CONFIG"
else
    echo "🎯 Running DeepStream in Basic Mode..."
    echo "� Features: Live video display only"
    echo "� Using tracking-based object counter"
    echo ""
    
    python3 src/tracking_deepstream.py "$PRODUCTION_CONFIG"
fi

# This point should not be reached unless DeepStream exits normally
echo "📊 DeepStream application completed"
