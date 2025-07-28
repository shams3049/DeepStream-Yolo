#!/usr/bin/env python3

"""
Production DeepStream Application with Multi-Topic MQTT Broadcasting
Integrates with external MQTT broker for real-time production monitoring
"""

import sys
import signal
import threading
import time
import os
from production_mqtt import ProductionMQTTPublisher
from object_counter import ObjectCounter

# Global variables for graceful shutdown
running = True
mqtt_publisher = None

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global running, mqtt_publisher
    print("\n🛑 Shutting down production DeepStream application...")
    running = False
    
    if mqtt_publisher:
        mqtt_publisher.stop_publishing()
        mqtt_publisher.disconnect()
    
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_deepstream_app(config_path=None):
    """Run the DeepStream application with production configuration"""
    try:
        # Use provided config path or default
        if config_path is None:
            config_path = "/home/deepstream/DeepStream-Yolo/configs/environments/config_sources_production.txt"
        
        print("🏭 Starting Production DeepStream Application")
        print(f"📋 Config: {config_path}")
        
        # Determine source type from config
        if "test" in config_path:
            print(f"🎥 Sources: 2 Test Videos (MP4 files)")
        else:
            print(f"🎥 Sources: 2 RTSP Cameras (10.20.100.102-103)")
        
        print(f"📡 MQTT: External broker configured")
        print()
        
        # Change to DeepStream directory
        deepstream_dir = '/opt/nvidia/deepstream/deepstream-7.1'
        os.chdir(deepstream_dir)
        
        # Run DeepStream application with correct path
        deepstream_app = f"{deepstream_dir}/bin/deepstream-app"
        cmd = f"{deepstream_app} -c {config_path}"
        
        print(f"🚀 Executing: {cmd}")
        print("=" * 60)
        
        # Execute DeepStream application
        os.system(cmd)
        
    except Exception as e:
        print(f"❌ Error running DeepStream application: {e}")

def monitor_and_publish():
    """Monitor object counts and publish to MQTT"""
    global mqtt_publisher, running
    
    try:
        # Initialize MQTT publisher
        mqtt_publisher = ProductionMQTTPublisher()
        
        # Connect to MQTT broker
        if mqtt_publisher.connect():
            print("✅ Connected to production MQTT broker")
            
            # Start continuous publishing
            mqtt_publisher.start_continuous_publishing()
            
            # Keep monitoring
            while running:
                time.sleep(1)
                
        else:
            print("❌ Failed to connect to MQTT broker")
            
    except Exception as e:
        print(f"❌ MQTT monitoring error: {e}")

def main():
    """Main production application"""
    setup_signal_handlers()
    
    # Get config file from command line argument
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    print("🏭 PRODUCTION DEEPSTREAM APPLICATION")
    print("===================================")
    print("📡 External MQTT Broker: Configured via production config")
    print("🔐 Client ID: deepstream-production-counter")
    print("📊 Multi-topic broadcasting every 1 second")
    if config_file:
        print(f"📋 Config: {config_file}")
    print()
    
    try:
        # Start MQTT monitoring in background thread
        mqtt_thread = threading.Thread(target=monitor_and_publish, daemon=True)
        mqtt_thread.start()
        
        # Small delay to let MQTT initialize
        time.sleep(2)
        
        # Run DeepStream application
        run_deepstream_app(config_file)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Production application error: {e}")
    finally:
        global running
        running = False
        if mqtt_publisher:
            mqtt_publisher.stop_publishing()
            mqtt_publisher.disconnect()

if __name__ == "__main__":
    main()
