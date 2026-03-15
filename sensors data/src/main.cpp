#define BLYNK_PRINT Serial

#define BLYNK_TEMPLATE_ID "TMPL30SDQvWJ-"
#define BLYNK_TEMPLATE_NAME "Smart plant doctor "
#define BLYNK_AUTH_TOKEN "NYBW0sT3yQds1XwWsioyF18uSENfoNfb"

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>
#include <time.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ---------------- WIFI ----------------
const char* ssid = "Pixel";
const char* password = "dontknow";

// ---------------- INGEST API ----------------
// Use your laptop LAN IP where `uvicorn ingest:app --host 0.0.0.0 --port 8000` is running.
const char* ingestUrl = "http://192.168.29.40:8000/ingest";
const char* ingestToken = "changeme";
const char* plantName = "Money Plant";

// NTP configuration for epoch timestamps.
const char* ntpServer = "pool.ntp.org";
const long gmtOffsetSec = 0;
const int daylightOffsetSec = 0;

// ---------------- PINS ----------------
#define DHTPIN 18
#define DHTTYPE DHT11
#define LDR_PIN 34
#define SOIL_PIN 35

// ---------------- OBJECTS ----------------
DHT dht(DHTPIN, DHTTYPE);
BlynkTimer timer;

float clampf(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

float ldrToLux(int raw) {
  return clampf((raw / 4095.0f) * 1200.0f, 0.0f, 1200.0f);
}

float soilToPercent(int raw) {
  const float wetAdc = 1200.0f;
  const float dryAdc = 3200.0f;
  float pct = (dryAdc - raw) / (dryAdc - wetAdc) * 100.0f;
  return clampf(pct, 0.0f, 100.0f);
}

long currentEpochSeconds() {
  time_t now = time(nullptr);
  if (now > 946684800) {
    return static_cast<long>(now);
  }
  return static_cast<long>(millis() / 1000UL);
}

void ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
  WiFi.disconnect();
  WiFi.begin(ssid, password);
  for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
}

void postToIngest(float temperature, float humidity, int ldrValue, int soilValue) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Ingest skip: WiFi disconnected");
    return;
  }

  const float lightLux = ldrToLux(ldrValue);
  const float soilPct = soilToPercent(soilValue);
  const float ph = 6.5f;
  const long ts = currentEpochSeconds();

  String body = "{";
  body += "\"ts\":" + String(ts) + ",";
  body += "\"plant\":\"" + String(plantName) + "\",";
  body += "\"temperature\":" + String(temperature, 2) + ",";
  body += "\"humidity\":" + String(humidity, 2) + ",";
  body += "\"light\":" + String(lightLux, 2) + ",";
  body += "\"soil_moisture\":" + String(soilPct, 2) + ",";
  body += "\"ph\":" + String(ph, 2);
  body += "}";

  HTTPClient http;
  http.begin(ingestUrl);
  http.setTimeout(5000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + String(ingestToken));
  int code = http.POST(body);
  String response = http.getString();
  http.end();

  if (code == 200 && response.indexOf("\"ok\":true") >= 0) {
    Serial.println("Ingest OK");
  } else {
    Serial.print("Ingest failed: ");
    Serial.print(code);
    Serial.print(" ");
    Serial.println(response);
  }
}

// -------- FUNCTION TO SEND DATA --------
void sendToBlynk() {

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  int ldrValue = analogRead(LDR_PIN);
  int soilValue = analogRead(SOIL_PIN);

  String soilStatus;

  if (soilValue < 1500) {
    soilStatus = "Wet 🌱";
  } 
  else if (soilValue < 2500) {
    soilStatus = "Moist 💧";
  } 
  else {
    soilStatus = "Dry ⚠️";
  }


  // Send to Blynk
  Blynk.virtualWrite(V0, temperature);
  Blynk.virtualWrite(V1, humidity);
  Blynk.virtualWrite(V2, soilValue);
  Blynk.virtualWrite(V3, ldrValue);
  Blynk.virtualWrite(V4, soilStatus);

  // Send to your dashboard backend over Wi-Fi.
  postToIngest(temperature, humidity, ldrValue, soilValue);

  Serial.println("Data sent to Blynk ✅");
}

void setup() {
  // Disable brownout
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  delay(1000);

  // Start sensors
  dht.begin();

  // Connect WiFi
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected ✅");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Start Blynk
  Serial.println("Connecting to Blynk...");
  Blynk.config(BLYNK_AUTH_TOKEN);
  Blynk.connect();

  // Configure NTP for usable epoch timestamps.
  configTime(gmtOffsetSec, daylightOffsetSec, ntpServer);

  // Send data every 3 seconds
  timer.setInterval(3000L, sendToBlynk);

  Serial.println("\nSystem Ready 🚀\n");
}

void loop() {

  ensureWiFiConnected();
  Blynk.run();
  timer.run();

  // -------- READ DHT --------
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  int ldrValue = analogRead(LDR_PIN);
  int soilValue = analogRead(SOIL_PIN);

  Serial.print("WiFi Status: ");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connected ✅");
  } else {
    Serial.println("Disconnected ❌");
  }

  Serial.println("===== Sensor Readings =====");

  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");

  Serial.print("LDR Value: ");
  Serial.println(ldrValue);

  Serial.print("Soil Moisture Value: ");
  Serial.println(soilValue);

  if (soilValue < 1500) {
    Serial.println("Soil Status: Wet");
  } else if (soilValue < 2500) {
    Serial.println("Soil Status: Moist");
  } else {
    Serial.println("Soil Status: Dry");
  }

  Serial.println("============================\n");
  delay(250);
}