#!/usr/bin/env python3

"""
Production MQTT Publisher for External Broker
Handles multi-topic broadcasting with per-source counts and system health
"""

import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import psutil
import os
import subprocess
from object_counter import ObjectCounter

class ProductionMQTTPublisher:
    def __init__(self, config_file=None):
        # Load configuration from file
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'components', 'mqtt_broker_config.txt')
        
        self.load_config(config_file)
        
        # Topic configuration - only 2 cameras now
        self.topics = {
            "source0": "camera1",
            "source1": "camera2", 
            "health": "deepstream/health"
        }
        
        self.client = None
        self.connected = False
        self.counter = ObjectCounter()
        self.publishing = False
        
        # Camera location mapping - only cameras 102 and 103
        self.camera_locations = {
            0: {"name": "Camera 1 (102)", "ip": "10.20.100.102", "area": "Production Area 1", "stream": "subtype=0"},
            1: {"name": "Camera 2 (103)", "ip": "10.20.100.103", "area": "Production Area 2", "stream": "subtype=0"}
        }
        
        print(f"🏭 Production MQTT Publisher initialized")
        print(f"📡 Broker: {self.broker_host}:{self.broker_port}")
        print(f"🔐 Client ID: {self.client_id}")
    
    def load_config(self, config_file):
        """Load MQTT configuration from file"""
        import configparser
        
        config = configparser.ConfigParser()
        try:
            config.read(config_file)
            
            # Load MQTT broker settings
            broker_section = config['message-broker']
            self.username = broker_section.get('username', 'admin')
            self.password = broker_section.get('password', 'password')
            self.client_id = broker_section.get('client-id', 'deepstream-production-counter')
            
            # Default broker settings (can be overridden by environment variables)
            self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
            self.broker_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
            
        except Exception as e:
            print(f"⚠️  Warning: Could not load MQTT config from {config_file}: {e}")
            print("Using default configuration...")
            self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
            self.broker_port = int(os.getenv('MQTT_BROKER_PORT', '1883'))
            self.username = os.getenv('MQTT_USERNAME', 'admin')
            self.password = os.getenv('MQTT_PASSWORD', 'password')
            self.client_id = os.getenv('MQTT_CLIENT_ID', 'deepstream-production-counter')
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for MQTT connection (VERSION2)"""
        if reason_code.is_failure:
            print(f"❌ Failed to connect to MQTT broker: {reason_code}")
            self.connected = False
        else:
            self.connected = True
            print(f"✅ Connected to production MQTT broker")
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
    
    def publish_source_count(self, source_id, can_count, total_objects):
        """Publish count for specific source/camera"""
        try:
            if not self.connected:
                return False
            
            camera_info = self.camera_locations.get(source_id, {})
            topic = self.topics.get(f"source{source_id}")
            
            if not topic:
                return False
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "source_id": source_id,
                "camera_name": camera_info.get("name", f"Camera {source_id + 1}"),
                "camera_ip": camera_info.get("ip", "unknown"),
                "location": camera_info.get("area", "unknown"),
                "can_count": can_count,
                "total_objects": total_objects,
                "message_type": "count_update"
            }
            
            result = self.client.publish(topic, json.dumps(payload), qos=0)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Error publishing source count: {e}")
            return False
    
    def get_system_health(self):
        """Get comprehensive system health information"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # GPU information (if available)
            gpu_info = "N/A"
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
            
            # Get current counts
            counts = self.counter.get_all_counts()
            total_cans = sum(stream_data.get('cans', 0) for stream_data in counts.values())
            total_objects = sum(stream_data.get('total_objects', 0) for stream_data in counts.values())
            
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
                "deepstream_running": deepstream_running,
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "disk_usage": f"{disk.percent:.1f}%",
                "gpu_info": gpu_info,
                "total_cans_detected": total_cans,
                "total_objects_detected": total_objects,
                "active_cameras": 2,  # Only 2 cameras now
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
        """Start continuous publishing every 1 second"""
        def publish_loop():
            print("🚀 Starting continuous MQTT publishing (1-second intervals)")
            print("📊 Topics:")
            for source, topic in self.topics.items():
                print(f"   {source}: {topic}")
            print()
            
            self.publishing = True
            
            while self.publishing:
                try:
                    if self.connected:
                        # Publish individual source counts (only 2 sources now)
                        counts = self.counter.get_all_counts()
                        
                        for source_id in range(2):  # Only 2 cameras
                            stream_key = f"stream_{source_id}"
                            stream_data = counts.get(stream_key, {"cans": 0, "total_objects": 0})
                            
                            self.publish_source_count(
                                source_id,
                                stream_data.get("cans", 0),
                                stream_data.get("total_objects", 0)
                            )
                        
                        # Publish health status every 5 seconds
                        if int(time.time()) % 5 == 0:
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
        print("🛑 Stopped continuous MQTT publishing")

def main():
    """Test the production MQTT publisher"""
    publisher = ProductionMQTTPublisher()
    
    try:
        if publisher.connect():
            print("✅ Production MQTT publisher connected")
            publisher.start_continuous_publishing()
            
            # Keep running
            print("🔄 Publishing to production MQTT broker...")
            print("🛑 Press Ctrl+C to stop")
            
            while True:
                time.sleep(1)
                
        else:
            print("❌ Failed to connect to production MQTT broker")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping production MQTT publisher...")
    finally:
        publisher.disconnect()

if __name__ == "__main__":
    main()
