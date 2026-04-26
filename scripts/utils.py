#!/usr/bin/env python3
"""
utils.py - Helper functions for firmware analysis and exploitation
"""

import struct
import zlib

def calculate_crc32(data):
    """Calculate CRC32 checksum"""
    return zlib.crc32(data) & 0xffffffff

def calculate_esp_checksum(data):
    """Calculate ESP8266 firmware checksum"""
    checksum = 0xef
    for byte in data:
        checksum ^= byte
    return checksum

def find_pattern(firmware_data, pattern):
    """Find byte pattern in firmware"""
    matches = []
    for i in range(len(firmware_data) - len(pattern)):
        if firmware_data[i:i+len(pattern)] == pattern:
            matches.append(i)
    return matches

def extract_strings(firmware_data, min_length=4):
    """Extract printable ASCII strings from binary"""
    strings = []
    current_string = b''
    
    for byte in firmware_data:
        if 32 <= byte <= 126:  # Printable ASCII
            current_string += bytes([byte])
        else:
            if len(current_string) >= min_length:
                try:
                    strings.append(current_string.decode('ascii'))
                except:
                    pass
            current_string = b''
    
    return strings

def find_xrefs(firmware_data, address):
    """Find cross-references to address in firmware"""
    # Search for 32-bit and 16-bit references
    xrefs = []
    addr_bytes_le = struct.pack('<I', address)  # Little-endian
    addr_bytes_be = struct.pack('>I', address)  # Big-endian
    
    # Search for little-endian references
    xrefs.extend(find_pattern(firmware_data, addr_bytes_le))
    
    return xrefs

def hex_dump(data, start_address=0, width=16):
    """Generate hex dump of binary data"""
    output = []
    for i in range(0, len(data), width):
        addr = start_address + i
        hex_bytes = ' '.join(f'{b:02x}' for b in data[i:i+width])
        ascii_text = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+width])
        output.append(f'{addr:08x}  {hex_bytes:<{width*3}}  {ascii_text}')
    
    return '\n'.join(output)

def parse_mqtt_payload(payload_bytes):
    """Parse MQTT control packet"""
    if len(payload_bytes) < 2:
        return None
    
    # MQTT packet structure: [Control byte][Remaining length][Variable header][Payload]
    control_byte = payload_bytes[0]
    packet_type = (control_byte >> 4) & 0x0f
    
    packet_types = {
        1: "CONNECT",
        2: "CONNACK",
        3: "PUBLISH",
        4: "PUBACK",
        5: "PUBREC",
        6: "PUBREL",
        7: "PUBCOMP",
        8: "SUBSCRIBE",
        9: "SUBACK",
        10: "UNSUBSCRIBE",
        11: "UNSUBACK",
        12: "PINGREQ",
        13: "PINGRESP",
        14: "DISCONNECT"
    }
    
    return {
        'type': packet_types.get(packet_type, 'UNKNOWN'),
        'type_code': packet_type,
        'flags': control_byte & 0x0f
    }

if __name__ == "__main__":
    # Test functions
    print("[*] Utils module loaded. Use in your analysis scripts.")
