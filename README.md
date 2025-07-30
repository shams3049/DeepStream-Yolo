# DeepStream Object Counter - Production Documentation

## Overview

Production-ready NVIDIA DeepStream application for real-time object counting with MQTT broadcasting. Uses tracking-based counting for accurate results and persistent storage for 24/7 operation.

**Key Capabilities:**
- Real-time object detection and counting using YOLO11
- RTSP camera support (multiple streams)  
- MQTT real-time broadcasting
- Persistent count storage across restarts
- Auto-restart functionality for 24/7 operation
- System health monitoring

## Quick Start

### 1. Launch Production Mode
```bash
# Interactive mode (choose option 2 for production)
./scripts/start_production.sh

# Direct infinite mode for 24/7 operation
./scripts/start_production.sh --mode infinite
```

### 2. Test MQTT Reception
```bash
python3 scripts/test_mqtt_subscriber.py
```

## System Requirements

- **Hardware**: NVIDIA Jetson or GPU-enabled system
- **Software**: NVIDIA DeepStream SDK 7.x, CUDA 12.2+
- **Python**: 3.8+ with `paho-mqtt`, `psutil`
- **Network**: RTSP camera access, MQTT broker connectivity

## Configuration

### MQTT Broker Setup
File: `configs/components/mqtt_broker_config.txt`
```ini
[message-broker]
username = r_vmays
password = csYr9xH&WTfAvMj2
client-id = deepstream-production-counter
keep-alive = 60
```

**Environment Variables** (overrides file config):
```bash
export MQTT_BROKER_HOST=mqtt-proxy.ad.dicodrink.com
export MQTT_BROKER_PORT=1883
export MQTT_BROKER_USER=r_vmays
export MQTT_BROKER_PASS=csYr9xH&WTfAvMj2
```

### Camera Sources
File: `configs/environments/config_sources_production.txt`

**RTSP Camera Configuration:**
```ini
[source0]
enable=1
type=4
uri=rtsp://admin:%23DDuDU2025%21@10.20.100.102:554/cam/realmonitor?channel=1&subtype=0
num-sources=1

[source1]
enable=1
type=4
uri=rtsp://admin:%23DDuDU2025%21@10.20.100.103:554/cam/realmonitor?channel=1&subtype=0
num-sources=1
```

**Add More Cameras:**
- Add `[source2]`, `[source3]` sections
- Update `[tiled-display]` rows/columns
- Update `[streammux]` batch-size

## MQTT Data Structure

### Count Messages (Published every 1 second per camera)
**Topics:** `camera1/tracking`, `camera2/tracking`, etc.

```json
{
  "timestamp": "2025-07-30T12:31:45.123456",
  "source_id": 0,
  "camera_name": "Camera 1 (102)",
  "camera_ip": "10.20.100.102",
  "location": "Production Area 1",
  "counting_method": "tracker_ids",
  "unique_objects_tracked": 15,
  "session_new_objects": 3,
  "total_objects_detected": 158,
  "can_count": 158,
  "tracked_object_ids": [1, 5, 12, 18, 22],
  "message_type": "tracking_count_update"
}
```

### System Health (Published every 5 seconds)
**Topic:** `deepstream/health`

```json
{
  "timestamp": "2025-07-30T12:31:45.123456",
  "system_status": "healthy",
  "deepstream_running": true,
  "cpu_usage": "45.2%",
  "memory_usage": "68.1%",
  "disk_usage": "34.5%",
  "gpu_info": "NVIDIA Jetson AGX Orin",
  "total_unique_objects": 45,
  "total_session_objects": 12,
  "total_persistent_count": 1247,
  "active_streams": 2,
  "uptime": "2 days, 14:23:15"
}
```

### Analytics Summary (Published every 10 seconds)
**Topic:** `deepstream/analytics`

```json
{
  "timestamp": "2025-07-30T12:31:45.123456",
  "counting_method": "nvidia_analytics_tracker_ids",
  "total_unique_objects_tracked": 45,
  "total_session_new_objects": 12,
  "total_persistent_count": 1247,
  "active_streams": 2,
  "per_stream_breakdown": {
    "0": {"unique": 23, "session": 7, "total": 623},
    "1": {"unique": 22, "session": 5, "total": 624}
  }
}
```

## Data Persistence

**Location:** `data/persistence/`

### tracking_counts.json
```json
{
  "stream_0": {"session_count": 7, "total_count": 623, "last_update": "2025-07-30T12:31:45"},
  "stream_1": {"session_count": 5, "total_count": 624, "last_update": "2025-07-30T12:31:45"}
}
```

### live_counts.json
```json
{
  "timestamp": "2025-07-30T12:31:45.123456",
  "session_counts": {"0": 7, "1": 5},
  "stream_totals": {"0": 623, "1": 624}
}
```

