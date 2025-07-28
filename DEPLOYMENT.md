# Deployment Guide

## Production Deployment Checklist

### 🔧 Pre-Deployment Setup

#### 1. System Requirements Verification
- [ ] NVIDIA Jetson device or GPU-enabled system
- [ ] NVIDIA DeepStream SDK 7.x installed
- [ ] CUDA 12.x runtime
- [ ] Python 3.8+ with pip
- [ ] Minimum 8GB RAM
- [ ] 32GB+ storage space

#### 2. Network Infrastructure
- [ ] Stable network connection (minimum 100 Mbps)
- [ ] RTSP camera network accessibility
- [ ] MQTT broker connectivity
- [ ] Firewall ports configured (1883, 554)
- [ ] Network security policies reviewed

#### 3. Hardware Setup
- [ ] Camera mounting and positioning
- [ ] Network cable connections
- [ ] Power supply redundancy
- [ ] Environmental considerations (temperature, humidity)

### 🚀 Installation Steps

#### 1. System Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip git

# Install Python dependencies
pip3 install paho-mqtt psutil
```

#### 2. Application Setup
```bash
# Clone repository
git clone <your-repository-url>
cd DeepStream-Object-Counter

# Make scripts executable
chmod +x scripts/start_production.sh

# Create data directories
mkdir -p data/persistence
```

#### 3. Configuration
```bash
# Copy and edit MQTT configuration
cp configs/components/mqtt_broker_config.txt.example configs/components/mqtt_broker_config.txt
nano configs/components/mqtt_broker_config.txt

# Edit production configuration
nano configs/environments/config_sources_production.txt
```

### ⚙️ Configuration Steps

#### 1. MQTT Broker Configuration
Edit `configs/components/mqtt_broker_config.txt`:
```ini
[message-broker]
username = production_user
password = secure_password_here
client-id = deepstream-production-counter
keep-alive = 60
```

#### 2. Camera Sources Configuration
Edit `configs/environments/config_sources_production.txt`:

**Update camera URLs:**
```ini
[source0]
uri=rtsp://admin:camera_password@10.20.100.101:554/cam/realmonitor?channel=1&subtype=1

[source1]
uri=rtsp://admin:camera_password@10.20.100.102:554/cam/realmonitor?channel=1&subtype=0
```

**Update MQTT broker connection:**
```ini
[sink1]
msg-broker-conn-str=your-mqtt-broker.com;1883
```

#### 3. Model Verification
```bash
# Verify YOLO model exists
ls -la models/yolo11s.onnx

# If missing, download appropriate model
# wget https://path-to-yolo11s-model/yolo11s.onnx -O models/yolo11s.onnx
```

### 🧪 Testing and Validation

#### 1. Component Testing
```bash
# Test MQTT connectivity
mosquitto_sub -h your-mqtt-broker.com -p 1883 \
  -u username -P password -t 'camera1' -C 5

# Test camera connectivity
ffplay rtsp://admin:password@camera_ip:554/stream

# Test GPU availability
nvidia-smi
```

#### 2. Application Testing
```bash
# Start in test mode (short duration)
timeout 30 python3 src/production_mqtt.py

# Verify object counter functionality
python3 -c "from src.object_counter import ObjectCounter; oc = ObjectCounter(); print(oc.get_all_counts())"
```

#### 3. Integration Testing
```bash
# Run full production test
timeout 60 ./scripts/start_production.sh
```

### 🏭 Production Launch

#### 1. Service Configuration (Optional)
Create systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/deepstream-counter.service
```

```ini
[Unit]
Description=DeepStream Object Counter
After=network.target

[Service]
Type=simple
User=deepstream
WorkingDirectory=/home/deepstream/DeepStream-Object-Counter
ExecStart=/home/deepstream/DeepStream-Object-Counter/scripts/start_production.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable deepstream-counter
sudo systemctl start deepstream-counter
```

#### 2. Production Launch
```bash
# Manual launch
./scripts/start_production.sh

# Or with service
sudo systemctl start deepstream-counter
```

### 📊 Monitoring and Maintenance

#### 1. Real-time Monitoring
```bash
# Monitor MQTT messages
mosquitto_sub -h your-broker.com -p 1883 -u username -P password -t '+' -v

# Monitor system resources
htop

# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor application logs
tail -f /var/log/syslog | grep deepstream
```

#### 2. Performance Metrics
Monitor these key metrics:
- **Message Rate**: ~4 messages/second (camera counts)
- **CPU Usage**: < 80% sustained
- **GPU Utilization**: 60-90% optimal
- **Memory Usage**: < 85% of available
- **Network Latency**: < 100ms to MQTT broker

#### 3. Health Checks
```bash
# Check process status
ps aux | grep production

# Check MQTT connectivity
mosquitto_pub -h your-broker.com -p 1883 \
  -u username -P password -t 'test' -m 'connectivity_test'

# Check object counting functionality
python3 -c "
import json
with open('data/persistence/object_counts.json', 'r') as f:
    counts = json.load(f)
    print(f'Current total objects: {sum(stream.get(\"total_objects\", 0) for stream in counts.values())}')
"
```

### 🛡️ Security Considerations

#### 1. Network Security
- Use VPN or secure networks for camera access
- Enable MQTT TLS/SSL in production
- Implement proper firewall rules
- Regular security updates

#### 2. Application Security
- Use strong MQTT credentials
- Rotate passwords regularly
- Limit network access to required ports only
- Monitor for unauthorized access attempts

#### 3. Data Security
- Encrypt sensitive configuration files
- Secure backup of persistent data
- Implement access logging
- Regular security audits

### 🔄 Backup and Recovery

#### 1. Configuration Backup
```bash
# Create configuration backup
tar -czf deepstream-config-backup-$(date +%Y%m%d).tar.gz configs/ models/ data/

# Automated daily backup
echo "0 2 * * * tar -czf /backup/deepstream-config-\$(date +\%Y\%m\%d).tar.gz -C /home/deepstream/DeepStream-Object-Counter configs/ models/ data/" | crontab -
```

#### 2. Recovery Procedures
```bash
# Restore from backup
tar -xzf deepstream-config-backup-YYYYMMDD.tar.gz

# Reset persistent counts (if needed)
rm -f data/persistence/object_counts.json

# Restart application
sudo systemctl restart deepstream-counter
```

### 📈 Scaling Considerations

#### 1. Multi-Camera Scaling
- Each additional camera increases GPU load by ~15-20%
- Monitor memory usage when adding cameras
- Consider load balancing across multiple devices

#### 2. High Availability
- Deploy on multiple Jetson devices
- Implement MQTT message deduplication
- Use redundant network connections
- Monitor with external health checks

#### 3. Performance Optimization
- Adjust batch sizes based on available resources
- Use appropriate video resolution for detection accuracy vs performance
- Consider edge computing deployment patterns

### 🆘 Troubleshooting Guide

#### Common Issues and Solutions

**Application won't start:**
1. Check DeepStream SDK installation
2. Verify GPU availability: `nvidia-smi`
3. Check Python dependencies: `pip3 list`
4. Review configuration files for syntax errors

**No MQTT messages:**
1. Test broker connectivity: `telnet broker_address 1883`
2. Verify credentials in configuration
3. Check firewall settings
4. Monitor application logs for MQTT errors

**Poor detection accuracy:**
1. Adjust detection threshold in model config
2. Verify camera focus and positioning
3. Check lighting conditions
4. Review object class filtering

**High resource usage:**
1. Reduce batch size in configuration
2. Lower input resolution
3. Optimize detection parameters
4. Consider hardware upgrade

For additional support, monitor system logs and application output for specific error messages.
