// ============================================================
// ESP32-FRAT Project — Vulnerable IoT Node Firmware
// Target board: NodeMCU v0.1 (ESP8266)
// INTENTIONAL FLAWS: documented below for RE analysis
//
// FLAW-01: Hardcoded WiFi credentials (plaintext in binary)
// FLAW-02: Hardcoded MQTT credentials (plaintext in binary)
// FLAW-03: No TLS — all MQTT traffic in plaintext over port 1883
// FLAW-04: Unauthenticated /admin HTTP endpoint
// FLAW-05: Unsafe strcpy() — buffer overflow in /cmd handler
// FLAW-06: Device info exposed on /info without auth
// ============================================================

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ESP8266WebServer.h>
#include <string.h>

// ----------------------------------------------------------
// FLAW-01: Hardcoded WiFi credentials
// These strings are stored in plaintext in the binary.
// esptool dump + strings command will reveal them instantly.
// ----------------------------------------------------------
const char* WIFI_SSID     = "HomeNetwork_2G";
const char* WIFI_PASSWORD = "supersecret123";

// ----------------------------------------------------------
// FLAW-02: Hardcoded MQTT credentials
// Same issue — visible in firmware dump.
// ----------------------------------------------------------
const char* MQTT_BROKER   = "192.168.1.100";  // your Kali IP
const int   MQTT_PORT     = 1883;             // no TLS
const char* MQTT_USER     = "iotdevice";
const char* MQTT_PASS     = "mqtt_pass_2024"; // FLAW-02
const char* MQTT_CLIENT   = "smart_lock_node_01";
const char* MQTT_TOPIC    = "home/lock/status";
const char* MQTT_CMD      = "home/lock/cmd";

WiFiClient   espClient;
PubSubClient mqttClient(espClient);
ESP8266WebServer httpServer(80);

// ----------------------------------------------------------
// FLAW-05: Fixed-size buffer — vulnerable to overflow
// An attacker sending >63 chars to /cmd will corrupt memory
// ----------------------------------------------------------
char cmdBuffer[64];

// Forward declarations
void connectWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void handleRoot();
void handleInfo();
void handleAdmin();
void handleCmd();
void handleNotFound();

// ----------------------------------------------------------
// SETUP
// ----------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\n[BOOT] Vulnerable IoT Node v1.0");
  Serial.println("[BOOT] FRAT Research Device");

  connectWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // HTTP routes
  httpServer.on("/",       handleRoot);
  httpServer.on("/info",   handleInfo);    // FLAW-06: exposes device info
  httpServer.on("/admin",  handleAdmin);   // FLAW-04: no auth check
  httpServer.on("/cmd",    HTTP_POST, handleCmd); // FLAW-05: strcpy overflow
  httpServer.onNotFound(handleNotFound);

  httpServer.begin();
  Serial.println("[HTTP] Web server started on port 80");
}

// ----------------------------------------------------------
// LOOP
// ----------------------------------------------------------
void loop() {
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();
  httpServer.handleClient();

  // Publish fake sensor data every 5 seconds
  static unsigned long lastMsg = 0;
  if (millis() - lastMsg > 5000) {
    lastMsg = millis();
    String payload = "{\"device\":\"" + String(MQTT_CLIENT) +
                     "\",\"status\":\"locked\",\"uptime\":" +
                     String(millis()/1000) + "}";
    // FLAW-03: published over plaintext port 1883 — no TLS
    mqttClient.publish(MQTT_TOPIC, payload.c_str());
    Serial.println("[MQTT] Published: " + payload);
  }
}

// ----------------------------------------------------------
// WiFi connection
// ----------------------------------------------------------
void connectWiFi() {
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);  // FLAW-01: prints creds to serial
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("[WiFi] Connected! IP: ");
  Serial.println(WiFi.localIP());
}

