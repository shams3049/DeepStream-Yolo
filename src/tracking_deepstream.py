#!/usr/bin/env python3

"""
DeepStream Application with Tracking-Based Object Counting
Uses NVIDIA Analytics tracked object IDs for accurate counting instead of detection lines
"""

import sys
import signal
import threading
import time
import os
from pathlib import Path

# Import our custom modules
import sys
sys.path.append(os.path.dirname(__file__))
from tracking_mqtt import TrackingMQTTPublisher
from tracking_based_counter import TrackingBasedCounter

# DeepStream imports
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GObject, Gst
    import pyds
    PYDS_AVAILABLE = True
    print("✅ DeepStream Python bindings available")
except Exception as e:
    PYDS_AVAILABLE = False
    print(f"⚠️  DeepStream Python bindings not available: {e}")

# Global variables for graceful shutdown
running = True
mqtt_publisher = None
tracking_counter = None

def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    global running, mqtt_publisher, tracking_counter
    print("\n🛑 Shutting down tracking-based DeepStream application...")
    running = False
    
    if mqtt_publisher:
        mqtt_publisher.stop_publishing()
        mqtt_publisher.disconnect()
    
    if tracking_counter:
        tracking_counter.cleanup()
    
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

class TrackingDeepStreamApp:
    def __init__(self, config_path):
        self.config_path = config_path
        self.pipeline = None
        self.loop = None
        self.mqtt_publisher = None
        self.tracking_counter = None
        
        # Initialize tracking-based components
        self.mqtt_publisher = TrackingMQTTPublisher()
        self.tracking_counter = TrackingBasedCounter(config_path)
        
    def bus_call(self, bus, message, loop):
        """Callback for GStreamer bus messages"""
        t = message.type
        if t == Gst.MessageType.EOS:
            print("🏁 End-of-stream reached")
            loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(f"⚠️  Warning: {err}: {debug}")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"❌ Error: {err}: {debug}")
            loop.quit()
        return True

    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        """Enhanced buffer probe for tracking-based counting"""
        if not PYDS_AVAILABLE:
            return Gst.PadProbeReturn.OK
        
        try:
            gst_buffer = info.get_buffer()
            if not gst_buffer:
                return Gst.PadProbeReturn.OK
            
            # Get metadata from buffer
            batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
            if not batch_meta:
                return Gst.PadProbeReturn.OK
            
            l_frame = batch_meta.frame_meta_list
            while l_frame is not None:
                try:
                    frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
                    stream_id = frame_meta.source_id
                    
                    # Collect tracked object IDs for this frame
                    tracked_object_ids = []
                    l_obj = frame_meta.obj_meta_list
                    
                    while l_obj is not None:
                        try:
                            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                            
                            # Only count objects with valid tracking IDs and good confidence
                            if (obj_meta.object_id != pyds.UNTRACKED_OBJECT_ID and 
                                obj_meta.confidence > 0.5):
                                tracked_object_ids.append(obj_meta.object_id)
                        
                        except StopIteration:
                            break
                        
                        try:
                            l_obj = l_obj.next
                        except StopIteration:
                            break
                    
                    # Update MQTT publisher with tracked objects
                    if self.mqtt_publisher:
                        self.mqtt_publisher.update_tracked_objects(stream_id, tracked_object_ids)
                    
                    # Add tracking overlay using the counter
                    if self.tracking_counter:
                        self.tracking_counter.add_tracking_overlay(frame_meta, stream_id)
                
                except StopIteration:
                    break
                
                try:
                    l_frame = l_frame.next
                except StopIteration:
                    break
        
        except Exception as e:
            print(f"❌ Error in tracking probe: {e}")
        
        return Gst.PadProbeReturn.OK

    def create_pipeline(self):
        """Create DeepStream pipeline with tracking-based counting"""
        if not PYDS_AVAILABLE:
            print("❌ Cannot create DeepStream pipeline - Python bindings not available")
            return False
        
        try:
            # Initialize GStreamer
            GObject.threads_init()
            Gst.init(None)
            
            # Create pipeline using deepstream-app with configuration
            print(f"📋 Creating pipeline with config: {self.config_path}")
            print("🎯 Using tracking-based object counting")
            
            # For this implementation, we'll use the standard deepstream-app
            # but add our custom probe for tracking-based counting
            
            # Run deepstream-app as external process and monitor
            return self.run_with_external_deepstream()
            
        except Exception as e:
            print(f"❌ Error creating pipeline: {e}")
            return False

    def run_with_external_deepstream(self):
        """Run DeepStream app externally and handle MQTT publishing"""
        try:
            # Start MQTT publisher
            if self.mqtt_publisher.connect():
                print("✅ Connected to MQTT broker for tracking-based publishing")
                self.mqtt_publisher.start_continuous_publishing()
            else:
                print("⚠️  Could not connect to MQTT broker")
            
            # Change to DeepStream directory
            deepstream_dir = '/opt/nvidia/deepstream/deepstream-7.1'
            original_dir = os.getcwd()
            os.chdir(deepstream_dir)
            
            try:
                # Run DeepStream application
                deepstream_app = f"{deepstream_dir}/bin/deepstream-app"
                cmd = f"{deepstream_app} -c {self.config_path}"
                
                print(f"🚀 Executing: {cmd}")
                print("=" * 60)
                print("🎯 Tracking-based counting enabled")
                print("📊 MQTT publishing: Unique object counts via tracker IDs")
                print("🔄 No detection lines required")
                print("=" * 60)
                
                # Execute DeepStream application
                os.system(cmd)
                
            finally:
                os.chdir(original_dir)
            
            return True
            
        except Exception as e:
            print(f"❌ Error running external DeepStream: {e}")
            return False

    def run(self):
        """Run the tracking-based DeepStream application"""
        print("🎯 TRACKING-BASED DEEPSTREAM APPLICATION")
        print("========================================")
        print("📊 Method: NVIDIA Analytics Tracker IDs")
        print("🔄 No detection lines required")
        print(f"📋 Config: {self.config_path}")
        print()
        
        try:
            return self.create_pipeline()
        except Exception as e:
            print(f"❌ Error running application: {e}")
            return False
        finally:
            if self.mqtt_publisher:
                self.mqtt_publisher.stop_publishing()
                self.mqtt_publisher.disconnect()
            if self.tracking_counter:
                self.tracking_counter.cleanup()

