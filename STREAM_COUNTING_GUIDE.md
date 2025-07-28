# Enhanced Per-Stream Object Counting Guide

## Overview
The DeepStream-Yolo system now includes enhanced per-stream object counting with prominent GUI display. This guide explains how to use and configure the enhanced analytics features.

## Features

### 🎥 Per-Stream Object Counting
- **Live Object Count**: Current number of objects visible in each camera stream
- **Session Count**: Total objects detected since application start
- **Total Count**: Persistent count across all sessions
- **Analytics Integration**: Uses NVIDIA Analytics module for accurate counting

### 📊 GUI Display Enhancements
- **Prominent Display**: Large, easily readable object counts per stream
- **Side-by-Side Layout**: Camera 1 overlay on left, Camera 2 on right
- **Real-time Updates**: Live FPS and confidence metrics
- **Visual Indicators**: Color-coded status and stream identification

### 📡 NVIDIA Analytics Integration
- **Line Crossing Detection**: Tracks objects crossing defined lines
- **ROI Filtering**: Counts objects only within specified regions
- **Overcrowding Detection**: Alerts when object threshold exceeded
- **Direction Detection**: Tracks movement patterns

## Usage

### 1. Start Enhanced Counting
```bash
# Start production with enhanced analytics
./scripts/start_production.sh

# The system will automatically use the enhanced counter if available
```

### 2. GUI Display Layout

**Camera 1 (10.20.100.102)** - Left Side Display:
```
🎥 Camera 1 (102)
🔢 LIVE OBJECTS: 3
📊 Session: 45 | Total: 1,234
⚡ FPS: 29.5 | 📡 Analytics: ON
🟢 ACTIVE STREAM 1
```

**Camera 2 (10.20.100.103)** - Right Side Display:
```
🎥 Camera 2 (103)
🔢 LIVE OBJECTS: 1
📊 Session: 23 | Total: 856
⚡ FPS: 30.1 | 📡 Analytics: ON
🟢 ACTIVE STREAM 2
```

### 3. Console Output
```
📊 Live: 4 | Cam1: 3(1234) | Cam2: 1(856) | Session: 68
```

## Configuration

### 1. Analytics Configuration
File: `configs/components/nvdsanalytics_config.txt`

```ini
[property]
enable=1
config-width=1920
config-height=1080
osd-mode=2
display-font-size=16

# Per-stream line crossing
[line-crossing-stream-0]
enable=1
class-id=0
line-crossing-LC0=200;900;1720;900

[line-crossing-stream-1]
enable=1
class-id=0
line-crossing-LC1=200;900;1720;900
```

### 2. Production Configuration
File: `configs/environments/config_sources_production.txt`

Key settings:
```ini
[nvds-analytics]
enable=1
config-file=/home/deepstream/DeepStream-Yolo/configs/components/nvdsanalytics_config.txt

[tiled-display]
rows=1
columns=2  # Side-by-side display for per-stream counting
```

## Data Persistence

### 1. Storage Location
- **File**: `data/persistence/live_counts.json`
- **Format**: JSON with per-stream data
- **Auto-save**: On application exit

### 2. Data Structure
```json
{
  "0": {
    "total": 1234,
    "session": 45,
    "last_updated": "2025-01-28T10:30:00"
  },
  "1": {
    "total": 856,
    "session": 23,
    "last_updated": "2025-01-28T10:30:00"
  }
}
```

## Customization

### 1. Overlay Positioning
Modify `src/advanced_live_counter.py` in the `add_counting_overlay` function:

```python
# Camera 1 - left side
if stream_id == 0:
    base_x = 20      # X position
    base_y = 20      # Y position

# Camera 2 - right side  
else:
    base_x = 680     # X position for right side
    base_y = 20      # Y position
```

### 2. Font and Colors
```python
# Main count display
py_nvosd_text_params_2.font_params.font_size = 24  # Large font
py_nvosd_text_params_2.font_params.font_color.green = 1.0  # Green text
```

### 3. Analytics Zones
Edit `configs/components/nvdsanalytics_config.txt`:

```ini
# Adjust line crossing coordinates (x1;y1;x2;y2)
line-crossing-LC0=200;540;1720;540

# Add ROI filtering (x;y;width;height)
roi-RF0=100;100;1720;880
```

## Testing and Validation

### 1. Simulation Mode
For testing without cameras:
```bash
python3 src/stream_gui_counter.py
```

### 2. Verify Analytics
Check for these console messages:
```
✅ DeepStream Python bindings available
📊 Analytics enabled in config
⚡ FPS updates show per-stream data
```

### 3. GUI Validation
- Each stream should show separate overlay
- Live counts update in real-time
- Session counts increment with detections
- Total counts persist across restarts

## Troubleshooting

### 1. No Per-Stream Display
**Issue**: Overlays not showing separately
**Solution**: 
- Check tiled display configuration (columns=2)
- Verify stream IDs in overlay positioning
- Ensure analytics is enabled

### 2. Counts Not Updating
**Issue**: Object counts remain at zero
**Solution**:
- Check YOLO model confidence thresholds
- Verify analytics configuration
- Test with simulation mode first

### 3. FPS Issues
**Issue**: Low FPS affecting counting accuracy
**Solution**:
- Reduce stream resolution if needed
- Check GPU utilization
- Optimize analytics zones

## Performance Optimization

### 1. GPU Memory
- Monitor with `nvidia-smi`
- Adjust batch size if needed
- Consider stream resolution

### 2. Analytics Efficiency
- Use specific ROI regions
- Limit class IDs to relevant objects
- Adjust confidence thresholds

### 3. Display Performance
- Reduce overlay complexity if needed
- Limit text elements per stream
- Optimize font rendering

## Integration with MQTT

The enhanced counting integrates with the existing MQTT system:

```python
# MQTT messages include per-stream data
{
  "stream_id": 0,
  "live_objects": 3,
  "session_count": 45,
  "total_count": 1234,
  "analytics_events": 12
}
```

## Summary

The enhanced per-stream object counting provides:

1. **Clear Visual Display**: Prominent object counts per camera stream
2. **Analytics Integration**: Uses NVIDIA Analytics for accurate detection
3. **Persistent Storage**: Counts preserved across sessions
4. **Real-time Updates**: Live FPS and confidence metrics
5. **Easy Configuration**: Flexible analytics zones and display options

This system gives you comprehensive visibility into object detection performance per camera stream with professional-grade accuracy and display.
