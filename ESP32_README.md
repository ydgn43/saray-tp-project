# ESP32 Integration Guide

## Overview
Each ESP32 device monitors supplies in a specific room and reports status updates to the server.

## Room ID System
When you create a room in the dashboard, a unique **Room ID** (e.g., `A1B2C3D4`) is generated. This ID must be configured in your ESP32 code.

## ESP32 Code Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* serverUrl = "http://192.168.50.68:5000/report";

// Room ID (Get this from the dashboard after creating a room)
const char* roomId = "A1B2C3D4";  // Replace with your actual room ID

// Sensor pins
const int TOILET_PAPER_PIN = 34;
const int SOAP_PIN = 35;
const int TOWEL_PIN = 32;
const int TRASH_PIN = 33;

void setup() {
  Serial.begin(115200);
  
  // Setup sensor pins
  pinMode(TOILET_PAPER_PIN, INPUT);
  pinMode(SOAP_PIN, INPUT);
  pinMode(TOWEL_PIN, INPUT);
  pinMode(TRASH_PIN, INPUT);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  // Read sensors
  checkSupply("toilet_paper", digitalRead(TOILET_PAPER_PIN));
  checkSupply("soap", digitalRead(SOAP_PIN));
  checkSupply("towel", digitalRead(TOWEL_PIN));
  checkSupply("trash", digitalRead(TRASH_PIN));
  
  delay(60000);  // Check every minute
}

void checkSupply(const char* item, int sensorValue) {
  String status;
  
  // Determine status based on sensor reading
  // Adjust logic based on your sensor type
  if (sensorValue == HIGH) {
    status = "empty";
  } else {
    status = "full";
  }
  
  sendStatus(item, status);
}

void sendStatus(const char* item, String status) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    String payload = "{";
    payload += "\"room_id\":\"" + String(roomId) + "\",";
    payload += "\"item\":\"" + String(item) + "\",";
    payload += "\"status\":\"" + status + "\"";
    payload += "}";
    
    int httpCode = http.POST(payload);
    
    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Status sent: " + String(item) + " - " + status);
      Serial.println("Response: " + response);
    } else {
      Serial.println("Error sending status");
    }
    
    http.end();
  }
}
```

## API Endpoints for ESP32

### 1. Report Supply Status
**POST** `/report`

```json
{
  "room_id": "A1B2C3D4",
  "item": "toilet_paper",
  "status": "empty"
}
```

**Item types:**
- `toilet_paper`
- `soap`
- `towel`
- `trash`

**Status values:**
- `full` - Supply is full
- `low` - Supply is running low (optional)
- `empty` - Supply is empty

**Response:**
```json
{
  "ok": true,
  "room": "Main Floor Restroom"
}
```

### 2. Verify Room ID
**GET** `/room/{room_id}`

Example: `GET /room/A1B2C3D4`

**Response:**
```json
{
  "id": "A1B2C3D4",
  "name": "Main Floor Restroom",
  "type": "restroom",
  "location": "1st Floor",
  "supplies": {...}
}
```

## Setup Steps

1. **Create a Room** in the dashboard
2. **Copy the Room ID** from the room settings
3. **Configure your ESP32** with the Room ID
4. **Upload the code** to your ESP32
5. **Monitor** the dashboard for real-time updates

## Testing

You can test the API using curl:

```bash
curl -X POST http://192.168.50.68:5000/report \
  -H "Content-Type: application/json" \
  -d '{"room_id":"A1B2C3D4","item":"toilet_paper","status":"empty"}'
```

## Troubleshooting

- **Invalid room_id error**: Make sure the Room ID in your ESP32 code matches the ID in the dashboard
- **Connection issues**: Check that ESP32 and server are on the same network
- **No updates**: Verify the server URL and port are correct
