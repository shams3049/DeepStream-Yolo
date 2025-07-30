# DeepStream-Yolo Production Setup

## Overview
This is a streamlined DeepStream application for production object counting with MQTT broadcasting and persistent count storage.

## Key Features
- **Tracking-based counting**: Uses NVIDIA Analytics tracker IDs for accurate object counting
- **MQTT broadcasting**: Real-time count data publishing to external broker
- **Persistent storage**: Counts are saved and restored across restarts
- **Infinite mode**: Auto-restart capability for 24/7 operation

## Quick Start

### 1. Basic Production Mode
```bash
./scripts/start_production.sh
# Choose option 2 for production mode with MQTT
```

### 2. Infinite Runner Mode (Recommended for 24/7)
```bash
./scripts/start_production.sh --mode infinite
```

### 3. Test MQTT Messages
```bash
python3 scripts/test_mqtt_subscriber.py
```

## Project Structure (Cleaned)

```
📁 configs/
  📁 components/         # Component configurations
    📄 config_infer_primary_yolo11.txt
    📄 mqtt_broker_config.txt
    📄 nvdsanalytics_config.txt
    📄 tracker_config.txt
    📄 msg_config.txt
  📁 environments/       # Environment configurations
    📄 config_sources_production.txt  # Main production config

📁 data/
  📁 persistence/        # Persistent count storage
    📄 tracking_counts.json
    📄 live_counts.json

📁 scripts/              # Essential scripts only
  📄 start_production.sh          # Main production launcher
  📄 run_tracking_indefinitely.sh # Infinite runner
  📄 cleanup_deepstream.sh       # Cleanup utility
  📄 test_mqtt_subscriber.py     # MQTT test script

📁 src/                 # Core application
  📄 tracking_deepstream.py      # Main DeepStream app
  📄 tracking_mqtt.py            # MQTT publisher
  📄 tracking_based_counter.py   # Counting logic

📁 models/              # YOLO models
📁 nvdsinfer_custom_impl_Yolo/ # Custom inference
```

## Configuration

### MQTT Broker
Edit `configs/components/mqtt_broker_config.txt` or set environment variables:
```bash
export MQTT_BROKER_HOST=your-broker.com
export MQTT_BROKER_PORT=1883
export MQTT_BROKER_USER=username
export MQTT_BROKER_PASS=password
```

### Camera Sources
Edit `configs/environments/config_sources_production.txt` for your camera sources.

## Data Persistence

Counts are automatically saved to:
- `data/persistence/tracking_counts.json` - Per-camera tracking counts
- `data/persistence/live_counts.json` - Live session counts

## Production Operation

### Option 2 (Production Mode)
- Live video display with object detection overlays
- Real-time MQTT broadcasting of count data
- Persistent count storage across restarts
- System health monitoring

### Infinite Mode
- Automatic restart on failure
- 24/7 operation capability
- Continuous MQTT publishing
- Health monitoring and recovery

## Monitoring

### MQTT Topics Published
- `camera1`, `camera2`, `camera3`, `camera4` - Count data per camera
- `deepstream/health` - System health status

### Testing MQTT Reception
```bash
python3 scripts/test_mqtt_subscriber.py
```

## Troubleshooting

### GPU Issues
```bash
./scripts/cleanup_deepstream.sh
```

### Check System
- GPU: `nvidia-smi`
- DeepStream: `/opt/nvidia/deepstream/deepstream/bin/deepstream-app --version`
- Python deps: `pip3 install paho-mqtt psutil`

## Files Removed in Cleanup
- All demo and test scripts (except MQTT subscriber test)
- Redundant configuration files
- Old source implementations
- Development utilities

This streamlined setup focuses solely on production operation with minimal maintenance overhead.
