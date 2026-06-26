/**
 * Smart Plant Doctor ESP32 firmware
 * - NVS storage for device_token and ingest_url after claim
 * - Multi-pot ingest (pot_index 0-3)
 * - Polls pending relay commands from backend
 *
 * First-time setup: set WIFI_SSID / WIFI_PASSWORD below, flash, then claim via API.
 * Serial: send SETUP_TOKEN=<token> to trigger claim when WiFi is connected.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <DHT.h>
#include <time.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// --- WiFi (configure for your network) ---
#ifndef WIFI_SSID
#define WIFI_SSID "YOUR_WIFI_SSID"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#endif

#ifndef API_BASE_URL
#define API_BASE_URL "http://192.168.1.100:8000"
#endif

#define DHTPIN 18
#define DHTTYPE DHT11
#define LDR_PIN 34
#define SOIL_PINS 35, 32, 33, 36
#define RELAY_PIN 26
#define NUM_POTS 4

const char* ntpServer = "pool.ntp.org";
const long gmtOffsetSec = 0;
const int daylightOffsetSec = 0;

DHT dht(DHTPIN, DHTTYPE);
Preferences prefs;

String deviceToken;
String ingestUrl;
String deviceId;
String setupTokenPending;
bool claimed = false;

const int soilPins[NUM_POTS] = {SOIL_PINS};

float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

float ldrToLux(int raw) {
  return clampf((raw / 4095.0f) * 1200.0f, 0.0f, 1200.0f);
}

float soilToPercent(int raw) {
  const float wetAdc = 1200.0f;
  const float dryAdc = 3200.0f;
  return clampf((dryAdc - raw) / (dryAdc - wetAdc) * 100.0f, 0.0f, 100.0f);
}

long currentEpochSeconds() {
  time_t now = time(nullptr);
  if (now > 946684800) return (long)now;
  return (long)(millis() / 1000UL);
}

void loadCredentials() {
  prefs.begin("spd", true);
  deviceToken = prefs.getString("dev_token", "");
  ingestUrl = prefs.getString("ingest_url", "");
  deviceId = prefs.getString("device_id", "");
  claimed = deviceToken.length() > 0 && ingestUrl.length() > 0;
  prefs.end();
  if (!claimed) {
    ingestUrl = String(API_BASE_URL) + "/api/v1/ingest";
  }
}

void saveCredentials(const String& token, const String& url, const String& devId) {
  prefs.begin("spd", false);
  prefs.putString("dev_token", token);
  prefs.putString("ingest_url", url);
  prefs.putString("device_id", devId);
  prefs.end();
  deviceToken = token;
  ingestUrl = url;
  deviceId = devId;
  claimed = true;
}

void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (int i = 0; i < 30 && WiFi.status() != WL_CONNECTED; i++) delay(500);
}

bool claimDevice(const String& setupToken) {
  if (WiFi.status() != WL_CONNECTED) return false;
  HTTPClient http;
  String url = String(API_BASE_URL) + "/api/v1/devices/claim";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  String body = "{\"setup_token\":\"" + setupToken + "\",\"firmware_version\":\"2.0.0\"}";
  int code = http.POST(body);
  String response = http.getString();
  http.end();
  if (code != 200) {
    Serial.printf("Claim failed %d: %s\n", code, response.c_str());
    return false;
  }
  // Parse minimal JSON fields
  int tokIdx = response.indexOf("\"device_token\":\"");
  int urlIdx = response.indexOf("\"ingest_url\":\"");
  int devIdx = response.indexOf("\"device_id\":");
  if (tokIdx < 0 || urlIdx < 0) return false;
  tokIdx += 16;
  urlIdx += 14;
  String token = response.substring(tokIdx, response.indexOf('"', tokIdx));
  String ingest = response.substring(urlIdx, response.indexOf('"', urlIdx));
  String devId = "1";
  if (devIdx >= 0) {
    devIdx += 12;
    devId = response.substring(devIdx);
    devId.trim();
    int comma = devId.indexOf(',');
    if (comma > 0) devId = devId.substring(0, comma);
  }
  saveCredentials(token, ingest, devId);
  Serial.println("Device claimed OK");
  return true;
}

void postReadings() {
  if (!claimed || WiFi.status() != WL_CONNECTED) return;

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int ldrValue = analogRead(LDR_PIN);
  float lightLux = ldrToLux(ldrValue);
  long ts = currentEpochSeconds();

  String body = "{\"readings\":[";
  for (int pot = 0; pot < NUM_POTS; pot++) {
    int soilRaw = analogRead(soilPins[pot]);
    float soilPct = soilToPercent(soilRaw);
    if (pot > 0) body += ",";
    body += "{";
    body += "\"pot_index\":" + String(pot) + ",";
    body += "\"ts\":" + String(ts) + ",";
    body += "\"temperature\":" + String(temperature, 2) + ",";
    body += "\"humidity\":" + String(humidity, 2) + ",";
    body += "\"light\":" + String(lightLux, 2) + ",";
    body += "\"soil_moisture\":" + String(soilPct, 2) + ",";
    body += "\"ph\":6.5";
    body += "}";
  }
  body += "]}";

  HTTPClient http;
  http.begin(ingestUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + deviceToken);
  int code = http.POST(body);
  Serial.printf("Ingest %d\n", code);
  http.end();
}

void pollCommands() {
  if (!claimed || deviceId.length() == 0) return;
  String base = String(API_BASE_URL);
  int apiIdx = ingestUrl.indexOf("/api/");
  if (apiIdx > 0) base = ingestUrl.substring(0, apiIdx);

  HTTPClient http;
  String url = base + "/api/v1/devices/" + deviceId + "/commands/pending";

  http.begin(url);
  http.addHeader("Authorization", "Bearer " + deviceToken);
  int code = http.GET();
  if (code == 200) {
    String resp = http.getString();
    if (resp.indexOf("water") >= 0) {
      digitalWrite(RELAY_PIN, HIGH);
      delay(5000);
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("Water command executed");
    }
  }
  http.end();
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  dht.begin();
  loadCredentials();
  ensureWiFi();
  configTime(gmtOffsetSec, daylightOffsetSec, ntpServer);
  Serial.println("Smart Plant Doctor firmware ready");
  Serial.println("Send SETUP_TOKEN=your_token via Serial to claim device");
}

unsigned long lastPost = 0;

void loop() {
  ensureWiFi();

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("SETUP_TOKEN=")) {
      setupTokenPending = line.substring(12);
      claimDevice(setupTokenPending);
    }
  }

  if (millis() - lastPost > 3000) {
    lastPost = millis();
    postReadings();
    pollCommands();
  }
  delay(50);
}
