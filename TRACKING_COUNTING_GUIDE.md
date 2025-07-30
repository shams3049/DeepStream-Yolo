# 🎯 Tracking-Based Object Counting Guide

## Overview

The DeepStream-Yolo system now includes **tracking-based object counting** using NVIDIA Analytics tracked object IDs instead of detection lines. This approach provides more accurate counting by tracking unique objects throughout their lifecycle in the video stream.

## 🔄 Key Differences from Line-Based Counting

### **Traditional Line-Based Counting:**
- ❌ Objects must cross specific detection lines
- ❌ Can miss objects that don't cross lines
- ❌ May double-count objects crossing multiple times
- ❌ Limited to specific areas of the frame

### **Tracking-Based Counting (NEW):**
- ✅ Counts every unique object with a tracker ID
- ✅ Works across the entire frame
- ✅ No detection lines required
- ✅ Prevents double-counting with unique IDs
- ✅ More accurate total object counts

## 🎯 How Tracking-Based Counting Works

### 1. **Object Detection & Tracking**
```
Camera Frame → YOLO Detection → NVIDIA Tracker → Unique Object IDs
```

### 2. **Unique ID Management**
- Each detected object gets a unique tracker ID
- System maintains a set of tracked object IDs per stream
- New IDs are added to the total count
- Existing IDs don't increment the count

### 3. **MQTT Publishing**
Enhanced MQTT messages include:
- `unique_objects_tracked`: Current objects with valid tracker IDs
- `session_new_objects`: New objects detected this session
- `total_count`: Persistent count across all sessions
- `tracked_object_ids`: Array of current tracker IDs

## 📊 Enhanced MQTT Message Format

### Camera Tracking Message
```json
{
  "timestamp": "2025-07-30T12:00:00.000000",
  "source_id": 0,
  "camera_name": "Camera 1 (102)",
  "camera_ip": "10.20.100.102",
  "location": "Production Area 1",
  "counting_method": "tracker_ids",
  "unique_objects_tracked": 5,
  "session_new_objects": 23,
  "total_objects_detected": 1234,
  "can_count": 15,
  "tracked_object_ids": [1001, 1005, 1007, 1012, 1018],
  "message_type": "tracking_count_update"
}
```

### Analytics Summary Message
```json
{
  "timestamp": "2025-07-30T12:00:00.000000",
  "counting_method": "nvidia_analytics_tracker_ids",
  "total_unique_objects_tracked": 8,
  "total_session_new_objects": 45,
  "total_persistent_count": 2567,
  "active_streams": 2,
  "per_stream_breakdown": {
    "0": {"unique_objects": 5, "session_count": 23},
    "1": {"unique_objects": 3, "session_count": 22}
  },
  "analytics_enabled": true,
  "message_type": "analytics_summary"
}
```

## 🚀 Getting Started

### 1. **Configuration Files Created**

#### **Analytics Configuration:**
```
configs/components/tracking_analytics_config.txt
```
- Enables full-frame ROI filtering
- Disables line-crossing detection
- Adds overcrowding and direction detection

#### **Production Configuration:**
```
configs/environments/config_tracking_production.txt
```
- Uses tracking-based analytics
- Enhanced tracker settings
- Optimized for object ID accuracy

### 2. **New Source Files**

#### **Core Tracking Counter:**
```
src/tracking_based_counter.py
```
- Main tracking logic
- Unique object ID management
- Display overlay generation

#### **Enhanced MQTT Publisher:**
```
src/tracking_mqtt.py
```
- Tracking-specific MQTT messages
- Enhanced payload format
- Real-time unique object counts

#### **Integrated Application:**
```
src/tracking_deepstream.py
```
- Complete DeepStream application
- Tracking-based counting integration
- MQTT publishing coordination

### 3. **Usage**

#### **Automatic Selection (Recommended):**
```bash
./scripts/start_production.sh
```
The script automatically uses tracking-based counting if available.

#### **Direct Execution:**
```bash
# Use tracking-based configuration
python3 src/tracking_deepstream.py configs/environments/config_tracking_production.txt

# Or use with existing configuration
python3 src/tracking_deepstream.py configs/environments/config_sources_production.txt
```

