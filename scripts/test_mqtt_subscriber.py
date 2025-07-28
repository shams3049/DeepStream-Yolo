#!/usr/bin/env python3

"""
MQTT Subscriber Test - Monitor all production topics
Tests what messages are being received from the external MQTT broker
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time

class MQTTSubscriberTest:
    def __init__(self):
        self.broker_host = "mqtt-proxy.ad.dicodrink.com"
        self.broker_port = 1883
        self.username = "r_vmays"
        self.password = "csYr9xH&WTfAvMj2"
        self.client_id = "deepstream-test-subscriber"
        
        # Topics to monitor
        self.topics = [
            "camera1",
            "camera2", 
            "camera3",
            "camera4",
            "deepstream/health",
            "+",  # Wildcard for all topics
        ]
        
        self.message_count = {}
        self.client = None
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print("✅ Connected to MQTT broker for testing")
            print(f"📡 {self.broker_host}:{self.broker_port}")
            print("🔍 Subscribing to production topics...")
            print()
            
            # Subscribe to all production topics
            for topic in self.topics:
                result = client.subscribe(topic, qos=0)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    print(f"✅ Subscribed to: {topic}")
                else:
                    print(f"❌ Failed to subscribe to: {topic}")
            
            print("\n🎧 Listening for messages...")
            print("=" * 60)
            
        else:
            print(f"❌ Failed to connect: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Count messages per topic
            if topic not in self.message_count:
                self.message_count[topic] = 0
            self.message_count[topic] += 1
            
            print(f"📨 [{timestamp}] Topic: {topic}")
            print(f"    Message #{self.message_count[topic]}")
            
            # Try to parse JSON payload
            try:
                data = json.loads(payload)
                print(f"    📊 Parsed JSON:")
                
                # Display key fields based on message type
                if 'message_type' in data:
                    msg_type = data.get('message_type')
                    
                    if msg_type == 'count_update':
                        print(f"       🏭 Camera: {data.get('camera_name', 'Unknown')}")
                        print(f"       📦 Can Count: {data.get('can_count', 0)}")
                        print(f"       📋 Total Objects: {data.get('total_objects', 0)}")
                        print(f"       📍 Location: {data.get('location', 'Unknown')}")
                        
                    elif msg_type == 'health_status':
                        print(f"       💚 Status: {data.get('system_status', 'unknown')}")
                        print(f"       🖥️  CPU: {data.get('cpu_usage', 'N/A')}")
                        print(f"       💾 Memory: {data.get('memory_usage', 'N/A')}")
                        print(f"       🎮 GPU: {data.get('gpu_info', 'N/A')}")
                        print(f"       📦 Total Cans: {data.get('total_cans_detected', 0)}")
                
                # Show timestamp
                if 'timestamp' in data:
                    print(f"       ⏰ Timestamp: {data['timestamp']}")
                
            except json.JSONDecodeError:
                print(f"    📝 Raw payload: {payload}")
            
            print("    " + "-" * 50)
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        print(f"\n📡 Disconnected from MQTT broker")
    
    def start_monitoring(self):
        """Start monitoring MQTT messages"""
        try:
            print("🔍 MQTT MESSAGE MONITORING TEST")
            print("=" * 40)
            print(f"📡 Broker: {self.broker_host}:{self.broker_port}")
            print(f"🔐 Username: {self.username}")
            print(f"🆔 Client ID: {self.client_id}")
            print()
            
            # Create MQTT client
            self.client = mqtt.Client(client_id=self.client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
            self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Connect and start loop
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping message monitoring...")
            self.show_statistics()
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            if self.client:
                self.client.disconnect()
    
    def show_statistics(self):
        """Show message statistics"""
        print("\n📊 MESSAGE STATISTICS")
        print("=" * 30)
        
        if self.message_count:
            total_messages = sum(self.message_count.values())
            print(f"📈 Total Messages Received: {total_messages}")
            print("\n📋 Messages per Topic:")
            
            for topic, count in self.message_count.items():
                print(f"   {topic}: {count} messages")
        else:
            print("📭 No messages received")

def main():
    """Main test function"""
    subscriber = MQTTSubscriberTest()
    subscriber.start_monitoring()

if __name__ == "__main__":
    main()
