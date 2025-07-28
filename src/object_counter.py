# Object Counter - Persistent count storage for DeepStream YOLO
# Stores object counts per stream with timestamps for persistence across restarts

import json
import time
import threading
from datetime import datetime
from pathlib import Path

class ObjectCounter:
    def __init__(self, persistence_file="data/persistence/object_counts.json"):
        self.persistence_file = Path(persistence_file)
        self.counts = {
            "stream_0": {"cans": 0, "total_objects": 0, "last_updated": None},
            "stream_1": {"cans": 0, "total_objects": 0, "last_updated": None},
            "stream_2": {"cans": 0, "total_objects": 0, "last_updated": None},
            "stream_3": {"cans": 0, "total_objects": 0, "last_updated": None}
        }
        self.lock = threading.Lock()
        self.load_counts()
    
    def load_counts(self):
        """Load persistent counts from file"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    loaded_counts = json.load(f)
                    self.counts.update(loaded_counts)
                print(f"✅ Loaded persistent counts from {self.persistence_file}")
                self.print_current_counts()
            else:
                print(f"📁 No existing counts file found, starting fresh")
                self.save_counts()
        except Exception as e:
            print(f"⚠️ Error loading counts: {e}, starting with fresh counts")
    
    def save_counts(self):
        """Save current counts to persistent storage"""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_file, 'w') as f:
                json.dump(self.counts, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving counts: {e}")
    
    def increment_count(self, stream_id, object_class="can"):
        """Increment count for specific stream and object type"""
        with self.lock:
            stream_key = f"stream_{stream_id}"
            if stream_key in self.counts:
                if object_class == "can" or object_class == "bottle":
                    self.counts[stream_key]["cans"] += 1
                self.counts[stream_key]["total_objects"] += 1
                self.counts[stream_key]["last_updated"] = datetime.now().isoformat()
                self.save_counts()
                return self.counts[stream_key]["cans"]
        return 0
    
    def get_count(self, stream_id, object_type="cans"):
        """Get current count for specific stream"""
        with self.lock:
            stream_key = f"stream_{stream_id}"
            if stream_key in self.counts:
                return self.counts[stream_key].get(object_type, 0)
        return 0
    
    def get_all_counts(self):
        """Get all current counts"""
        with self.lock:
            return self.counts.copy()
    
    def reset_count(self, stream_id=None):
        """Reset counts for specific stream or all streams"""
        with self.lock:
            if stream_id is not None:
                stream_key = f"stream_{stream_id}"
                if stream_key in self.counts:
                    self.counts[stream_key]["cans"] = 0
                    self.counts[stream_key]["total_objects"] = 0
                    self.counts[stream_key]["last_updated"] = datetime.now().isoformat()
            else:
                for stream_key in self.counts:
                    self.counts[stream_key]["cans"] = 0
                    self.counts[stream_key]["total_objects"] = 0
                    self.counts[stream_key]["last_updated"] = datetime.now().isoformat()
            self.save_counts()
    
    def print_current_counts(self):
        """Print current counts in a formatted way"""
        print("\n" + "="*50)
        print("📊 CURRENT OBJECT COUNTS")
        print("="*50)
        for stream_key, data in self.counts.items():
            stream_num = stream_key.split('_')[1]
            print(f"Stream {stream_num}: {data['cans']} cans | {data['total_objects']} total")
            if data['last_updated']:
                last_update = datetime.fromisoformat(data['last_updated'])
                print(f"           Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50 + "\n")
    
    def generate_mqtt_payload(self, stream_id):
        """Generate MQTT payload for specific stream"""
        stream_key = f"stream_{stream_id}"
        if stream_key in self.counts:
            return {
                "timestamp": datetime.now().isoformat(),
                "stream_id": stream_id,
                "can_count": self.counts[stream_key]["cans"],
                "total_objects": self.counts[stream_key]["total_objects"],
                "last_updated": self.counts[stream_key]["last_updated"]
            }
        return None

# Global instance for use across the application
counter = ObjectCounter()

if __name__ == "__main__":
    # Test the counter
    print("🧪 Testing Object Counter...")
    
    # Simulate some counts
    counter.increment_count(0, "can")
    counter.increment_count(0, "can")
    counter.increment_count(1, "can")
    counter.increment_count(2, "bottle")
    
    counter.print_current_counts()
    
    # Test MQTT payload generation
    payload = counter.generate_mqtt_payload(0)
    print(f"📡 MQTT Payload for Stream 0: {json.dumps(payload, indent=2)}")