// ----------------------------------------------------------
// MQTT connection
// ----------------------------------------------------------
void connectMQTT() {
  Serial.print("[MQTT] Connecting to broker: ");
  Serial.println(MQTT_BROKER);
  // FLAW-02: credentials sent in plaintext CONNECT packet
  if (mqttClient.connect(MQTT_CLIENT, MQTT_USER, MQTT_PASS)) {
    Serial.println("[MQTT] Connected!");
    mqttClient.subscribe(MQTT_CMD);
  } else {
    Serial.print("[MQTT] Failed, rc=");
    Serial.println(mqttClient.state());
  }
}

// ----------------------------------------------------------
// MQTT message callback
// ----------------------------------------------------------
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  Serial.println("[MQTT] Command received: " + msg);

  if (msg == "unlock") {
    Serial.println("[ACTION] Lock OPENED via MQTT command!");
    mqttClient.publish(MQTT_TOPIC, "{\"status\":\"unlocked\"}");
  } else if (msg == "lock") {
    Serial.println("[ACTION] Lock CLOSED via MQTT command!");
    mqttClient.publish(MQTT_TOPIC, "{\"status\":\"locked\"}");
  }
}

// ----------------------------------------------------------
// HTTP: root
// ----------------------------------------------------------
void handleRoot() {
  httpServer.send(200, "text/html",
    "<h2>IoT Smart Lock Node</h2>"
    "<p>Device: smart_lock_node_01</p>"
    "<p><a href='/info'>Device Info</a> | "
    "<a href='/admin'>Admin Panel</a></p>"
  );
}

// ----------------------------------------------------------
// HTTP: /info — FLAW-06: exposes sensitive device details
// No authentication required to view WiFi SSID, IP, firmware
// ----------------------------------------------------------
void handleInfo() {
  String json = "{";
  json += "\"device\":\"" + String(MQTT_CLIENT) + "\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"ssid\":\"" + String(WIFI_SSID) + "\",";   // FLAW-06
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"uptime\":" + String(millis()/1000) + ",";
  json += "\"firmware\":\"v1.0-vulnerable\"";
  json += "}";
  httpServer.send(200, "application/json", json);
}

// ----------------------------------------------------------
// HTTP: /admin — FLAW-04: no authentication whatsoever
// Any device on the network can send admin commands
// ----------------------------------------------------------
void handleAdmin() {
  String action = httpServer.arg("action");
  String response = "<h2>Admin Panel — Full Control</h2>";

  if (action == "reset") {
    response += "<p>Device rebooting...</p>";
    httpServer.send(200, "text/html", response);
    delay(500);
    ESP.restart();
  } else if (action == "unlock") {
    mqttClient.publish(MQTT_TOPIC, "{\"status\":\"unlocked\",\"source\":\"admin\"}");
    response += "<p>Lock forced OPEN via admin override.</p>";
  } else {
    response += "<p>Available actions: "
                "<a href='/admin?action=unlock'>Force Unlock</a> | "
                "<a href='/admin?action=reset'>Reboot Device</a></p>";
    response += "<p>MQTT broker: " + String(MQTT_BROKER) + "</p>";
    response += "<p>MQTT user: " + String(MQTT_USER) + "</p>";  // exposes creds
  }
  httpServer.send(200, "text/html", response);
}

// ----------------------------------------------------------
// HTTP: /cmd — FLAW-05: buffer overflow via strcpy
// cmdBuffer is only 64 bytes. Sending >63 chars corrupts stack.
// In a real exploit this overwrites the return address.
// ----------------------------------------------------------
void handleCmd() {
  String cmdArg = httpServer.arg("c");

  // VULNERABLE: no length check before copy
  strcpy(cmdBuffer, cmdArg.c_str());  // FLAW-05

  Serial.println("[CMD] Executing: " + String(cmdBuffer));
  httpServer.send(200, "text/plain", "CMD executed: " + String(cmdBuffer));
}

// ----------------------------------------------------------
// HTTP: 404
// ----------------------------------------------------------
void handleNotFound() {
  httpServer.send(404, "text/plain", "404 Not Found");
}
