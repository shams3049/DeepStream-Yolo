# MQTT Data Flow and Persistence Analysis Report

## Overview
This document analyzes what data is being sent over MQTT and demonstrates the persistence system capabilities of the tracking-based object counting system.

## MQTT Data Flow

### 📡 Broker Configuration
- **External Broker**: `mqtt-proxy.ad.dicodrink.com:1883`
- **Authentication**: Username/password authentication with user `r_vmays`
- **Connection Status**: ✅ Successfully tested and operational

### 📋 Published Topics

#### 1. Camera Tracking Data
**Topics**: `camera1/tracking`, `camera2/tracking`

**Message Structure**:
```json
{
  "timestamp": "2025-07-30 11:50:21",
  "source_id": "source0",
  "camera_name": "Camera 1 (102)",
  "camera_ip": "10.20.100.102", 
  "area": "Production Area 1",
  "counting_method": "NVIDIA Analytics Tracker IDs",
  "message_type": "tracking_count",
  "unique_objects_tracked": 3,        // Live objects currently being tracked
  "session_new_objects": 2,          // New objects detected this session
  "total_objects_detected": 16,      // All-time total including persistence
  "tracked_object_ids": [            // Unique tracker IDs from NVIDIA Analytics
    "obj_0_0_1",
    "obj_0_1_1", 
    "obj_0_2_1"
  ],
  "object_details": [                // Detailed info per tracked object
    {
      "id": "obj_0_0_1",
      "class": "can",
      "confidence": 0.91,
      "first_seen": "2025-07-30 11:50:21"
    }
  ],
  "session_info": {
    "session_start": "2025-07-30 11:50:21",
    "session_duration_seconds": 30,
    "total_detections_this_session": 2
  },
  "persistence_info": {              // Indicates persistence system status
    "counts_saved": true,
    "persistence_file": "data/persistence/tracking_counts.json",
    "last_save": "2025-07-30 11:50:21"
  }
}
```

#### 2. System Health Status
**Topic**: `deepstream/health`

**Message Structure**:
```json
{
  "timestamp": "2025-07-30 11:50:27",
  "message_type": "health_status", 
  "system_status": "operational",
  "streams_active": 2,
  "mqtt_status": "connected",
  "persistence_status": "active",
  "total_objects_tracked": 21,
  "uptime_seconds": 180,
  "memory_usage_mb": 1024,
  "cpu_usage_percent": 15.5
}
```

#### 3. Analytics Summary
**Topic**: `deepstream/analytics`

**Message Structure**:
```json
{
  "timestamp": "2025-07-30 11:50:27",
  "message_type": "analytics_summary",
  "summary_period": "last_5_minutes",
  "total_objects_detected": 25,
  "objects_by_stream": {
    "stream_0": 15,
    "stream_1": 10
  },
  "peak_objects_detected": 4,
  "average_objects_per_minute": 5.0,
  "persistence_data": {             // Shows persistent vs session counts
    "stream_0": {"total": 13, "session": 8},
    "stream_1": {"total": 2, "session": 5},
    "stream_2": {"total": 1, "session": 0},
    "stream_3": {"total": 5, "session": 0}
  }
}
```

## Persistence System

### 📁 Storage Location
- **Directory**: `data/persistence/`
- **Files**: 
  - `object_counts.json` - Historical persistent counts
  - `tracking_counts.json` - Session-specific tracking data
  - `analytics_stream_counts.json` - Analytics historical data
  - `live_counts.json` - Real-time count cache

### 💾 Persistence Data Structure

**object_counts.json**:
```json
{
  "stream_0": {
    "cans": 3,                      // Current live count
    "total_objects": 16,            // All-time total 
    "last_updated": "2025-07-30T11:51:46.144775"
  },
  "stream_1": {
    "cans": 1,
    "total_objects": 3,
    "last_updated": "2025-07-30T11:51:46.144203"
  }
}
```

### ✅ Cross-Session Persistence Verification

**Test Results**: 
- ✅ Counts successfully saved to disk
- ✅ Counts successfully loaded on application restart  
- ✅ All stream counts maintained exactly across sessions
- ✅ Timestamps properly updated
- ✅ Historical totals preserved while allowing new session counts

## Data Recipients (Who is Sensing It)

### 🎯 MQTT Subscribers
Any system connected to `mqtt-proxy.ad.dicodrink.com:1883` can subscribe to:
- `camera1/tracking` - Camera 1 object counts and tracker IDs
- `camera2/tracking` - Camera 2 object counts and tracker IDs  
- `deepstream/health` - System health and operational status
- `deepstream/analytics` - Analytics summaries and persistence data

### 📊 Data Usage Scenarios
1. **Real-time Dashboards**: Live object count monitoring
2. **Analytics Systems**: Historical trend analysis using persistence data
3. **Alerting Systems**: Monitoring system health and detecting anomalies
4. **Inventory Systems**: Integration with production counting
5. **Quality Control**: Tracking detection confidence and object details

## Key Features Demonstrated

### 🎯 Tracking-Based Counting
- **Method**: NVIDIA Analytics tracker IDs instead of detection lines
- **Advantage**: More accurate, eliminates false positives from line crossings
- **Data**: Provides unique object identifiers and detailed tracking info

### 🔄 Session vs Total Counting  
- **Session Counts**: Objects detected since application start
- **Total Counts**: Persistent all-time totals across restarts
- **MQTT**: Both values published for comprehensive monitoring

### 💾 Automatic Persistence
- **Auto-save**: Counts saved after every increment
- **Cross-session**: Data survives application restarts
- **Timestamped**: Last update tracking for each stream
- **Reliable**: Verified through testing load/save cycles

### 📡 External MQTT Integration
- **Broker**: External production broker (not localhost)
- **Authentication**: Secure credential-based access
- **Topics**: Organized by function (tracking, health, analytics)
- **Format**: Rich JSON payloads with comprehensive metadata

## Monitoring and Testing Tools

### 🔧 Created Tools
1. **`scripts/mqtt_monitor.py`** - Real-time MQTT message monitoring
2. **`scripts/test_mqtt_connection.py`** - MQTT connectivity testing
3. **`scripts/simulate_tracking_data.py`** - Demonstration data generation
4. **`scripts/demonstrate_persistence.py`** - Persistence system verification

### 📊 Verification Results
- ✅ MQTT connectivity established
- ✅ Message publishing confirmed  
- ✅ Topic subscription working
- ✅ Persistence system operational
- ✅ Cross-session data integrity maintained
