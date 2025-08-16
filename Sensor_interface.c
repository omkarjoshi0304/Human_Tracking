
// Simple ESP32 Test - Sends both real sensor data and test data
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "SKYY578M";
const char* password = "ZL6tIj8bSNib";
const char* mqtt_server = "192.168.0.23";

WiFiClient espClient;
PubSubClient client(espClient);
HardwareSerial mmWave(2);

String roomID = "Kitchen"; // Change to "Hall" for second sensor

unsigned long lastTestData = 0;
unsigned long lastSensorCheck = 0;
int testCounter = 0;

void setup() {
  Serial.begin(115200);
  mmWave.begin(115200, SERIAL_8N1, 17, 16);
  
  Serial.println("=== ESP32 Simple Test Mode ===");
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
  
  client.setServer(mqtt_server, 1883);
  reconnectMQTT();
  
  Serial.println("System ready - will send test data every 5 seconds");
  Serial.println("Also monitoring sensor for real data...");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Check for real sensor data
  if (millis() - lastSensorCheck > 100) {
    checkSensorData();
    lastSensorCheck = millis();
  }
  
  // Send test data every 5 seconds
  if (millis() - lastTestData > 5000) {
    sendTestData();
    lastTestData = millis();
  }
  
  delay(50);
}

void checkSensorData() {
  if (mmWave.available()) {
    String data = mmWave.readString();
    data.trim();
    
    if (data.length() > 0) {
      Serial.println("Real sensor data: " + data);
      
      // Send real sensor data
      StaticJsonDocument<300> doc;
      doc["room"] = roomID;
      doc["timestamp"] = millis();
      doc["sensor_type"] = "c1001_real";
      doc["raw_data"] = data;
      doc["data_length"] = data.length();
      
      // Simple parsing
      bool hasContent = (data.length() > 1 && data != "\0");
      doc["presence"] = hasContent;
      doc["movement"] = hasContent ? "detected" : "none";
      doc["signal_strength"] = hasContent ? 0.7 : 0.1;
      
      String payload;
      serializeJson(doc, payload);
      
      String topic = "home/sensors/" + roomID + "/motion";
      if (client.publish(topic.c_str(), payload.c_str())) {
        Serial.println("✅ Published real sensor data");
      }
    }
  }
}

void sendTestData() {
  testCounter++;
  
  // Simulate realistic human movement patterns
  bool presence = (testCounter % 3 != 0); // Present 66% of time
  String movements[] = {"walking", "sitting", "standing", "none"};
  String movement = presence ? movements[testCounter % 4] : "none";
  float signal = presence ? (0.4 + (testCounter % 50) / 100.0) : (0.0 + (testCounter % 20) / 100.0);
  
  StaticJsonDocument<300> doc;
  doc["room"] = roomID;
  doc["timestamp"] = millis();
  doc["sensor_type"] = "c1001_test";
  doc["presence"] = presence;
  doc["movement"] = movement;
  doc["signal_strength"] = signal;
  doc["test_counter"] = testCounter;
  doc["test_mode"] = true;
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "home/sensors/" + roomID + "/motion";
  
  if (client.publish(topic.c_str(), payload.c_str())) {
    Serial.println("📊 Test data #" + String(testCounter) + ": " + 
                  roomID + " presence=" + String(presence) + 
                  " movement=" + movement);
  } else {
    Serial.println("❌ Failed to publish test data");
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    
    String clientId = "ESP32-" + roomID + "-TEST-" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" connected!");
      
      // Publish startup message
      StaticJsonDocument<200> statusDoc;
      statusDoc["room"] = roomID;
      statusDoc["status"] = "online_test_mode";
      statusDoc["timestamp"] = millis();
      statusDoc["ip"] = WiFi.localIP().toString();
      
      String statusPayload;
      serializeJson(statusDoc, statusPayload);
      
      String statusTopic = "home/status/" + roomID;
      client.publish(statusTopic.c_str(), statusPayload.c_str(), true);
      
    } else {
      Serial.print(" failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}
