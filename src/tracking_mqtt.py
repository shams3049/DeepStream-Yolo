#!/usr/bin/env python3

"""
Enhanced Production MQTT Publisher with Tracking-Based Counting
Publishes unique object counts based on NVIDIA Analytics tracker IDs instead of detection lines
"""

import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import psutil
import os
import subprocess
from collections import defaultdict

# Import from same directory
import sys
sys.path.append(os.path.dirname(__file__))
from tracking_based_counter import TrackingBasedCounter

class TrackingMQTTPublisher:
    def __init__(self, config_file=None):
        # Load configuration from file
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'components', 'mqtt_broker_config.txt')
        
        self.load_config(config_file)
        
        # Enhanced topic configuration for tracking-based counting
        self.topics = {
            "source0": "camera1/tracking",
            "source1": "camera2/tracking", 
            "health": "deepstream/health",
            "analytics": "deepstream/analytics"
        }
        
        self.client = None
        self.connected = False
        self.counter = TrackingBasedCounter()
        self.publishing = False
        
        # Tracking-based counting data
        self.tracked_objects = defaultdict(set)  # {stream_id: {object_ids}}
        self.session_counts = defaultdict(int)   # {stream_id: session_count}
        self.tracking_enabled = True
        
        # Camera location mapping
        self.camera_locations = {
            0: {"name": "Camera 1 (102)", "ip": "10.20.100.102", "area": "Production Area 1", "stream": "subtype=0"},
            1: {"name": "Camera 2 (103)", "ip": "10.20.100.103", "area": "Production Area 2", "stream": "subtype=0"}
        }
        
        print(f"🎯 Tracking-Based MQTT Publisher initialized")
        print(f"📡 Broker: {self.broker_host}:{self.broker_port}")
        print(f"🔐 Client ID: {self.client_id}")
        print(f"📊 Counting Method: NVIDIA Analytics Tracker IDs")
    
    def load_config(self, config_file):
        """Load MQTT configuration from file"""
        import configparser
        
        # First, load from environment variables (priority)
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
        self.username = os.getenv('MQTT_BROKER_USER', 'admin')
        self.password = os.getenv('MQTT_BROKER_PASS', 'password')
        self.client_id = os.getenv('MQTT_CLIENT_ID', 'deepstream-tracking-counter')
        
        # Then try to load from config file (fallback)
        config = configparser.ConfigParser()
        try:
            config.read(config_file)
            
            # Load MQTT broker settings from file if not in environment
            broker_section = config['message-broker']
            
            # Override hostname and port from file if not set via environment
            if self.broker_host == 'localhost':  # Default value, override from file
                self.broker_host = broker_section.get('hostname', 'localhost')
            if self.broker_port == 1883:  # Default value, override from file
                self.broker_port = int(broker_section.get('port', '1883'))
            if self.username == 'admin':  # Default value, override from file
                self.username = broker_section.get('username', 'admin')
            if self.password == 'password':  # Default value, override from file  
                self.password = broker_section.get('password', 'password')
            if self.client_id == 'deepstream-tracking-counter':  # Default value, override from file
                self.client_id = broker_section.get('client-id', 'deepstream-tracking-counter')
            
        except Exception as e:
            print(f"⚠️  Warning: Could not load MQTT config from {config_file}: {e}")
            print("Using environment variables or defaults...")
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for MQTT connection (VERSION2)"""
        if reason_code.is_failure:
            print(f"❌ Failed to connect to MQTT broker: {reason_code}")
            self.connected = False
        else:
            self.connected = True
            print(f"✅ Connected to tracking-based MQTT broker")
            print(f"📡 {self.broker_host}:{self.broker_port}")
    
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Callback for MQTT disconnection (VERSION2)"""
        self.connected = False
        print(f"📡 Disconnected from MQTT broker")
    
    def on_publish(self, client, userdata, mid, reason_code, properties):
        """Callback for successful publish (VERSION2)"""
        pass  # Keep quiet for production
    
    def connect(self):
        """Connect to the production MQTT broker"""
        try:
            self.client = mqtt.Client(client_id=self.client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            
            # Set credentials
            print(f"🔐 Setting MQTT credentials for user: {self.username}")
            self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            # Connect to broker
            print(f"🔌 Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if self.connected:
                print(f"✅ Successfully connected to MQTT broker")
            else:
                print(f"❌ Failed to connect to MQTT broker within 10 seconds")
            
            return self.connected
            
        except Exception as e:
            print(f"❌ MQTT connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.publishing = False
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            print("📡 MQTT disconnected")
        except Exception as e:
            print(f"❌ MQTT disconnect error: {e}")
    
    def update_tracked_objects(self, stream_id, tracked_object_ids):
        """Update tracked objects for a stream (called from DeepStream probe)"""
        with threading.Lock():
            previous_count = len(self.tracked_objects[stream_id])
            self.tracked_objects[stream_id] = set(tracked_object_ids)
            current_count = len(self.tracked_objects[stream_id])
            
            # If we have new objects, update session count
            if current_count > previous_count:
                new_objects = current_count - previous_count
                self.session_counts[stream_id] += new_objects
                print(f"🎯 Stream {stream_id}: {new_objects} new tracked objects (Total: {current_count})")
    
    def publish_tracking_count(self, stream_id):
        """Publish tracking-based count for specific source/camera"""
        try:
            if not self.connected:
                return False
            
            camera_info = self.camera_locations.get(stream_id, {})
            topic = self.topics.get(f"source{stream_id}")
            
            if not topic:
                return False
            
            # Get current tracking data
            unique_objects = len(self.tracked_objects[stream_id])
            session_count = self.session_counts[stream_id]
            
            # Get persistent count data
            counts = self.counter.get_all_counts()
            session_count = counts['session_counts'].get(stream_id, 0)
            total_count = counts['stream_totals'].get(stream_id, 0)
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "source_id": stream_id,
                "camera_name": camera_info.get("name", f"Camera {stream_id + 1}"),
                "camera_ip": camera_info.get("ip", "unknown"),
                "location": camera_info.get("area", "unknown"),
                "counting_method": "tracker_ids",
                "unique_objects_tracked": unique_objects,
                "session_new_objects": session_count,
                "total_objects_detected": total_count,
                "can_count": total_count,  # Assuming all detected objects are cans
                "tracked_object_ids": list(self.tracked_objects[stream_id]),
                "message_type": "tracking_count_update"
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=0)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Error publishing tracking count: {e}")
            return False
    
    def publish_analytics_summary(self):
        """Publish analytics summary across all streams"""
        try:
            if not self.connected:
                return False
            
            topic = self.topics["analytics"]
            
            total_unique_objects = sum(len(objects) for objects in self.tracked_objects.values())
            total_session_objects = sum(self.session_counts.values())
            
            # Get persistent counts
            counts = self.counter.get_all_counts()
            total_persistent = sum(counts['stream_totals'].values())
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "counting_method": "nvidia_analytics_tracker_ids",
                "total_unique_objects_tracked": total_unique_objects,
                "total_session_new_objects": total_session_objects,
                "total_persistent_count": total_persistent,
                "active_streams": len(self.tracked_objects),
                "per_stream_breakdown": {
                    str(stream_id): {
                        "unique_objects": len(objects),
                        "session_count": self.session_counts[stream_id]
                    }
                    for stream_id, objects in self.tracked_objects.items()
                },
                "analytics_enabled": self.tracking_enabled,
                "message_type": "analytics_summary"
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=0)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Error publishing analytics summary: {e}")
            return False
    
    def get_system_health(self):
        """Get comprehensive system health information including tracking status"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # GPU information (if available)
            gpu_info = {"utilization": "[N/A]%", "memory_used": "[N/A]MB", "memory_total": "[N/A]MB"}
            try:
                gpu_result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True, timeout=5)
                if gpu_result.returncode == 0:
                    gpu_data = gpu_result.stdout.strip().split(', ')
                    if len(gpu_data) >= 3:
                        gpu_info = {
                            "utilization": f"{gpu_data[0]}%",
                            "memory_used": f"{gpu_data[1]}MB",
                            "memory_total": f"{gpu_data[2]}MB"
                        }
            except:
                pass
            
            # Check if DeepStream process is running
            deepstream_running = False
            try:
                result = subprocess.run(['pgrep', '-f', 'deepstream'], capture_output=True)
                deepstream_running = result.returncode == 0
            except:
                pass
            
            # Get tracking-based counts
            total_unique_objects = sum(len(objects) for objects in self.tracked_objects.values())
            total_session_objects = sum(self.session_counts.values())
            
            # Get persistent counts
            counts = self.counter.get_all_counts()
            total_persistent = sum(counts['stream_totals'].values())
            total_cans = total_persistent  # Assuming all detected objects are cans
            
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
                "deepstream_running": deepstream_running,
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "disk_usage": f"{disk.percent:.1f}%",
                "gpu_info": gpu_info,
                "counting_method": "tracker_ids",
                "total_unique_objects_tracked": total_unique_objects,
                "total_session_objects": total_session_objects,
                "total_persistent_count": total_persistent,
                "total_cans_detected": total_cans,
                "tracking_enabled": self.tracking_enabled,
                "active_cameras": len(self.camera_locations),
                "active_streams": len(self.tracked_objects),
                "uptime_hours": (time.time() - psutil.boot_time()) / 3600,
                "message_type": "health_status"
            }
            
            return health_data
            
        except Exception as e:
            print(f"❌ Error getting system health: {e}")
            return None
    
    def publish_health_status(self):
        """Publish system health status"""
        try:
            if not self.connected:
                return False
            
            health_data = self.get_system_health()
            if not health_data:
                return False
            
            topic = self.topics["health"]
            result = self.client.publish(topic, json.dumps(health_data), qos=0)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Error publishing health status: {e}")
            return False
    
    def start_continuous_publishing(self):
        """Start continuous publishing with tracking-based counts"""
        def publish_loop():
            print("🚀 Starting tracking-based MQTT publishing (1-second intervals)")
            print("📊 Topics:")
            for source, topic in self.topics.items():
                print(f"   {source}: {topic}")
            print("🎯 Method: NVIDIA Analytics Tracker IDs (no detection lines)")
            print()
            
            self.publishing = True
            
            while self.publishing:
                try:
                    if self.connected:
                        # Publish tracking-based counts for each stream
                        for source_id in range(2):  # Only 2 cameras
                            self.publish_tracking_count(source_id)
                        
                        # Publish analytics summary every 5 seconds
                        if int(time.time()) % 5 == 0:
                            self.publish_analytics_summary()
                        
                        # Publish health status every 10 seconds
                        if int(time.time()) % 10 == 0:
                            self.publish_health_status()
                    
                    time.sleep(1.0)  # 1-second intervals
                    
                except Exception as e:
                    print(f"❌ Publishing error: {e}")
                    time.sleep(1.0)
        
        # Start publishing thread
        publish_thread = threading.Thread(target=publish_loop, daemon=True)
        publish_thread.start()
        
        return True
    
    def stop_publishing(self):
        """Stop continuous publishing"""
        self.publishing = False
        print("🛑 Stopped tracking-based MQTT publishing")

def main():
    """Run the tracking-based MQTT publisher"""
    publisher = TrackingMQTTPublisher()
    reconnect_delay = 5  # seconds

    print("🎯 TRACKING-BASED MQTT PUBLISHER")
    print("================================")
    print("📊 Counting Method: NVIDIA Analytics Tracker IDs")
    print("🔄 No detection lines required")
    print("📡 Publishing unique object counts via MQTT")
    print()

    while True:
        try:
            if not publisher.connected:
                print("🔌 Attempting to connect to MQTT broker...")
                if publisher.connect():
                    print("✅ MQTT Publisher connected, starting tracking-based publishing.")
                    publisher.start_continuous_publishing()
                else:
                    print(f"❌ Connection failed. Retrying in {reconnect_delay} seconds...")
                    time.sleep(reconnect_delay)
                    continue

            # If connected, just keep the script alive and check connection
            while publisher.connected:
                time.sleep(1)
                
                # Simulate some tracking data for demonstration
                # In real implementation, this would be called from DeepStream probe
                import random
                if random.random() < 0.1:  # 10% chance to add new object
                    stream_id = random.randint(0, 1)
                    new_object_id = random.randint(1000, 9999)
                    current_objects = list(publisher.tracked_objects[stream_id])
                    if new_object_id not in current_objects:
                        current_objects.append(new_object_id)
                        publisher.update_tracked_objects(stream_id, current_objects)
            
            # This part is reached when on_disconnect sets publisher.connected to False
            print(f"🔌 MQTT disconnected. Attempting to reconnect in {reconnect_delay} seconds...")
            publisher.stop_publishing()
            publisher.client.loop_stop()
            time.sleep(reconnect_delay)

        except KeyboardInterrupt:
            print("\n🛑 Stopping tracking-based MQTT publisher...")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred in the main loop: {e}")
            print(f"🔁 Retrying in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
    
    publisher.disconnect()

if __name__ == "__main__":
    main()
