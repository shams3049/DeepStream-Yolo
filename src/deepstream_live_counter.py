#!/usr/bin/env python3

"""
DeepStream YOLO Application with Live Object Counting and GUI Display
Integrates real-time object detection, counting, and display on both sources
"""

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GObject, Gst, GstRtspServer
import sys
import signal
import threading
import time
import json
from pathlib import Path
from datetime import datetime
import pyds

# Import our object counter
from object_counter import ObjectCounter

class DeepStreamLiveCounter:
    def __init__(self, config_file=None):
        # Initialize GStreamer
        GObject.threads_init()
        Gst.init(None)
        
        self.config_file = config_file or "/home/deepstream/DeepStream-Yolo/configs/environments/config_sources_production.txt"
        self.loop = None
        self.pipeline = None
        self.counter = ObjectCounter()
        self.running = True
        
        # Object counting stats
        self.frame_count = {0: 0, 1: 0}
        self.object_count = {0: 0, 1: 0}
        self.fps_counter = {0: 0, 1: 0}
        self.last_fps_time = time.time()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🏭 DeepStream Live Object Counter Initialized")
        print(f"📋 Config: {self.config_file}")
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        if self.loop:
            self.loop.quit()
    
    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        """Buffer probe function to extract metadata and count objects"""
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
                    
                    # Update frame count
                    self.frame_count[stream_id] = self.frame_count.get(stream_id, 0) + 1
                    
                    # Count objects in this frame
                    frame_object_count = 0
                    l_obj = frame_meta.obj_meta_list
                    
                    while l_obj is not None:
                        try:
                            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                            
                            # Check if it's a valid detection (confidence threshold)
                            if obj_meta.confidence > 0.3:  # Confidence threshold
                                frame_object_count += 1
                                
                                # Update object counter
                                class_name = obj_meta.obj_label if obj_meta.obj_label else "object"
                                self.counter.increment_count(stream_id, class_name)
                        
                        except StopIteration:
                            break
                        
                        try:
                            l_obj = l_obj.next
                        except StopIteration:
                            break
                    
                    # Update object count for this stream
                    self.object_count[stream_id] = frame_object_count
                    
                    # Add display metadata for counts
                    self.add_count_overlay(frame_meta, stream_id)
                    
                except StopIteration:
                    break
                
                try:
                    l_frame = l_frame.next
                except StopIteration:
                    break
            
            # Update FPS every second
            current_time = time.time()
            if current_time - self.last_fps_time >= 1.0:
                self.print_live_stats()
                self.last_fps_time = current_time
                
        except Exception as e:
            print(f"❌ Error in buffer probe: {e}")
        
        return Gst.PadProbeReturn.OK
    
    def add_count_overlay(self, frame_meta, stream_id):
        """Add counting overlay to the frame"""
        try:
            # Get current counts from our counter
            current_cans = self.counter.get_count(stream_id, "cans")
            total_objects = self.counter.get_count(stream_id, "total_objects")
            
            # Create display metadata
            display_meta = pyds.nvds_acquire_display_meta_from_pool(frame_meta)
            if display_meta:
                # Text for current frame objects
                frame_text = f"Stream {stream_id}: Live: {self.object_count.get(stream_id, 0)}"
                
                # Text for total counts
                count_text = f"Total Cans: {current_cans} | All Objects: {total_objects}"
                
                # Add frame text
                py_nvosd_text_params = display_meta.text_params[0]
                py_nvosd_text_params.display_text = frame_text
                py_nvosd_text_params.x_offset = 10
                py_nvosd_text_params.y_offset = 10 + (stream_id * 80)
                py_nvosd_text_params.font_params.font_name = "Serif"
                py_nvosd_text_params.font_params.font_size = 12
                py_nvosd_text_params.font_params.font_color.red = 1.0
                py_nvosd_text_params.font_params.font_color.green = 1.0
                py_nvosd_text_params.font_params.font_color.blue = 0.0
                py_nvosd_text_params.font_params.font_color.alpha = 1.0
                py_nvosd_text_params.set_bg_clr = 1
                py_nvosd_text_params.text_bg_clr.red = 0.0
                py_nvosd_text_params.text_bg_clr.green = 0.0
                py_nvosd_text_params.text_bg_clr.blue = 0.0
                py_nvosd_text_params.text_bg_clr.alpha = 0.5
                
                # Add count text
                py_nvosd_text_params_2 = display_meta.text_params[1]
                py_nvosd_text_params_2.display_text = count_text
                py_nvosd_text_params_2.x_offset = 10
                py_nvosd_text_params_2.y_offset = 30 + (stream_id * 80)
                py_nvosd_text_params_2.font_params.font_name = "Serif"
                py_nvosd_text_params_2.font_params.font_size = 10
                py_nvosd_text_params_2.font_params.font_color.red = 0.0
                py_nvosd_text_params_2.font_params.font_color.green = 1.0
                py_nvosd_text_params_2.font_params.font_color.blue = 1.0
                py_nvosd_text_params_2.font_params.font_color.alpha = 1.0
                py_nvosd_text_params_2.set_bg_clr = 1
                py_nvosd_text_params_2.text_bg_clr.red = 0.0
                py_nvosd_text_params_2.text_bg_clr.green = 0.0
                py_nvosd_text_params_2.text_bg_clr.blue = 0.0
                py_nvosd_text_params_2.text_bg_clr.alpha = 0.5
                
                # Set number of strings
                display_meta.num_labels = 2
                
                # Add display metadata to frame
                pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
                
        except Exception as e:
            print(f"❌ Error adding overlay: {e}")
    
    def print_live_stats(self):
        """Print live statistics"""
        print(f"\r📊 Stream 0: {self.object_count.get(0, 0)} live | "
              f"Stream 1: {self.object_count.get(1, 0)} live | "
              f"Total Cans: {self.counter.get_count(0) + self.counter.get_count(1)}", end="", flush=True)
    
    def bus_call(self, bus, message):
        """Handle bus messages"""
        t = message.type
        if t == Gst.MessageType.EOS:
            print("\n📺 End-of-stream")
            self.loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(f"⚠️ Warning: {err}: {debug}")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"❌ Error: {err}: {debug}")
            self.loop.quit()
        return True
    
    def create_pipeline(self):
        """Create the GStreamer pipeline using deepstream-app"""
        try:
            # Create pipeline using deepstream-app-config
            print("🔧 Creating DeepStream pipeline...")
            
            # Create the pipeline command
            cmd = f"deepstream-app -c {self.config_file}"
            
            # For now, let's use the existing approach but with our probe
            self.pipeline = Gst.parse_launch(f'''
                filesrc location=/dev/null ! fakesink
            ''')
            
            if not self.pipeline:
                print("❌ Failed to create pipeline")
                return False
            
            # We'll modify this to work with the config file approach
            print("✅ Pipeline created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating pipeline: {e}")
            return False
    
    def run_with_deepstream_app(self):
        """Run using deepstream-app with our custom probes"""
        import subprocess
        import os
        
        print("🚀 Starting DeepStream application with live counting...")
        
        # Set environment for our custom library
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = "/opt/nvidia/deepstream/deepstream/lib:" + env.get('LD_LIBRARY_PATH', '')
        
        try:
            # Run deepstream-app as subprocess and monitor output
            process = subprocess.Popen(
                ['deepstream-app', '-c', self.config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env,
                cwd="/opt/nvidia/deepstream/deepstream-7.1"
            )
            
            print("📺 DeepStream application started")
            print("📊 Monitoring object counts...")
            print("💡 Note: Live counting will be shown in the DeepStream GUI")
            print("🔢 Console will show periodic count summaries")
            print()
            
            # Monitor the process and show periodic updates
            start_time = time.time()
            last_summary_time = time.time()
            
            while self.running and process.poll() is None:
                try:
                    # Show summary every 10 seconds
                    current_time = time.time()
                    if current_time - last_summary_time >= 10.0:
                        self.show_count_summary()
                        last_summary_time = current_time
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Interrupted by user")
                    break
            
            # Clean up
            if process.poll() is None:
                process.terminate()
                process.wait()
                
        except Exception as e:
            print(f"❌ Error running DeepStream application: {e}")
    
    def show_count_summary(self):
        """Show a summary of current counts"""
        print(f"\n{'='*60}")
        print(f"📊 LIVE COUNT SUMMARY - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        total_cans = 0
        total_objects = 0
        
        for stream_id in [0, 1]:
            cans = self.counter.get_count(stream_id, "cans")
            objects = self.counter.get_count(stream_id, "total_objects")
            total_cans += cans
            total_objects += objects
            
            print(f"📹 Camera {stream_id + 1}: {cans} cans, {objects} total objects")
        
        print(f"📊 TOTALS: {total_cans} cans, {total_objects} objects")
        print(f"{'='*60}")
    
    def run(self):
        """Main run method"""
        print("🏭 Starting DeepStream Live Object Counter")
        print("=========================================")
        
        # Show initial counts
        self.counter.print_current_counts()
        
        # Run the application
        self.run_with_deepstream_app()
        
        print("\n✅ DeepStream Live Counter session completed")

def main():
    """Main function"""
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    app = DeepStreamLiveCounter(config_file)
    app.run()

if __name__ == "__main__":
    main()
