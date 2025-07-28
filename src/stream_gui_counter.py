#!/usr/bin/env python3

"""
Stream Object Counter with Enhanced GUI Display
Shows object counts per input stream prominently in the GUI
Integrates with existing DeepStream analytics infrastructure
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import sys
import signal
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

# Try to import pyds (DeepStream Python bindings)
try:
    import pyds
    PYDS_AVAILABLE = True
    print("✅ DeepStream Python bindings available")
except ImportError:
    PYDS_AVAILABLE = False
    print("⚠️ DeepStream Python bindings not available, using simulation mode")

class StreamObjectCounter:
    def __init__(self, config_file=None):
        # Initialize GStreamer
        GObject.threads_init()
        Gst.init(None)
        
        self.config_file = config_file or "/home/deepstream/DeepStream-Yolo/configs/environments/config_sources_production.txt"
        self.running = True
        
        # Per-stream object tracking with enhanced display info
        self.stream_data = {
            0: {
                "name": "Camera 1 (102)",
                "current_objects": 0,           # Objects currently visible in frame
                "total_detected": 0,            # Total objects detected ever
                "session_count": 0,             # Objects detected this session
                "last_detection_time": None,
                "avg_confidence": 0.0,
                "objects_by_class": {},         # Count by object class
                "fps": 0.0,
                "frame_count": 0
            },
            1: {
                "name": "Camera 2 (103)", 
                "current_objects": 0,
                "total_detected": 0,
                "session_count": 0,
                "last_detection_time": None,
                "avg_confidence": 0.0,
                "objects_by_class": {},
                "fps": 0.0,
                "frame_count": 0
            }
        }
        
        # Performance tracking
        self.last_fps_time = time.time()
        self.persistence_file = Path("data/persistence/stream_object_counts.json")
        
        # Object class names for display
        self.class_names = {
            0: "Person", 1: "Bicycle", 2: "Car", 3: "Motorbike", 5: "Bus",
            7: "Truck", 9: "Boat", 16: "Bird", 17: "Cat", 18: "Dog"
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.load_persistent_data()
        print(f"🎥 Stream Object Counter initialized for per-stream counting")
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Shutting down Stream Object Counter...")
        self.running = False
        self.save_persistent_data()
    
    def load_persistent_data(self):
        """Load persistent counting data"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    for stream_id in [0, 1]:
                        if str(stream_id) in data:
                            stream_info = data[str(stream_id)]
                            self.stream_data[stream_id]["total_detected"] = stream_info.get("total_detected", 0)
                print(f"✅ Loaded persistent stream data from {self.persistence_file}")
        except Exception as e:
            print(f"⚠️ Could not load persistent data: {e}")
    
    def save_persistent_data(self):
        """Save current counting data"""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for stream_id in [0, 1]:
                stream_info = self.stream_data[stream_id]
                data[str(stream_id)] = {
                    "name": stream_info["name"],
                    "total_detected": stream_info["total_detected"],
                    "session_count": stream_info["session_count"],
                    "last_updated": datetime.now().isoformat()
                }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving persistent data: {e}")
    
    def count_objects_in_frame(self, frame_meta, stream_id):
        """Count and analyze objects in current frame"""
        stream_info = self.stream_data[stream_id]
        
        # Reset frame counters
        stream_info["current_objects"] = 0
        stream_info["objects_by_class"].clear()
        confidence_sum = 0.0
        confidence_count = 0
        
        # Count objects with good confidence
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                
                # Count objects with confidence > 0.6 for better accuracy
                if obj_meta.confidence > 0.6:
                    stream_info["current_objects"] += 1
                    stream_info["session_count"] += 1
                    stream_info["total_detected"] += 1
                    
                    # Track by class
                    class_id = obj_meta.class_id
                    class_name = self.class_names.get(class_id, f"Class_{class_id}")
                    if class_name not in stream_info["objects_by_class"]:
                        stream_info["objects_by_class"][class_name] = 0
                    stream_info["objects_by_class"][class_name] += 1
                    
                    # Track confidence
                    confidence_sum += obj_meta.confidence
                    confidence_count += 1
                    
                    stream_info["last_detection_time"] = datetime.now()
                
            except StopIteration:
                break
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        
        # Calculate average confidence
        if confidence_count > 0:
            stream_info["avg_confidence"] = confidence_sum / confidence_count
        else:
            stream_info["avg_confidence"] = 0.0
    
    def create_prominent_overlay(self, frame_meta, stream_id):
        """Create prominent per-stream object count overlay"""
        if not PYDS_AVAILABLE:
            return
        
        try:
            # Get display metadata
            display_meta = pyds.nvds_acquire_display_meta_from_pool(frame_meta)
            if not display_meta:
                return
            
            stream_info = self.stream_data[stream_id]
            
            # Position based on stream (side-by-side display)
            if stream_id == 0:
                # Left stream - position overlay on left side
                base_x = 20
                base_y = 20
            else:
                # Right stream - position overlay on right side
                base_x = 680  # Assuming 1280 width, position on right half
                base_y = 20
            
            # Stream header with prominent styling
            header_text = f"🎥 {stream_info['name']}"
            text_params = display_meta.text_params[0]
            text_params.display_text = header_text
            text_params.x_offset = base_x
            text_params.y_offset = base_y
            text_params.font_params.font_name = "Serif"
            text_params.font_params.font_size = 18
            text_params.font_params.font_color.red = 1.0
            text_params.font_params.font_color.green = 1.0
            text_params.font_params.font_color.blue = 0.0
            text_params.font_params.font_color.alpha = 1.0
            text_params.set_bg_clr = 1
            text_params.text_bg_clr.red = 0.0
            text_params.text_bg_clr.green = 0.0
            text_params.text_bg_clr.blue = 0.0
            text_params.text_bg_clr.alpha = 0.9
            
            # MAIN COUNT DISPLAY - Large and prominent
            count_text = f"🔢 OBJECTS: {stream_info['current_objects']}"
            text_params_2 = display_meta.text_params[1]
            text_params_2.display_text = count_text
            text_params_2.x_offset = base_x
            text_params_2.y_offset = base_y + 30
            text_params_2.font_params.font_name = "Serif"
            text_params_2.font_params.font_size = 24  # Large font for main count
            text_params_2.font_params.font_color.red = 0.0
            text_params_2.font_params.font_color.green = 1.0
            text_params_2.font_params.font_color.blue = 0.0
            text_params_2.font_params.font_color.alpha = 1.0
            text_params_2.set_bg_clr = 1
            text_params_2.text_bg_clr.red = 0.0
            text_params_2.text_bg_clr.green = 0.0
            text_params_2.text_bg_clr.blue = 0.0
            text_params_2.text_bg_clr.alpha = 0.9
            
            # Session and total counts
            totals_text = f"📊 Session: {stream_info['session_count']} | Total: {stream_info['total_detected']}"
            text_params_3 = display_meta.text_params[2]
            text_params_3.display_text = totals_text
            text_params_3.x_offset = base_x
            text_params_3.y_offset = base_y + 65
            text_params_3.font_params.font_name = "Serif"
            text_params_3.font_params.font_size = 14
            text_params_3.font_params.font_color.red = 0.0
            text_params_3.font_params.font_color.green = 0.8
            text_params_3.font_params.font_color.blue = 1.0
            text_params_3.font_params.font_color.alpha = 1.0
            text_params_3.set_bg_clr = 1
            text_params_3.text_bg_clr.red = 0.0
            text_params_3.text_bg_clr.green = 0.0
            text_params_3.text_bg_clr.blue = 0.0
            text_params_3.text_bg_clr.alpha = 0.8
            
            # Object breakdown by class (top 3 classes)
            class_breakdown = ""
            if stream_info["objects_by_class"]:
                sorted_classes = sorted(stream_info["objects_by_class"].items(), 
                                      key=lambda x: x[1], reverse=True)[:3]
                class_breakdown = " | ".join([f"{name}: {count}" for name, count in sorted_classes])
            else:
                class_breakdown = "No objects detected"
            
            breakdown_text = f"📋 {class_breakdown}"
            text_params_4 = display_meta.text_params[3]
            text_params_4.display_text = breakdown_text
            text_params_4.x_offset = base_x
            text_params_4.y_offset = base_y + 90
            text_params_4.font_params.font_name = "Serif"
            text_params_4.font_params.font_size = 12
            text_params_4.font_params.font_color.red = 1.0
            text_params_4.font_params.font_color.green = 1.0
            text_params_4.font_params.font_color.blue = 1.0
            text_params_4.font_params.font_color.alpha = 1.0
            text_params_4.set_bg_clr = 1
            text_params_4.text_bg_clr.red = 0.0
            text_params_4.text_bg_clr.green = 0.0
            text_params_4.text_bg_clr.blue = 0.0
            text_params_4.text_bg_clr.alpha = 0.8
            
            # FPS and confidence info
            stats_text = f"⚡ FPS: {stream_info['fps']:.1f} | 🎯 Conf: {stream_info['avg_confidence']:.2f}"
            text_params_5 = display_meta.text_params[4]
            text_params_5.display_text = stats_text
            text_params_5.x_offset = base_x
            text_params_5.y_offset = base_y + 115
            text_params_5.font_params.font_name = "Serif"
            text_params_5.font_params.font_size = 10
            text_params_5.font_params.font_color.red = 0.8
            text_params_5.font_params.font_color.green = 0.8
            text_params_5.font_params.font_color.blue = 0.8
            text_params_5.font_params.font_color.alpha = 1.0
            text_params_5.set_bg_clr = 1
            text_params_5.text_bg_clr.red = 0.0
            text_params_5.text_bg_clr.green = 0.0
            text_params_5.text_bg_clr.blue = 0.0
            text_params_5.text_bg_clr.alpha = 0.8
            
            # Set number of text elements
            display_meta.num_labels = 5
            
            # Add display metadata to frame
            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
            
        except Exception as e:
            print(f"❌ Error creating overlay for stream {stream_id}: {e}")
    
    def update_fps(self, stream_id):
        """Update FPS calculation for stream"""
        current_time = time.time()
        self.stream_data[stream_id]["frame_count"] += 1
        
        if current_time - self.last_fps_time >= 1.0:
            # Update FPS for all streams
            time_diff = current_time - self.last_fps_time
            for sid in [0, 1]:
                if sid in self.stream_data:
                    self.stream_data[sid]["fps"] = self.stream_data[sid]["frame_count"] / time_diff
                    self.stream_data[sid]["frame_count"] = 0
            
            self.last_fps_time = current_time
            self.print_stream_summary()
    
    def print_stream_summary(self):
        """Print live stream summary to console"""
        stream0 = self.stream_data[0]
        stream1 = self.stream_data[1]
        
        total_current = stream0["current_objects"] + stream1["current_objects"]
        total_session = stream0["session_count"] + stream1["session_count"]
        
        print(f"\r🎥 Live: {total_current} | "
              f"Cam1: {stream0['current_objects']}({stream0['total_detected']}) | "
              f"Cam2: {stream1['current_objects']}({stream1['total_detected']}) | "
              f"Session: {total_session}", 
              end="", flush=True)
    
    def run_with_simulation(self):
        """Run with simulation for testing without DeepStream"""
        import random
        import threading
        
        print("🎮 Running in simulation mode for testing...")
        print("📊 Simulating per-stream object detection")
        
        def simulate_detection():
            while self.running:
                for stream_id in [0, 1]:
                    # Simulate object detection
                    if random.random() < 0.4:  # 40% chance
                        objects = random.randint(0, 5)
                        self.stream_data[stream_id]["current_objects"] = objects
                        
                        if objects > 0:
                            self.stream_data[stream_id]["session_count"] += objects
                            self.stream_data[stream_id]["total_detected"] += objects
                            self.stream_data[stream_id]["avg_confidence"] = random.uniform(0.7, 0.95)
                            
                            # Simulate class distribution
                            classes = ["Person", "Car", "Bicycle", "Bus"]
                            self.stream_data[stream_id]["objects_by_class"].clear()
                            for _ in range(objects):
                                class_name = random.choice(classes)
                                if class_name not in self.stream_data[stream_id]["objects_by_class"]:
                                    self.stream_data[stream_id]["objects_by_class"][class_name] = 0
                                self.stream_data[stream_id]["objects_by_class"][class_name] += 1
                    
                    # Simulate FPS
                    self.stream_data[stream_id]["fps"] = random.uniform(25, 30)
                
                self.print_stream_summary()
                time.sleep(2)
        
        sim_thread = threading.Thread(target=simulate_detection, daemon=True)
        sim_thread.start()
        
        try:
            while self.running:
                time.sleep(5)
                self.show_detailed_summary()
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped")
    
    def show_detailed_summary(self):
        """Show detailed per-stream summary"""
        print(f"\n{'='*70}")
        print(f"🎥 PER-STREAM OBJECT COUNT SUMMARY - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        total_current = 0
        total_session = 0
        total_all = 0
        
        for stream_id in [0, 1]:
            stream_info = self.stream_data[stream_id]
            total_current += stream_info["current_objects"]
            total_session += stream_info["session_count"]
            total_all += stream_info["total_detected"]
            
            print(f"📹 {stream_info['name']}:")
            print(f"   🔢 Current Objects: {stream_info['current_objects']}")
            print(f"   📊 Session Count: {stream_info['session_count']}")
            print(f"   📈 Total Detected: {stream_info['total_detected']}")
            print(f"   ⚡ FPS: {stream_info['fps']:.1f}")
            print(f"   🎯 Avg Confidence: {stream_info['avg_confidence']:.2f}")
            
            if stream_info["objects_by_class"]:
                print(f"   📋 Object Types: {stream_info['objects_by_class']}")
            print()
        
        print(f"🌟 TOTALS: {total_current} current | {total_session} session | {total_all} all-time")
        print(f"{'='*70}")
    
    def run(self):
        """Main run method"""
        print("🎥 Stream Object Counter with Enhanced GUI")
        print("==========================================")
        print("📊 Features: Per-stream object counting with prominent display")
        print("🔢 GUI: Large object counts prominently shown per camera stream")
        print("📈 Tracking: Live counts, session totals, object types")
        print()
        
        try:
            if PYDS_AVAILABLE:
                print("🚀 DeepStream integration mode - modify existing scripts to use this counter")
                print("💡 This counter provides enhanced overlay functions for per-stream display")
            else:
                self.run_with_simulation()
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        finally:
            self.save_persistent_data()
            print("\n✅ Stream object counter session completed")
            self.show_detailed_summary()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Stream Object Counter with Enhanced GUI')
    parser.add_argument('config', nargs='?', help='DeepStream config file path')
    args = parser.parse_args()
    
    counter = StreamObjectCounter(args.config)
    counter.run()

if __name__ == "__main__":
    main()