## Project Structure

```
📁 configs/
  📁 components/              # Component configurations
    📄 config_infer_primary_yolo11.txt    # YOLO inference config
    📄 mqtt_broker_config.txt             # MQTT broker settings
    📄 nvdsanalytics_config.txt           # Analytics configuration
    📄 tracker_config.txt                 # Object tracker settings
    📄 msg_config.txt                     # Message format config
  📁 environments/            # Environment configurations  
    📄 config_sources_production.txt      # Production camera config

📁 data/
  📁 persistence/             # Persistent count storage
    📄 tracking_counts.json               # Per-stream counts
    📄 live_counts.json                   # Live session data

📁 scripts/                   # Essential scripts
  📄 start_production.sh                 # Main launcher
  📄 run_tracking_indefinitely.sh       # 24/7 infinite runner
  📄 cleanup_deepstream.sh              # System cleanup
  📄 test_mqtt_subscriber.py            # MQTT test tool

📁 src/                      # Core application
  📄 tracking_deepstream.py             # Main DeepStream app
  📄 tracking_mqtt.py                   # MQTT publisher
  📄 tracking_based_counter.py          # Counting logic

📁 models/                   # YOLO models
  📄 model_b1_gpu0_fp32.engine          # TensorRT engine
  📄 yolo11s.onnx                       # ONNX model
  📄 labels.txt                         # Class labels

📁 nvdsinfer_custom_impl_Yolo/         # Custom inference library
```

## Operation Modes

### 1. Interactive Mode
```bash
./scripts/start_production.sh
```
- Choose option 1: Basic GUI only
- Choose option 2: Production with MQTT + persistence

### 2. Infinite Runner (24/7)
```bash
./scripts/start_production.sh --mode infinite
```
- Automatic restart on failure
- Continuous operation
- Health monitoring and recovery
- Maximum 20 restarts per hour protection

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Check imports
python3 -c "from src.tracking_deepstream import *; print('✅ OK')"
```

**GPU Issues:**
```bash
# Clean up GPU resources
./scripts/cleanup_deepstream.sh
nvidia-smi
```

**MQTT Connection:**
```bash
# Test MQTT connectivity
timeout 5 bash -c "</dev/tcp/mqtt-proxy.ad.dicodrink.com/1883"
```

**Camera Connectivity:**
```bash
# Test RTSP streams
timeout 3 ping -c 1 10.20.100.102
timeout 3 ping -c 1 10.20.100.103
```

### Performance Optimization

**Expected Performance:**
- **FPS**: 25+ per camera stream
- **Latency**: <100ms end-to-end
- **Accuracy**: >95% tracking consistency

**Resource Usage:**
- **CPU**: <70% sustained
- **Memory**: <80% of available
- **GPU**: DeepStream optimized

### Monitoring Commands

**Check Application Status:**
```bash
ps aux | grep tracking_deepstream
ps aux | grep tracking_mqtt
```

**Monitor MQTT Messages:**
```bash
python3 scripts/test_mqtt_subscriber.py
```

**Check Data Persistence:**
```bash
cat data/persistence/tracking_counts.json
cat data/persistence/live_counts.json
```

**System Health:**
```bash
nvidia-smi
htop
df -h
```

## Technical Details

### Counting Method
- **Technology**: NVIDIA Analytics Tracker IDs
- **Accuracy**: Unique object tracking (no duplicates)
- **Performance**: Hardware-accelerated GPU processing
- **Persistence**: JSON storage with atomic writes

### DeepStream Pipeline
1. **RTSP Source** → Video decode (NVDEC)
2. **Stream Mux** → Batch processing  
3. **Primary GIE** → YOLO11 inference (TensorRT)
4. **Tracker** → NVIDIA Multi-Object Tracker
5. **OSD** → On-screen display overlay
6. **Sink** → Display output

### MQTT Architecture
- **Publisher**: Separate thread for non-blocking operation
- **QoS**: Level 0 (fire-and-forget for performance)
- **Reconnection**: Automatic with exponential backoff
- **Topics**: Structured hierarchy for different data types

## Maintenance

### Regular Tasks
- Monitor disk space in `data/persistence/`
- Check MQTT broker connectivity
- Verify camera stream health
- Review system performance metrics

### Updates
- YOLO models: Replace in `models/` directory
- Configuration: Update relevant config files
- Restart: Use infinite runner for automatic recovery

### Backup
```bash
# Backup persistent data
cp -r data/persistence/ backup/persistence-$(date +%Y%m%d)/

# Backup configurations
cp -r configs/ backup/configs-$(date +%Y%m%d)/
```

---

**For technical support or issues, check the troubleshooting section above or review system logs.**
