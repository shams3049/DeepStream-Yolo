# DeepStream Object Counter with MQTT Broadcasting

A production-ready NVIDIA DeepStream application for real-time object counting with MQTT integration for industrial IoT monitoring.

## 🏭 Features

- **Real-time Object Detection**: YOLO11-based object detection using NVIDIA DeepStream SDK
- **Persistent Counting**: Thread-safe object counting with JSON persistence across application restarts
- **MQTT Broadcasting**: Real-time count broadcasting to external MQTT broker every 1 second
- **Multi-Camera Support**: Supports up to 4 RTSP camera streams simultaneously
- **Health Monitoring**: System health metrics broadcasting every 5 seconds
- **Production Ready**: Optimized for industrial deployment with external MQTT broker integration

## 🚀 Quick Start

### Prerequisites

- NVIDIA Jetson device with DeepStream SDK 7.x
- NVIDIA GPU with CUDA support
- Python 3.8+
- RTSP camera streams
- External MQTT broker access

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd DeepStream-Object-Counter
```

2. **Install Python dependencies**
```bash
pip3 install paho-mqtt psutil
```

3. **Configure MQTT broker**
Edit `configs/components/mqtt_broker_config.txt` with your MQTT broker credentials:
```ini
[message-broker]
username = your_username
password = your_password
client-id = deepstream-production-counter
keep-alive = 60
```

4. **Configure camera sources**
Edit `configs/environments/config_sources_production.txt` with your RTSP camera URLs:
```ini
[source0]
uri=rtsp://username:password@camera1_ip:554/stream
[source1]
uri=rtsp://username:password@camera2_ip:554/stream
# ... etc
```

### Running the Application

**Start the production system:**
```bash
./scripts/start_production.sh
```

**Or run components separately:**
```bash
# Start MQTT broadcasting
python3 src/production_mqtt.py &

# Start DeepStream application
python3 src/production_deepstream.py
```

## 📡 MQTT Topics

The application publishes to simplified MQTT topics:

### Camera Count Topics (1-second intervals)
- `camera1` - Camera 1 object counts
- `camera2` - Camera 2 object counts  
- `camera3` - Camera 3 object counts
- `camera4` - Camera 4 object counts

### Health Status Topic (5-second intervals)
- `deepstream/health` - System health and performance metrics

## 📊 Message Format

### Camera Count Message
```json
{
  "timestamp": "2025-07-28T11:55:25.311223",
  "source_id": 0,
  "camera_name": "Assembly Line A",
  "camera_ip": "10.20.100.101", 
  "location": "Production Floor 1",
  "can_count": 45,
  "total_objects": 67,
  "message_type": "count_update"
}
```

### Health Status Message
```json
{
  "timestamp": "2025-07-28T11:55:26.358938",
  "system_status": "healthy",
  "deepstream_running": true,
  "cpu_usage": "29.1%",
  "memory_usage": "8.0%",
  "gpu_info": {
    "utilization": "78%",
    "memory_used": "3456MB",
    "memory_total": "8192MB"
  },
  "total_cans_detected": 234,
  "total_objects_detected": 456,
  "active_cameras": 4,
  "uptime_hours": 72.5,
  "message_type": "health_status"
}
```

## 🔧 Configuration

### MQTT Broker Configuration
File: `configs/components/mqtt_broker_config.txt`
```ini
[message-broker]
username = your_mqtt_username
password = your_mqtt_password
client-id = deepstream-production-counter
keep-alive = 60
```

### Camera Sources Configuration  
File: `configs/environments/config_sources_production.txt`
- Configure RTSP camera streams
- Set resolution and encoding parameters
- Configure MQTT broker connection string
- Set object detection parameters

### Model Configuration
File: `configs/components/config_infer_primary_yolo11.txt`
- YOLO11 model configuration
- Detection thresholds
- Class filtering

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RTSP Cameras  │───▶│  DeepStream SDK  │───▶│  Object Counter │
│   (4 streams)   │    │   (YOLO11)       │    │  (Persistent)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ External MQTT   │◀───│ MQTT Publisher  │
                       │ Broker          │    │ (1-sec intervals)│
                       └─────────────────┘    └─────────────────┘
```

## 📦 Project Structure

```
DeepStream-Object-Counter/
├── src/
│   ├── object_counter.py          # Persistent object counting
│   ├── production_mqtt.py         # MQTT broadcasting
│   └── production_deepstream.py   # Main DeepStream application
├── scripts/
│   └── start_production.sh        # Production startup script
├── configs/
│   ├── components/
│   │   ├── mqtt_broker_config.txt
│   │   ├── config_infer_primary_yolo11.txt
│   │   └── ...
│   └── environments/
│       └── config_sources_production.txt
├── models/
│   └── yolo11s.onnx              # YOLO11 model
├── data/
│   └── persistence/
│       └── object_counts.json     # Persistent count storage
└── nvdsinfer_custom_impl_Yolo/   # DeepStream YOLO plugin
```

## 🔍 Monitoring

### Test MQTT Connection
```bash
# Monitor all topics
mosquitto_sub -h your-mqtt-broker.com -p 1883 \
  -u username -P password -t '+' -v

# Monitor specific camera
mosquitto_sub -h your-mqtt-broker.com -p 1883 \
  -u username -P password -t 'camera1'

# Monitor health status
mosquitto_sub -h your-mqtt-broker.com -p 1883 \
  -u username -P password -t 'deepstream/health'
```

### Dashboard Integration
The MQTT messages are JSON-formatted and ready for integration with:
- Grafana dashboards
- Node-RED flows
- Custom web dashboards
- Industrial IoT platforms

## 🛡️ Production Deployment

### Security Considerations
- Use secure MQTT credentials
- Enable MQTT TLS/SSL for production
- Implement proper firewall rules
- Regular security updates

### Performance Optimization
- Adjust batch size based on GPU memory
- Configure appropriate detection thresholds
- Monitor system resources
- Use appropriate video resolution

### Reliability Features
- Automatic application restart on failure
- Persistent count storage
- MQTT reconnection handling
- Health monitoring alerts

## 📚 Dependencies

- **NVIDIA DeepStream SDK 7.x**
- **CUDA 12.x**
- **Python 3.8+**
- **paho-mqtt** - MQTT client library
- **psutil** - System monitoring
- **TensorRT** - GPU inference optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support and questions:
- Create an issue in this repository
- Check the configuration files for proper setup
- Verify MQTT broker connectivity
- Ensure DeepStream SDK is properly installed

## 🏷️ Version

Current version: 1.0.0 - Production Ready
