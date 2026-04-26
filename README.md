# ESP32-FRAT: Firmware Reverse Engineering & Attack Toolkit

A comprehensive cybersecurity project combining hardware exploitation, firmware reverse engineering, and network security analysis targeting IoT devices (ESP8266/ESP32).

## Overview

ESP32-FRAT demonstrates a methodical approach to identifying and exploiting firmware vulnerabilities in constrained embedded systems. This project combines physical firmware extraction, static binary analysis, and live traffic interception to uncover six distinct vulnerability classes in a deliberately vulnerable IoT firmware.

**Target Device:** ESP8266 NodeMCU v0.1  
**Vulnerability Classes Identified:** 6 (hardcoded credentials, unauthenticated endpoints, buffer overflow, info exposure, no TLS enforcement, MQTT injection)

---

## Project Scope

### Phases

1. **Physical Extraction** — UART firmware dump via esptool.py
2. **Static Analysis** — Ghidra binary disassembly with Xtensa LX106 processor module
3. **Dynamic Analysis** — Live MQTT traffic capture and protocol mapping
4. **Exploitation** — Proof-of-concept payload delivery and device compromise
5. **Documentation** — CVE-style vulnerability reports

### Vulnerabilities Documented

| ID | Type | Severity | Impact |
|---|---|---|---|
| ESP32-FRAT-001 | Hardcoded Credentials | Critical | Admin access via plaintext stored password |
| ESP32-FRAT-002 | Unauthenticated Admin Endpoint | Critical | Remote configuration without authentication |
| ESP32-FRAT-003 | Buffer Overflow (strcpy) | High | Memory corruption via oversized MQTT payload |
| ESP32-FRAT-004 | Info Exposure | High | Firmware strings leak internal API endpoints |
| ESP32-FRAT-005 | No TLS Enforcement | High | Unencrypted credential transmission |
| ESP32-FRAT-006 | MQTT Injection | Medium | Malicious payload delivery via unfiltered input |

---

## Tools & Environment

### Hardware
- ESP8266 NodeMCU v0.1
- ESP-01 WiFi module
- USB UART adapter (CH340/FTDI)

### Software
- **Firmware Extraction:** esptool.py, Binwalk
- **Binary Analysis:** Ghidra 11.x (Xtensa LX106 processor module)
- **Traffic Analysis:** Wireshark, Scapy, tcpdump
- **Exploit Development:** Python 3.8+, Paho MQTT
- **Environment:** Kali Linux 2024.x on VMware (Bridged networking)
- **Broker:** Mosquitto MQTT

---

## Quick Start

### Prerequisites
```bash
pip install esptool paho-mqtt scapy wireshark-python binwalk
# Install Ghidra 11.x separately from ghidra-sre.org
# Kali Linux with vmware-tools (USB passthrough required)
```

### Firmware Extraction
```bash
python3 scripts/extract_firmware.py --port /dev/ttyUSB0 --baud 115200 --output firmware.bin
```

### Static Analysis
1. Open `firmware.bin` in Ghidra
2. Load Xtensa LX106 processor module
3. Auto-analyze at entry point 0x40200000
4. Review annotated functions in `analysis/ghidra_exports/`

### Traffic Capture
```bash
python3 scripts/mqtt_sniffer.py --interface eth0 --broker-ip 192.168.x.x --output traffic.pcap
```

### Exploit Testing
```bash
python3 scripts/poc_hardcoded_creds.py --target 192.168.x.x --username admin --password password123
```

---

## Directory Structure

```
ESP32-FRAT/
├── firmware/                    # Extracted and compiled firmware
│   ├── esp8266_original.bin    # Raw firmware dump
│   ├── Ghidra/                 # Binary analysis project
│   └── strings_analysis.txt    # Extracted firmware strings
├── analysis/                   # Static & dynamic analysis results
│   ├── ghidra_exports/         # Function exports, cross-references
│   ├── vulnerability_summary/  # Per-vulnerability breakdown
│   └── traffic_pcaps/          # Wireshark captures
├── scripts/                    # Working Python utilities
│   ├── extract_firmware.py     # Automated UART dump
│   ├── mqtt_sniffer.py         # MQTT traffic capture
│   ├── poc_*.py                # Proof-of-concept exploits
│   └── utils.py                # Helper functions (CRC, checksum)
├── tools/                      # Configuration & reference files
│   ├── mqtt_topics.json        # Device MQTT topic mapping
│   ├── ghidra_scripts/         # Ghidra automation scripts
│   └── wireshark_filters.txt   # Pre-built Wireshark filter rules
├── docs/report/                # CVE-style vulnerability reports
│   ├── ESP32-FRAT-001.md       # Hardcoded credentials report
│   ├── ESP32-FRAT-002.md       # Unauthenticated endpoint report
│   └── ...
└── README.md                   # This file
```

---

## Key Findings

### ESP32-FRAT-001: Hardcoded Credentials
**Severity:** Critical | **CWE-798**

Firmware contains plaintext admin password stored in binary:
```
String @ 0x402001FC: "admin_password=password123"
```
**Impact:** Unauthenticated remote administrative access  
**Remediation:** Implement secure credential storage (NVS encryption, HMAC verification)

### ESP32-FRAT-002: Unauthenticated Admin Endpoint
**Severity:** Critical | **CWE-306**

