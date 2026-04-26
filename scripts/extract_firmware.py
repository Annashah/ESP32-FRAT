#!/usr/bin/env python3
"""
extract_firmware.py - Automated ESP8266/ESP32 Firmware Extraction
Requires: esptool (pip install esptool)
"""

import subprocess
import argparse
import os
import sys
from pathlib import Path

def extract_firmware(port, baud, output_file):
    """Extract firmware from ESP8266/ESP32 via UART"""
    
    print(f"[*] Extracting firmware from {port} at {baud} baud...")
    print(f"[*] Output: {output_file}")
    
    cmd = [
        "esptool.py",
        "--chip", "esp8266",
        "--port", port,
        "--baud", str(baud),
        "--before", "default_reset",
        "--after", "hard_reset",
        "read_flash",
        "0x00000",  # Start address
        "detect",   # Auto-detect size
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[+] Firmware extraction successful")
        print(f"[*] File size: {os.path.getsize(output_file)} bytes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Extraction failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[-] esptool.py not found. Install with: pip install esptool")
        return False

def extract_strings(firmware_file, output_file):
    """Extract printable strings from firmware binary"""
    print(f"\n[*] Extracting strings from {firmware_file}...")
    
    strings = []
    with open(firmware_file, 'rb') as f:
        data = f.read()
    
    current_string = b''
    for byte in data:
        if 32 <= byte <= 126:  # Printable ASCII
            current_string += bytes([byte])
        else:
            if len(current_string) >= 4:  # Minimum string length
                strings.append(current_string.decode('ascii', errors='ignore'))
            current_string = b''
    
    with open(output_file, 'w') as f:
        for s in strings:
            f.write(s + '\n')
    
    print(f"[+] Extracted {len(strings)} strings")
    print(f"[*] Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="ESP8266/ESP32 Firmware Extraction Tool")
    parser.add_argument("--port", required=True, help="Serial port (e.g., /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--output", required=True, help="Output firmware filename")
    parser.add_argument("--extract-strings", action="store_true", help="Extract strings after dump")
    
    args = parser.parse_args()
    
    # Extract firmware
    if not extract_firmware(args.port, args.baud, args.output):
        sys.exit(1)
    
    # Extract strings if requested
    if args.extract_strings:
        strings_file = args.output.replace('.bin', '_strings.txt')
        extract_strings(args.output, strings_file)

if __name__ == "__main__":
    main()