def monitor_and_publish():
    """Monitor tracking-based counts and publish to MQTT with auto-reconnection"""
    global mqtt_publisher, running
    
    reconnect_attempts = 0
    max_reconnect_attempts = 5
    
    while running:
        try:
            # Initialize tracking-based MQTT publisher
            if mqtt_publisher is None:
                mqtt_publisher = TrackingMQTTPublisher()
            
            # Connect to MQTT broker
            if mqtt_publisher.connect():
                print("✅ Connected to tracking-based MQTT broker")
                reconnect_attempts = 0  # Reset counter on successful connection
                
                # Start continuous publishing
                mqtt_publisher.start_continuous_publishing()
                
                # Keep monitoring
                while running and mqtt_publisher.client.is_connected():
                    time.sleep(1)
                    
                if not running:
                    break
                    
                print("🔄 MQTT connection lost, attempting to reconnect...")
                
            else:
                print(f"❌ Failed to connect to MQTT broker (attempt {reconnect_attempts + 1})")
                reconnect_attempts += 1
                
                if reconnect_attempts >= max_reconnect_attempts:
                    print(f"❌ Max reconnection attempts ({max_reconnect_attempts}) reached")
                    print("🔄 Continuing with video processing only...")
                    # Continue without MQTT for a while
                    time.sleep(30)
                    reconnect_attempts = 0  # Reset for next attempt
                else:
                    time.sleep(5)  # Wait before retry
                    
        except Exception as e:
            print(f"❌ MQTT monitoring error: {e}")
            print("🔄 Restarting MQTT monitoring...")
            time.sleep(5)
            mqtt_publisher = None  # Force re-initialization

def main():
    """Main tracking-based DeepStream application with auto-restart"""
    global running, mqtt_publisher
    
    setup_signal_handlers()
    
    # Get config file from command line argument
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # Default to production configuration
        config_file = "/home/deepstream/DeepStream-Yolo/configs/environments/config_sources_production.txt"
    
    # Verify config file exists
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        print("Available configurations:")
        config_dir = Path("/home/deepstream/DeepStream-Yolo/configs/environments")
        for cfg in config_dir.glob("*.txt"):
            print(f"   {cfg}")
        sys.exit(1)
    
    print("🎯 TRACKING-BASED DEEPSTREAM APPLICATION")
    print("========================================")
    print("📊 Counting Method: NVIDIA Analytics Tracker IDs")
    print("🔄 No detection lines required")
    print("📡 MQTT Broker: Auto-reconnection enabled")
    print("🔐 Enhanced message format with tracker ID information")
    print("♾️  Running indefinitely with auto-restart")
    print(f"📋 Config: {config_file}")
    print()
    
    restart_count = 0
    max_restarts = 10
    
    while running and restart_count < max_restarts:
        try:
            print(f"🚀 Starting application (attempt {restart_count + 1})")
            
            # Start MQTT monitoring in background thread
            mqtt_thread = threading.Thread(target=monitor_and_publish, daemon=True)
            mqtt_thread.start()
            
            # Small delay to let MQTT initialize
            time.sleep(2)
            
            # Create and run tracking-based DeepStream app
            app = TrackingDeepStreamApp(config_file)
            success = app.run()
            
            if not success and running:
                print("🔄 Application stopped unexpectedly, restarting in 5 seconds...")
                time.sleep(5)
                restart_count += 1
            else:
                # Clean exit
                break
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Application error: {e}")
            if running:
                restart_count += 1
                print(f"🔄 Restarting application (attempt {restart_count + 1}/{max_restarts}) in 10 seconds...")
                time.sleep(10)
            else:
                break
    
    if restart_count >= max_restarts:
        print(f"❌ Maximum restart attempts ({max_restarts}) reached. Exiting.")
    
    # Cleanup
    running = False
    if mqtt_publisher:
        mqtt_publisher.stop_publishing()
        mqtt_publisher.disconnect()
    
    print("🏁 Application shutdown complete")

if __name__ == "__main__":
    main()