#### **MQTT Publishing Only:**
```bash
# Start enhanced MQTT publisher
python3 src/tracking_mqtt.py
```

## 📊 GUI Display Features

### **Enhanced Overlay Information:**
```
🎥 Camera 1 (102) - TRACKING MODE
🔢 UNIQUE OBJECTS: 5
📊 Session: 23 | Total: 1,234
⚡ FPS: 29.5 | 🎯 Tracker IDs
🟢 TRACKING STREAM 1
```

### **Display Layout:**
- **Side-by-side**: Each camera stream shows separate tracking info
- **Real-time Updates**: Live object counts update as objects are tracked
- **Tracking Method Indicator**: Clear indication of tracking-based counting
- **Performance Metrics**: FPS and tracking status

## 🔧 Configuration Options

### **Tracker Settings (tracker_config.txt):**
```ini
tracker-width=960
tracker-height=544
ll-lib-file=/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so
enable-batch-process=1
enable-past-frame=1
```

### **Analytics Settings (tracking_analytics_config.txt):**
```ini
[roi-filtering-stream-0]
enable=1
class-id=-1  # Apply to all classes
roi-RF0=0;0;1920;1080  # Full frame ROI
```

### **Confidence Thresholds:**
- Default confidence threshold: `0.5`
- Only objects above threshold get tracked
- Adjustable in the tracking counter code

## 🎯 Benefits of Tracking-Based Counting

### **Accuracy Improvements:**
1. **No Missed Objects**: Counts all detected objects, not just those crossing lines
2. **Prevents Double-Counting**: Unique IDs ensure each object counted once
3. **Full Frame Coverage**: Works across entire camera view
4. **Persistent Tracking**: Objects tracked even when temporarily occluded

### **Operational Benefits:**
1. **No Line Configuration**: No need to define detection lines
2. **Flexible Deployment**: Works with any camera angle or setup
3. **Enhanced Analytics**: Provides object ID information for advanced analysis
4. **Better Integration**: Rich MQTT data for dashboard integration

### **Technical Advantages:**
1. **NVIDIA Optimized**: Uses built-in DeepStream tracking capabilities
2. **GPU Accelerated**: Efficient tracker ID management
3. **Real-time Performance**: Maintains high FPS while tracking
4. **Scalable**: Easily extends to more cameras or object types

## 📈 Performance Considerations

### **GPU Memory Usage:**
- Tracking requires additional GPU memory
- Monitor with `nvidia-smi`
- Adjust batch size if needed

### **Tracker Configuration:**
- Tracker resolution affects accuracy vs performance
- Current settings optimized for production use
- Can be tuned based on specific requirements

### **Object Lifetime:**
- Tracker IDs persist while objects are visible
- IDs may be reused after objects leave frame
- Session counts track new unique appearances

## 🔍 Monitoring and Debugging

### **Console Output:**
```
🆕 New object tracked: Stream 0, ID 1234, Class: can
📊 Stream 0 - Session: 45, Total: 1,234
🎯 Stream 1: 2 new tracked objects (Total: 7)
```

### **MQTT Monitoring:**
```bash
# Monitor tracking-specific topics
mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \
  -u r_vmays -P 'csYr9xH&WTfAvMj2' \
  -t 'camera1/tracking' -v

# Monitor analytics summary
mosquitto_sub -h mqtt-proxy.ad.dicodrink.com -p 1883 \
  -u r_vmays -P 'csYr9xH&WTfAvMj2' \
  -t 'deepstream/analytics' -v
```

### **Data Persistence:**
- Tracking data saved to: `data/persistence/tracking_counts.json`
- Includes session counts and total counts
- Unique object IDs tracked per session

## 🚀 Next Steps

### **Immediate Benefits:**
✅ More accurate object counting  
✅ No detection line configuration needed  
✅ Enhanced MQTT data with tracker IDs  
✅ Full frame object tracking  
✅ Prevents double counting  

### **Future Enhancements:**
- Object trajectory analysis using tracker paths
- Advanced behavioral analytics
- Historical tracking pattern analysis
- Integration with specific object classes
- Dashboard visualization of tracking data

---

**The tracking-based approach represents a significant improvement in counting accuracy and provides rich data for advanced analytics and monitoring systems.**
