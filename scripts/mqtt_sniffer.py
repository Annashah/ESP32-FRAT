#!/usr/bin/env python3
"""
mqtt_sniffer.py - MQTT Traffic Capture and Analysis
Requires: paho-mqtt, scapy (pip install paho-mqtt scapy)
"""

import paho.mqtt.client as mqtt
import json
import argparse
from datetime import datetime
from collections import defaultdict

class MQTTSniffer:
    def __init__(self, broker_ip, broker_port=1883, output_file=None):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.output_file = output_file
        self.topics_seen = defaultdict(int)
        self.payloads = []
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[+] Connected to broker {self.broker_ip}:{self.broker_port}")
            # Subscribe to all topics
            client.subscribe("#")
        else:
            print(f"[-] Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        timestamp = datetime.now().isoformat()
        self.topics_seen[msg.topic] += 1
        
        try:
            payload = msg.payload.decode('utf-8')
        except:
            payload = repr(msg.payload)
        
        record = {
            'timestamp': timestamp,
            'topic': msg.topic,
            'qos': msg.qos,
            'retain': msg.retain,
            'payload': payload
        }
        
        self.payloads.append(record)
        
        # Print to console
        print(f"[{timestamp}] Topic: {msg.topic}")
        print(f"    Payload: {payload[:100]}...")
        print()
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[-] Unexpected disconnection: {rc}")
    
    def start(self):
        """Connect and start sniffing"""
        try:
            print(f"[*] Connecting to {self.broker_ip}...")
            self.client.connect(self.broker_ip, self.broker_port, keepalive=60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n[*] Stopping sniffer...")
            self.save_results()
            self.client.disconnect()
        except Exception as e:
            print(f"[-] Error: {e}")
    
    def save_results(self):
        """Save captured data to JSON"""
        if not self.output_file:
            return
        
        output_data = {
            'capture_info': {
                'broker': self.broker_ip,
                'port': self.broker_port,
                'timestamp': datetime.now().isoformat(),
                'total_messages': len(self.payloads),
                'unique_topics': len(self.topics_seen)
            },
            'topic_summary': dict(self.topics_seen),
            'messages': self.payloads
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"[+] Results saved to {self.output_file}")

def main():
    parser = argparse.ArgumentParser(description="MQTT Traffic Sniffer")
    parser.add_argument("--broker-ip", required=True, help="MQTT broker IP address")
    parser.add_argument("--broker-port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    sniffer = MQTTSniffer(args.broker_ip, args.broker_port, args.output)
    sniffer.start()

if __name__ == "__main__":
    main()
