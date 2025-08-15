#!/usr/bin/env python3
"""
Fixed System Monitor - Ensures presence field is properly sent
"""

import json
import time
import threading
import paho.mqtt.client as mqtt
from datetime import datetime
import random

class FixedSystemMonitor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.received_data = {}
        self.counter = 0
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ Connected to MQTT broker (code: {rc})")
        
        # Subscribe to all relevant topics
        topics = [
            "home/sensors/+/motion",
            "home/status/+",
            "home/diagnostic/+",
            "home/events/+",
            "home/alerts/+"
        ]
        
        for topic in topics:
            client.subscribe(topic)
            print(f"📡 Subscribed to: {topic}")
    
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Store data
            self.received_data[topic] = {
                "payload": payload,
                "timestamp": timestamp
            }
            
            # Display sensor data
            if "sensors" in topic:
                self.display_sensor_data(topic, payload, timestamp)
                
        except Exception as e:
            print(f"❌ Error parsing message from {topic}: {e}")
    
    def display_sensor_data(self, topic, data, timestamp):
        room = data.get('room', 'Unknown')
        presence = data.get('presence', False)
        movement = data.get('movement', 'none')
        signal = data.get('signal_strength', 0)
        
        presence_icon = "👤" if presence else "🚫"
        movement_icon = "🚶" if movement != "none" else "⏸️"
        
        print(f"📊 [{timestamp}] SENSOR: {room} {presence_icon} Presence={presence} {movement_icon} Movement={movement} Signal={signal:.2f}")
    
    def send_enhanced_test_data(self):
        """Send test data with guaranteed presence field"""
        while True:
            self.counter += 1
            
            # Send data for all rooms
            rooms = ["Room", "Hall", "Kitchen"]
            
            for room in rooms:
                # Ensure presence is explicitly boolean
                presence_bool = bool(self.counter % 3 != 0)  # Explicitly convert to boolean
                
                # Create enhanced data with all required fields
                data = {
                    "room": str(room),  # Ensure string
                    "timestamp": int(time.time() * 1000),
                    "sensor_type": "c1001_enhanced",
                    "presence": presence_bool,  # Explicit boolean
                    "movement": random.choice(["walking", "sitting", "standing", "none"]),
                    "signal_strength": round(random.uniform(0.1, 0.9), 2),
                    "test_counter": self.counter,
                    "test_mode": True,
                    "uptime": self.counter * 5,
                    "raw_data": f"DATA_{self.counter}_{room}"
                }
                
                # Send to MQTT
                topic = f"home/sensors/{room}/motion"
                payload = json.dumps(data)
                
                try:
                    result = self.client.publish(topic, payload)
                    if result.rc == 0:
                        status = "👤" if presence_bool else "🚫"
                        print(f"{status} {room}: presence={presence_bool} | movement={data['movement']} | signal={data['signal_strength']}")
                    else:
                        print(f"❌ Failed to send {room} data")
                except Exception as e:
                    print(f"❌ MQTT publish error: {e}")
                
                time.sleep(0.5)
            
            print(f"--- Round {self.counter} completed ---")
            time.sleep(4)  # 4 seconds between rounds
    
    def show_summary(self):
        """Show periodic summary"""
        while True:
            time.sleep(30)
            print("\n" + "="*60)
            print(f"📈 SYSTEM SUMMARY - {datetime.now().strftime('%H:%M:%S')}")
            print("="*60)
            
            # Show latest sensor data
            sensor_count = 0
            for topic, info in self.received_data.items():
                if 'sensors' in topic:
                    sensor_count += 1
                    data = info['payload']
                    room = data.get('room', 'Unknown')
                    presence = "YES" if data.get('presence') else "NO"
                    movement = data.get('movement', 'none')
                    print(f"   {room}: Presence={presence}, Movement={movement}")
            
            print(f"🏠 Active Rooms: {sensor_count}")
            print(f"📡 Data Counter: {self.counter}")
            print("="*60 + "\n")
    
    def run(self):
        print("🚀 Starting Enhanced System Monitor...")
        print("This will send data with guaranteed presence field")
        print("Press Ctrl+C to stop\n")
        
        try:
            # Connect to MQTT (adjust IP if needed)
            self.client.connect("localhost", 1883, 60)  # Changed to localhost
            self.client.loop_start()
            
            # Start background threads
            summary_thread = threading.Thread(target=self.show_summary, daemon=True)
            summary_thread.start()
            
            # Start enhanced data sending
            data_thread = threading.Thread(target=self.send_enhanced_test_data, daemon=True)
            data_thread.start()
            
            print("👀 Monitoring and sending enhanced MQTT data...")
            print("-" * 60)
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping enhanced system monitor...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("✅ Enhanced system monitor stopped")

if __name__ == "__main__":
    monitor = FixedSystemMonitor()
    monitor.run()