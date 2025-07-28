# Configuration Guide

## MQTT Broker Setup

### 1. MQTT Credentials Configuration
File: `configs/components/mqtt_broker_config.txt`

```ini
[message-broker]
username = your_mqtt_username
password = your_mqtt_password
client-id = deepstream-production-counter
keep-alive = 60
```

**Required Changes:**
- Replace `your_mqtt_username` with your MQTT broker username
- Replace `your_mqtt_password` with your MQTT broker password
- Optionally change `client-id` for unique identification

### 2. Production Sources Configuration
File: `configs/environments/config_sources_production.txt`

**RTSP Camera Configuration:**
```ini
[source0]
enable=1
type=4
uri=rtsp://username:password@camera_ip:554/stream_path
num-sources=1
gpu-id=0
cudadec-memtype=0
```

**MQTT Broker Connection:**
```ini
[sink1]
msg-broker-conn-str=your-mqtt-broker.com;1883
topic=camera/stream
```

**Required Changes:**
- Update `uri` with your actual RTSP camera URLs
- Replace `your-mqtt-broker.com` with your MQTT broker address
- Adjust camera credentials and IP addresses
- Configure stream paths according to your cameras

## Camera Setup Guide

### Supported Camera Configurations

**Camera 1 - Assembly Line:**
- Location: Production Floor 1
- MQTT Topic: `camera1`
- Recommended: Higher resolution for detailed detection

**Camera 2 - Packaging Station:**
- Location: Production Floor 2  
- MQTT Topic: `camera2`
- Recommended: Medium resolution for packaging monitoring

**Camera 3 - Quality Control:**
- Location: QC Department
- MQTT Topic: `camera3`
- Recommended: High resolution for quality inspection

**Camera 4 - Shipping Dock:**
- Location: Shipping Area
- MQTT Topic: `camera4`
- Recommended: Wide angle for area coverage

### RTSP URL Format Examples

**Generic RTSP Format:**
```
rtsp://username:password@ip_address:port/stream_path
```

**Common Camera Brand Formats:**
```bash
# Hikvision
rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101

# Dahua  
rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0

# Axis
rtsp://user:password@192.168.1.102:554/axis-media/media.amp

# Generic IP Camera
rtsp://admin:password@192.168.1.103:554/stream1
```

## YOLO Model Configuration

### Model Parameters
File: `configs/components/config_infer_primary_yolo11.txt`

**Key Settings:**
```ini
# Model file location
model-file=../../models/yolo11s.onnx

# Detection threshold (0.0 - 1.0)
threshold=0.3

# Class filtering (0=person, 39=bottle, etc.)
filter-out-class-ids=0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25;26;27;28;29;30;31;32;33;34;35;36;37;38;40;41;42;43;44;45;46;47;48;49;50;51;52;53;54;55;56;57;58;59;60;61;62;63;64;65;66;67;68;69;70;71;72;73;74;75;76;77;78;79

# GPU configuration
gpu-id=0
network-mode=1
```

**Adjustable Parameters:**
- `threshold`: Lower values detect more objects, higher values are more selective
- `filter-out-class-ids`: Remove unwanted object classes
- `gpu-id`: Set GPU device ID for multi-GPU systems

## Network Configuration

### Firewall Settings
Ensure these ports are open:

**Outbound:**
- Port 1883 (MQTT)
- Port 554 (RTSP)
- Port 80/443 (HTTP/HTTPS for updates)

**Camera Network:**
- Ensure cameras are accessible from DeepStream host
- Configure appropriate VLANs if using network segmentation
- Test camera connectivity: `ping camera_ip`

### MQTT Broker Requirements

**Minimum Specifications:**
- Support for persistent connections
- QoS levels 0-2
- Username/password authentication
- Minimum 100 concurrent connections
- Message retention capabilities

**Recommended Features:**
- TLS/SSL encryption
- WebSocket support for web dashboards
- Message bridging capabilities
- Monitoring and logging

## Performance Tuning

### GPU Memory Optimization
```ini
# Batch processing
batched-push-timeout=40000
batch-size=4

# Memory type
nvbuf-memory-type=0
cudadec-memtype=0
```

### Stream Resolution Settings
```ini
# Input resolution
width=1920
height=1080

# Processing resolution (can be lower for performance)
process-width=640
process-height=480
```

### CPU/Memory Optimization
- Monitor system resources: `htop`
- Adjust batch size based on available GPU memory
- Configure appropriate number of worker threads
- Use hardware video decoding when available

## Troubleshooting

### Common Configuration Issues

**MQTT Connection Failures:**
1. Verify broker address and port
2. Check username/password
3. Ensure network connectivity: `telnet broker_address 1883`
4. Check firewall settings

**Camera Connection Issues:**
1. Test RTSP URL with VLC or similar player
2. Verify camera credentials
3. Check network connectivity: `ping camera_ip`
4. Ensure camera supports H.264 encoding

**Detection Issues:**
1. Adjust detection threshold
2. Verify model file exists and is accessible
3. Check GPU memory availability
4. Review class filtering settings

### Log Files
Monitor these logs for troubleshooting:
- DeepStream application output
- System logs: `/var/log/syslog`
- GPU status: `nvidia-smi`
- MQTT connection logs

### Performance Monitoring
```bash
# Monitor GPU usage
nvidia-smi -l 1

# Monitor system resources
htop

# Monitor network connectivity
netstat -an | grep 1883  # MQTT
netstat -an | grep 554   # RTSP
```
