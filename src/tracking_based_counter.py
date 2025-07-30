#!/usr/bin/env python3

"""
Tracking-Based Object Counter using NVIDIA Analytics Tracked Object IDs
Counts unique objects per stream using tracker IDs instead of detection lines
"""

import sys
import json
import time
import threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# DeepStream imports
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import GObject, Gst
    import pyds
    PYDS_AVAILABLE = True
    print("✅ DeepStream Python bindings available - Tracking mode enabled")
except Exception as e:
    PYDS_AVAILABLE = False
    print(f"⚠️  DeepStream Python bindings not available: {e}")
    print("📝 Running in simulation mode for testing")


class TrackingBasedCounter:
    def __init__(self, config_file_path=None, persistence_file="data/persistence/tracking_counts.json"):
        self.config_file = config_file_path
        self.persistence_file = Path(persistence_file)
        
        # Track unique object IDs per stream
        self.tracked_objects = defaultdict(set)  # {stream_id: {object_id1, object_id2, ...}}
        self.stream_totals = defaultdict(int)     # {stream_id: total_count}
        self.session_counts = defaultdict(int)    # {stream_id: session_count}
        
        # Performance metrics
        self.frame_count = defaultdict(int)
        self.fps_start_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Pipeline components
        self.pipeline = None
        self.loop = None
        
        print("🎯 Tracking-Based Object Counter initialized")
        print("📊 Method: Unique tracker IDs instead of detection lines")
        print("💾 Persistence file:", self.persistence_file)
        
        self.load_session_data()
        
    def load_session_data(self):
        """Load session data from persistence"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    
                for stream_id, stream_data in data.items():
                    if isinstance(stream_data, dict):
                        self.stream_totals[int(stream_id)] = stream_data.get('total_count', 0)
                        print(f"📊 Loaded Stream {stream_id}: {stream_data.get('total_count', 0)} total objects")
                        
        except Exception as e:
            print(f"⚠️  Could not load session data: {e}")
    
    def save_session_data(self):
        """Save current session data"""
        try:
            # Ensure directory exists
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for stream_id in self.stream_totals:
                data[str(stream_id)] = {
                    'total_count': self.stream_totals[stream_id],
                    'session_count': self.session_counts[stream_id],
                    'last_updated': datetime.now().isoformat(),
                    'unique_objects_this_session': len(self.tracked_objects[stream_id])
                }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving session data: {e}")
    
    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        """Buffer probe to process tracked objects from NVIDIA Analytics"""
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
                    
                    # Update frame count for FPS calculation
                    self.frame_count[stream_id] += 1
                    
                    # Process tracked objects in this frame
                    self.process_tracked_objects(frame_meta, stream_id)
                    
                    # Add display overlay
                    self.add_tracking_overlay(frame_meta, stream_id)
                    
                except StopIteration:
                    break
                
                try:
                    l_frame = l_frame.next
                except StopIteration:
                    break
        
        except Exception as e:
            print(f"❌ Error in tracking probe: {e}")
        
        return Gst.PadProbeReturn.OK
    
    def process_tracked_objects(self, frame_meta, stream_id):
        """Process tracked objects and count unique IDs"""
        l_obj = frame_meta.obj_meta_list
        current_frame_objects = set()
        
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                
                # Check if object has valid tracking ID and meets confidence threshold
                if (obj_meta.object_id != pyds.UNTRACKED_OBJECT_ID and 
                    obj_meta.confidence > 0.5):  # Confidence threshold
                    
                    object_key = f"{stream_id}_{obj_meta.object_id}"
                    current_frame_objects.add(obj_meta.object_id)
                    
                    # If this is a new unique object for this stream
                    if obj_meta.object_id not in self.tracked_objects[stream_id]:
                        with self.lock:
                            self.tracked_objects[stream_id].add(obj_meta.object_id)
                            self.session_counts[stream_id] += 1
                            self.stream_totals[stream_id] += 1
                            
                            # Update persistent counter
                            class_name = obj_meta.obj_label if obj_meta.obj_label else "object"
                            self.counter.increment_count(stream_id, class_name)
                            
                            print(f"🆕 New object tracked: Stream {stream_id}, ID {obj_meta.object_id}, Class: {class_name}")
                            print(f"📊 Stream {stream_id} - Session: {self.session_counts[stream_id]}, Total: {self.stream_totals[stream_id]}")
            
            except StopIteration:
                break
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
    
    def add_tracking_overlay(self, frame_meta, stream_id):
        """Add tracking-based count overlay to the display"""
        try:
            # Calculate current FPS
            current_time = time.time()
            elapsed = current_time - self.fps_start_time
            fps = self.frame_count[stream_id] / elapsed if elapsed > 0 else 0
            
            # Get current counts
            unique_objects_current = len(self.tracked_objects[stream_id])
            session_count = self.session_counts[stream_id]
            total_count = self.stream_totals[stream_id]
            
            # Create display metadata
            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            if display_meta:
                # Position based on stream ID (side by side for 2 cameras)
                if stream_id == 0:
                    x_offset = 50
                    title = "🎥 Camera 1 (102) - TRACKING MODE"
                else:
                    x_offset = 980  # Right side for second camera
                    title = "🎥 Camera 2 (103) - TRACKING MODE"
                
                y_start = 50
                
                # Title
                self.add_text_overlay(display_meta, title, x_offset, y_start, 
                                    font_size=16, font_color=(1.0, 1.0, 0.0, 1.0))  # Yellow
                
                # Unique objects currently visible
                self.add_text_overlay(display_meta, f"🔢 UNIQUE OBJECTS: {unique_objects_current}", 
                                    x_offset, y_start + 30, font_size=18, 
                                    font_color=(0.0, 1.0, 1.0, 1.0))  # Cyan
                
                # Session and total counts
                self.add_text_overlay(display_meta, f"📊 Session: {session_count} | Total: {total_count}", 
                                    x_offset, y_start + 60, font_size=14, 
                                    font_color=(1.0, 0.8, 0.0, 1.0))  # Orange
                
                # FPS and method
                self.add_text_overlay(display_meta, f"⚡ FPS: {fps:.1f} | 🎯 Tracker IDs", 
                                    x_offset, y_start + 90, font_size=12, 
                                    font_color=(0.7, 0.7, 0.7, 1.0))  # Gray
                
                # Status indicator
                status = f"🟢 TRACKING STREAM {stream_id + 1}"
                self.add_text_overlay(display_meta, status, x_offset, y_start + 120, 
                                    font_size=12, font_color=(0.0, 1.0, 0.0, 1.0))  # Green
                
                pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
        except Exception as e:
            print(f"❌ Error adding tracking overlay: {e}")
    
    def add_text_overlay(self, display_meta, text, x, y, font_size=12, font_color=(1.0, 1.0, 1.0, 1.0)):
        """Add text overlay to display"""
        try:
            txt_params = display_meta.text_params[display_meta.num_labels]
            txt_params.display_text = text
            txt_params.x_offset = x
            txt_params.y_offset = y
            txt_params.font_params.font_name = "Serif"
            txt_params.font_params.font_size = font_size
            txt_params.font_params.font_color.red = font_color[0]
            txt_params.font_params.font_color.green = font_color[1]
            txt_params.font_params.font_color.blue = font_color[2]
            txt_params.font_params.font_color.alpha = font_color[3]
            txt_params.set_bg_clr = 1
            txt_params.text_bg_clr.red = 0.0
            txt_params.text_bg_clr.green = 0.0
            txt_params.text_bg_clr.blue = 0.0
            txt_params.text_bg_clr.alpha = 0.7
            display_meta.num_labels += 1
        except Exception as e:
            print(f"❌ Error adding text overlay: {e}")
    
    def create_pipeline(self):
        """Create GStreamer pipeline for DeepStream"""
        if not PYDS_AVAILABLE:
            print("❌ Cannot create pipeline - PyDS not available")
            return False
        
        try:
            # Initialize GStreamer
            Gst.init(None)
            
            # Create pipeline
            self.pipeline = Gst.Pipeline()
            if not self.pipeline:
                print("❌ Unable to create Pipeline")
                return False
            
            # Read the configuration file
            if not self.config_file or not Path(self.config_file).exists():
                print(f"❌ Configuration file not found: {self.config_file}")
                return False
            
            # Use deepstream-app with configuration file
            print(f"📋 Using configuration: {self.config_file}")
            
            # For now, we'll use the existing deepstream-app approach
            # but with our custom probe for tracking-based counting
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating pipeline: {e}")
            return False
    
    def print_statistics(self):
        """Print current tracking statistics"""
        print("\n" + "="*60)
        print("📊 TRACKING-BASED OBJECT COUNTING STATISTICS")
        print("="*60)
        
        total_unique_objects = 0
        total_session_objects = 0
        
        for stream_id in sorted(self.tracked_objects.keys()):
            unique_count = len(self.tracked_objects[stream_id])
            session_count = self.session_counts[stream_id]
            total_count = self.stream_totals[stream_id]
            
            print(f"🎥 Stream {stream_id}: {unique_count} unique | Session: {session_count} | Total: {total_count}")
            
            total_unique_objects += unique_count
            total_session_objects += session_count
        
        print(f"📈 Grand Total: {total_unique_objects} unique objects currently tracked")
        print(f"📊 Session Total: {total_session_objects} new objects this session")
        print("="*60)
    
    def generate_mqtt_payload(self, stream_id):
        """Generate MQTT payload with tracking-based counts"""
        with self.lock:
            unique_objects = len(self.tracked_objects[stream_id])
            session_count = self.session_counts[stream_id]
            total_count = self.stream_totals[stream_id]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "stream_id": stream_id,
                "counting_method": "tracker_ids",
                "unique_objects_tracked": unique_objects,
                "session_count": session_count,
                "total_count": total_count,
                "tracked_object_ids": list(self.tracked_objects[stream_id]),
                "message_type": "tracking_count_update"
            }
    
    def get_all_counts(self):
        """Get all counts for MQTT publishing"""
        return {
            'session_counts': dict(self.session_counts),
            'stream_totals': dict(self.stream_totals),
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Cleanup resources and save data"""
        print("\n🧹 Cleaning up tracking-based counter...")
        self.save_session_data()
        self.print_statistics()
        
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

