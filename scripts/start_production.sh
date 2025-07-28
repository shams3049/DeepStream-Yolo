#!/bin/bash

# Production DeepStream Object Counter Launch Script
# Starts D# Test MQTT broker connectivity
echo "📡 Testing MQTT broker connectivity..."
echo "   Broker: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"

timeout 5 bash -c "</dev/tcp/$MQTT_BROKER_HOST/$MQTT_BROKER_PORT" 2>/dev/null && \
    echo "✅ External MQTT broker reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT" || \
    echo "⚠️  External MQTT broker not reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT (check network connectivity)"

# Test camera connectivity and choose appropriate config
echo "📷 Testing camera connectivity..."
CONFIG_TO_USE="$PRODUCTION_CONFIG"

if timeout 3 ping -c 1 10.20.100.102 >/dev/null 2>&1 && timeout 3 ping -c 1 10.20.100.103 >/dev/null 2>&1; then
    echo "✅ RTSP cameras accessible - using production config"
    CONFIG_TO_USE="$PRODUCTION_CONFIG"
else
    echo "⚠️  RTSP cameras not accessible - using test video config"
    CONFIG_TO_USE="$TEST_CONFIG"
fi

echo "📋 Configuration: $(basename "$CONFIG_TO_USE")"am application with MQTT broadcasting for industrial IoT monitoring

set -e  # Exit on any error

echo "🏭 Starting Production DeepStream Object Counter"
echo "==============================================="
echo "$(date): Initializing production environment..."

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MQTT_CONFIG="$PROJECT_DIR/configs/components/mqtt_broker_config.txt"
PRODUCTION_CONFIG="$PROJECT_DIR/configs/environments/config_sources_production.txt"
TEST_CONFIG="$PROJECT_DIR/configs/environments/config_sources_test_2cam.txt"

# Set environment variables
export CUDA_VER=12.2
export LD_LIBRARY_PATH=/opt/nvidia/deepstream/deepstream/lib:$LD_LIBRARY_PATH

# Set MQTT broker environment variables for external broker
export MQTT_BROKER_HOST=mqtt-proxy.ad.dicodrink.com
export MQTT_BROKER_PORT=1883

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
if [ ! -f "models/yolo11s.onnx" ]; then
    echo "❌ YOLO model not found: models/yolo11s.onnx"
    echo "Please ensure the YOLO11 model is available"
    exit 1
fi

# Create data directory if needed
mkdir -p data/persistence

# Test MQTT broker connectivity
echo "📡 Testing MQTT broker connectivity..."
echo "   Broker: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"

timeout 5 bash -c "</dev/tcp/$MQTT_BROKER_HOST/$MQTT_BROKER_PORT" 2>/dev/null && 
    echo "✅ External MQTT broker reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT" || 
    echo "⚠️  External MQTT broker not reachable at $MQTT_BROKER_HOST:$MQTT_BROKER_PORT (check network connectivity)"

# Display system information
echo "💻 System Information:"
echo "   GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "   Memory: $(free -h | awk '/^Mem:/ {print $2}') total"
echo "   Disk: $(df -h . | awk 'NR==2 {print $4}') available"

# Start MQTT publisher in background
echo "🚀 Starting MQTT publisher..."
python3 src/production_mqtt.py &
MQTT_PID=$!
echo "   MQTT Publisher PID: $MQTT_PID"

# Wait for MQTT initialization
echo "⏱️  Waiting for MQTT initialization..."
sleep 3

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."
    kill $MQTT_PID 2>/dev/null || true
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
python3 src/production_deepstream.py "$CONFIG_TO_USE"

# This point should not be reached unless DeepStream exits normally
echo "📊 DeepStream application completed"
