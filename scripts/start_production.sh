#!/bin/bash

# Production DeepStream Object Counter Launch Script
# Starts DeepStream application with MQTT broadcasting for industrial IoT monitoring

set -e  # Exit on any error

echo "🏭 Starting Production DeepStream Object Counter"
echo "==============================================="
echo "$(date): Initializing production environment..."

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MQTT_CONFIG="$PROJECT_DIR/configs/components/mqtt_broker_config.txt"
PRODUCTION_CONFIG="$PROJECT_DIR/configs/environments/config_sources_production.txt"
TEST_CONFIG="$PROJECT_DIR/configs/environments/config_test_simple.txt"

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

# Test camera connectivity and choose appropriate config
echo "📷 Testing camera connectivity..."
CONFIG_TO_USE="$PRODUCTION_CONFIG"

if timeout 3 ping -c 1 10.20.100.102 >/dev/null 2>&1 && timeout 3 ping -c 1 10.20.100.103 >/dev/null 2>&1; then
    echo "✅ Both RTSP cameras (10.20.100.102, 10.20.100.103) are accessible"
    CONFIG_TO_USE="$PRODUCTION_CONFIG"
    
    # Ask user if they want to enable MQTT and analytics
    echo ""
    echo "🔧 Configuration Options:"
    echo "1) Basic mode (display only, no MQTT/analytics) - RECOMMENDED for testing"
    echo "2) Full production mode (with MQTT and analytics)"
    echo ""
    read -p "Choose mode (1/2) [default: 1]: " mode_choice
    
    if [ "$mode_choice" = "2" ]; then
        echo "🔄 Enabling MQTT and analytics features..."
        # Enable MQTT sink
        sed -i 's/^\[sink1\]/[sink1]/; /^\[sink1\]/,/^\[/ s/enable=0/enable=1/' "$CONFIG_TO_USE"
        # Enable analytics
        sed -i 's/^\[nvds-analytics\]/[nvds-analytics]/; /^\[nvds-analytics\]/,/^\[/ s/enable=0/enable=1/' "$CONFIG_TO_USE"
        
        # Test MQTT broker connectivity
        echo "📡 Testing MQTT broker connectivity..."
        echo "   Broker: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"
        
        timeout 5 bash -c "</dev/tcp/$MQTT_BROKER_HOST/$MQTT_BROKER_PORT" 2>/dev/null && \
            echo "✅ External MQTT broker reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT" || \
            echo "⚠️  External MQTT broker not reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT (will continue without MQTT)"
    else
        echo "📺 Running in basic display mode (MQTT and analytics disabled)"
        # Ensure MQTT and analytics are disabled
        sed -i 's/^\[sink1\]/[sink1]/; /^\[sink1\]/,/^\[/ s/enable=1/enable=0/' "$CONFIG_TO_USE"
        sed -i 's/^\[nvds-analytics\]/[nvds-analytics]/; /^\[nvds-analytics\]/,/^\[/ s/enable=1/enable=0/' "$CONFIG_TO_USE"
    fi
else
    echo "⚠️  RTSP cameras not accessible - using test config with simple setup"
    CONFIG_TO_USE="$TEST_CONFIG"
fi

echo "📋 Using configuration: $(basename "$CONFIG_TO_USE")"

# Display system information
echo "💻 System Information:"
echo "   GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "   Memory: $(free -h | awk '/^Mem:/ {print $2}') total"
echo "   Disk: $(df -h . | awk 'NR==2 {print $4}') available"

# Start MQTT publisher in background (only if MQTT is enabled)
MQTT_PID=""
if [ "$mode_choice" = "2" ]; then
    echo "🚀 Starting MQTT publisher..."
    if [ -f "src/production_mqtt.py" ]; then
        python3 src/production_mqtt.py &
        MQTT_PID=$!
        echo "   MQTT Publisher PID: $MQTT_PID"
        
        # Wait for MQTT initialization
        echo "⏱️  Waiting for MQTT initialization..."
        sleep 3
    else
        echo "⚠️  MQTT publisher script not found, continuing without MQTT"
    fi
else
    echo "📺 Skipping MQTT publisher (basic mode selected)"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."
    if [ -n "$MQTT_PID" ]; then
        kill $MQTT_PID 2>/dev/null || true
        echo "   Stopped MQTT publisher"
    fi
    echo "✅ Production session completed"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start DeepStream application
echo "🎥 Starting DeepStream application..."
echo "   Configuration: $(basename "$CONFIG_TO_USE")"
echo "   Press Ctrl+C to stop"
echo ""

# Run DeepStream application with selected config
if [ -f "src/analytics_stream_counter.py" ]; then
    echo "🎯 Running DeepStream with Enhanced Analytics Stream Counter..."
    echo "📊 Features: NVIDIA Analytics integration, per-stream counting, live overlay"
    python3 src/analytics_stream_counter.py "$CONFIG_TO_USE"
elif [ -f "src/advanced_live_counter.py" ]; then
    echo "📊 Running DeepStream with advanced live object counting..."
    echo "📊 Features: Real-time counting, GUI overlay, persistent storage"
    python3 src/advanced_live_counter.py "$CONFIG_TO_USE"
elif [ -f "src/simple_live_counter.py" ]; then
    echo "📊 Running DeepStream with simple live counting..."
    python3 src/simple_live_counter.py "$CONFIG_TO_USE"
elif [ -f "src/production_deepstream.py" ]; then
    python3 src/production_deepstream.py "$CONFIG_TO_USE"
else
    echo "📱 Running direct DeepStream application..."
    deepstream-app -c "$CONFIG_TO_USE"
fi

# This point should not be reached unless DeepStream exits normally
echo "📊 DeepStream application completed"
