#!/bin/bash

# Infinite Runner for Tracking-Based DeepStream Application
# This script ensures the application runs indefinitely with automatic restarts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_APP="$WORKSPACE_DIR/src/tracking_deepstream.py"
CONFIG_FILE="$WORKSPACE_DIR/configs/environments/config_sources_production.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 TRACKING-BASED DEEPSTREAM - INFINITE RUNNER${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}📊 Method: NVIDIA Analytics Tracker IDs${NC}"
echo -e "${GREEN}♾️  Running indefinitely with auto-restart${NC}"
echo -e "${GREEN}📋 Config: $CONFIG_FILE${NC}"
echo -e "${GREEN}🔄 Press Ctrl+C to stop${NC}"
echo

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping infinite runner...${NC}"
    # Kill any remaining python processes
    pkill -f "tracking_deepstream.py" 2>/dev/null
    # Clean up any DeepStream resources
    "$SCRIPT_DIR/cleanup_deepstream.sh" 2>/dev/null
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Change to workspace directory
cd "$WORKSPACE_DIR"

# Set MQTT environment variables for external broker
export MQTT_BROKER_HOST=mqtt-proxy.ad.dicodrink.com
export MQTT_BROKER_PORT=1883
export MQTT_BROKER_USER="r_vmays"
export MQTT_BROKER_PASS="csYr9xH&WTfAvMj2"
export MQTT_CLIENT_ID="deepstream-production-counter"

# Set DeepStream environment variables
export CUDA_VER=12.2
export LD_LIBRARY_PATH=/opt/nvidia/deepstream/deepstream/lib:$LD_LIBRARY_PATH

# Main infinite loop
restart_count=0
max_restarts_per_hour=20
start_time=$(date +%s)

while true; do
    # Check if we've restarted too many times in the last hour
    current_time=$(date +%s)
    time_diff=$((current_time - start_time))
    
    if [ $time_diff -gt 3600 ]; then
        # Reset counters every hour
        restart_count=0
        start_time=$current_time
    fi
    
    if [ $restart_count -ge $max_restarts_per_hour ]; then
        echo -e "${RED}❌ Too many restarts ($restart_count) in the last hour. Pausing for 10 minutes...${NC}"
        sleep 600  # Wait 10 minutes
        restart_count=0
        start_time=$(date +%s)
    fi
    
    restart_count=$((restart_count + 1))
    echo -e "${BLUE}🚀 Starting tracking application (restart #$restart_count)${NC}"
    echo -e "${BLUE}   Time: $(date)${NC}"
    
    # Run the Python application
    python3 "$PYTHON_APP" "$CONFIG_FILE"
    exit_code=$?
    
    echo -e "${YELLOW}⚠️  Application stopped with exit code: $exit_code${NC}"
    
    # If exit was clean (Ctrl+C), don't restart
    if [ $exit_code -eq 0 ] || [ $exit_code -eq 130 ]; then
        echo -e "${GREEN}✅ Clean exit detected. Stopping infinite runner.${NC}"
        break
    fi
    
    # Clean up any leftover processes
    echo -e "${YELLOW}🧹 Cleaning up resources...${NC}"
    "$SCRIPT_DIR/cleanup_deepstream.sh" 2>/dev/null
    
    # Wait before restart
    echo -e "${YELLOW}⏳ Waiting 15 seconds before restart...${NC}"
    sleep 15
done

echo -e "${GREEN}🏁 Infinite runner stopped${NC}"