def main():
    """Test the tracking-based counter"""
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "/home/deepstream/DeepStream-Yolo/configs/environments/config_sources_production.txt"
    
    print("🎯 TRACKING-BASED OBJECT COUNTER")
    print("================================")
    print("📊 Method: NVIDIA Analytics Tracker IDs")
    print("🔄 No detection lines required")
    print(f"📋 Config: {config_file}")
    print()
    
    counter = TrackingBasedCounter(config_file)
    
    try:
        if PYDS_AVAILABLE:
            # In a real implementation, this would integrate with the DeepStream pipeline
            print("✅ Ready for DeepStream integration")
            print("📝 This module provides the probe function for tracking-based counting")
            
            # Keep running for demonstration
            while True:
                time.sleep(10)
                counter.print_statistics()
        else:
            # Simulation mode for testing
            print("🔄 Running in simulation mode...")
            
            # Simulate some tracked objects
            import random
            for i in range(20):
                stream_id = random.randint(0, 1)
                object_id = random.randint(1000, 9999)
                
                # Simulate new object tracking
                if object_id not in counter.tracked_objects[stream_id]:
                    counter.tracked_objects[stream_id].add(object_id)
                    counter.session_counts[stream_id] += 1
                    counter.stream_totals[stream_id] += 1
                    
                    print(f"🆕 Simulated: Stream {stream_id}, Object ID {object_id}")
                
                time.sleep(0.5)
            
            counter.print_statistics()
            
            # Test MQTT payload generation
            for stream_id in [0, 1]:
                payload = counter.generate_mqtt_payload(stream_id)
                print(f"\n📡 MQTT Payload for Stream {stream_id}:")
                print(json.dumps(payload, indent=2))
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        counter.cleanup()

if __name__ == "__main__":
    main()
