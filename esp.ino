#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// IP address of the server running the Node.js API
const char* serverUrl = "http://192.168.0.100:3000/arduino/temperature"; // Replace with your local IP

const int buttonAddPin = 12;
const int buttonSubPin = 14;

int temperature = 24;
unsigned long lastInputTime = 0;
bool inputChanged = false;

void setup() {
  Serial.begin(115200);

  pinMode(buttonAddPin, INPUT_PULLUP);
  pinMode(buttonSubPin, INPUT_PULLUP);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi");
}

void loop() {
  if (digitalRead(buttonAddPin) == LOW) {
    temperature++;
    inputChanged = true;
    lastInputTime = millis();
    Serial.println("Button + pressed");
    delay(300); // debounce
  }

  if (digitalRead(buttonSubPin) == LOW) {
    temperature--;
    inputChanged = true;
    lastInputTime = millis();
    Serial.println("Button - pressed");
    delay(300); // debounce
  }

  // After 5 seconds of inactivity, send the data
  if (inputChanged && millis() - lastInputTime >= 5000) {
    sendTemperature(temperature);
    inputChanged = false;
  }
}

void sendTemperature(int temp) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"temperature\": " + String(temp) + "}";

    int httpResponseCode = http.POST(payload);

    if (httpResponseCode > 0) {
      Serial.printf("✅ Sent! Status: %d\n", httpResponseCode);
      Serial.println(http.getString());
    } else {
      Serial.printf("❌ Error sending data: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
  } else {
    Serial.println("❌ WiFi not connected");
  }
}