HTTP endpoint `/api/admin/config` accepts POST without authentication check:
```
GET /api/admin/config HTTP/1.1
Response: 200 OK + full device configuration (SSID, WiFi password, API keys)
```
**Impact:** Information disclosure + configuration tampering  
**Remediation:** Implement token-based auth (JWT) with per-endpoint ACL

### ESP32-FRAT-003: Buffer Overflow (strcpy)
**Severity:** High | **CWE-120**

MQTT message handler uses unsafe strcpy without bounds checking:
```c
// @ 0x40203450 in firmware
strcpy(device_name, mqtt_payload);  // No length validation
```
**Impact:** Memory corruption, potential code execution  
**Remediation:** Replace strcpy with strncpy, add input validation

---

## Reproduction Steps

### Step 1: Extract Firmware
```bash
esptool.py --chip esp8266 --port /dev/ttyUSB0 read_flash 0 detect firmware.bin
```

### Step 2: Analyze in Ghidra
- Import firmware.bin as binary
- Set base address: 0x40200000 (ESP8266 code region)
- Apply Xtensa LX106 processor specification
- Auto-analyze

### Step 3: Identify Vulnerable Patterns
Search Ghidra for:
- `strcpy` / `strncpy` calls (buffer overflow)
- Plaintext string comparisons (hardcoded creds)
- HTTP handlers without auth checks (authz bypass)

### Step 4: Capture Live Traffic
```bash
tcpdump -i eth0 -n "tcp port 1883 or tcp port 80" -w traffic.pcap
mosquitto_sub -h 192.168.x.x -t "#" | tee mqtt_topics.log
```

### Step 5: Exploit
```bash
python3 scripts/poc_hardcoded_creds.py --target 192.168.x.x
# Output: Successfully authenticated as 'admin'
```

---

## Methodology

This project follows a structured vulnerability research workflow:

1. **Asset Identification** — Physical device, firmware location
2. **Acquisition** — Non-invasive extraction via serial interface
3. **Disassembly** — Static binary analysis with architecture-specific tools
4. **Behavior Mapping** — Live traffic analysis to correlate code with network behavior
5. **Vulnerability Identification** — CWE classification and impact assessment
6. **Exploitation** — Proof-of-concept development
7. **Documentation** — CVE-style reporting for responsible disclosure

---

## Tools Reference

### Ghidra (Binary Analysis)
- **Processor Module:** Xtensa LX106 (available in Ghidra marketplace)
- **Base Address:** 0x40200000 (ESP8266 instruction RAM)
- **Key Shortcuts:**
  - `G` — Go to address
  - `F` — Create function at cursor
  - `D` — Define data type
  - `X` — Show cross-references (who calls this function)

### Wireshark (Traffic Analysis)
- **MQTT Filter:** `mqtt` (show all MQTT traffic)
- **TCP Filter:** `tcp.port == 1883` (standard MQTT port)
- **Follow Stream:** Right-click packet → Follow → TCP Stream

### Scapy (Packet Crafting)
```python
from scapy.all import *
# Craft custom MQTT CONNECT packet
pkt = IP(dst="192.168.x.x")/TCP(dport=1883)/Raw(load=mqtt_payload)
send(pkt)
```

---

## Files Generated During Analysis

| File | Purpose |
|---|---|
| `firmware.bin` | Raw ESP8266 firmware dump |
| `firmware.elf` | Extracted ELF with symbols (if available) |
| `strings.txt` | All printable strings from binary |
| `traffic.pcap` | Wireshark packet capture |
| `mqtt_topics.json` | Device MQTT topic mapping |
| `ghidra_exports.xml` | Function exports for cross-reference |

---

## Limitations & Scope

**This Project:**
- ✓ Demonstrates firmware extraction from ESP8266
- ✓ Shows static analysis workflow with Ghidra
- ✓ Documents real vulnerability patterns
- ✓ Provides POC exploits for educational purposes

**This Project Does NOT:**
- ✗ Provide a weaponized attack toolkit
- ✗ Target production systems without explicit authorization
- ✗ Include zero-days or undisclosed vulnerabilities
- ✗ Provide bypass techniques for modern IoT security (e.g., TPM, secure boot)

---

## Educational Use

This project is designed for:
- Security researchers learning firmware analysis
- Ethical hackers practicing IoT penetration testing
- Academic study of embedded system vulnerabilities
- Responsible disclosure training

**Legal Note:** Do not use this toolkit on systems you do not own or have explicit written permission to test.

---

## Further Reading

- [OWASP IoT Security](https://owasp.org/www-project-iot-security/)
- [Ghidra User Guide](https://ghidra-sre.org/)
- [ESP8266 Technical Reference](https://www.espressif.com/sites/default/files/documentation/esp8266-technical_reference_en.pdf)
- [CWE-120: Buffer Overflow](https://cwe.mitre.org/data/definitions/120.html)
- [Wireshark MQTT Dissector](https://wiki.wireshark.org/MQTT)

---

## Author

Amna Shabir  
B.S. Information Technology, Shaheed Benazir Bhutto University  
Portfolio: https://annashah.github.io/portfolio/

---

## License

This project is provided for educational and authorized security research purposes only. Unauthorized access to computer systems is illegal.
