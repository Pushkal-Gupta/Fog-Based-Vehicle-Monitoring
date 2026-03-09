#include <WiFi.h>
#include <WebServer.h>
#include <SPIFFS.h>
#include <ArduinoJson.h>

/* ================= WIFI ================= */
const char* ssid     = "Voyager";
const char* password = "hellobantu";

/* ================= HTTP SERVER ================= */
WebServer server(80);

/* ================= CSV STATE ================= */
File csvFile;
bool headerSkipped = false;

/* ================= LED DEFINITIONS ================= */
#define LED_ENGINE_OIL     2
#define LED_ENGINE_KNOCK   4
#define LED_BRAKE_TEMP    16
#define LED_TIRE_PRESSURE 17
#define LED_BATTERY       5

/* ================= CORS HELPER ================= */
void addCORSHeaders() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

/* ================= LED CONTROL HELPER ================= */
void controlLED(int pin, float value) {

  Serial.print("🔧 Updating LED on pin ");
  Serial.print(pin);
  Serial.print(" with value: ");
  Serial.println(value);

  digitalWrite(pin, value == 0 ? LOW : HIGH);
}

/* ================= SEND NEXT CSV ROW ================= */
void handleNextRow() {

  Serial.println("\n📡 /next request received");

  addCORSHeaders();

  if (!csvFile || !csvFile.available()) {

    Serial.println("⚠️ No more CSV data available");

    server.send(200, "application/json",
      "{ \"status\": \"END_OF_DATA\" }");
    return;
  }

  if (!headerSkipped) {

    Serial.println("📄 Skipping CSV header");

    csvFile.readStringUntil('\n');
    headerSkipped = true;
  }

  if (!csvFile.available()) {

    Serial.println("⚠️ CSV file reached end");

    server.send(200, "application/json",
      "{ \"status\": \"END_OF_DATA\" }");
    return;
  }

  String line = csvFile.readStringUntil('\n');
  line.trim();

  Serial.print("📄 CSV Row: ");
  Serial.println(line);

  String values[29];
  int index = 0;
  int lastPos = 0;

  for (int i = 0; i < line.length(); i++) {

    if (line.charAt(i) == ',') {

      if (index < 29) {
        values[index++] = line.substring(lastPos, i);
      }

      lastPos = i + 1;
    }
  }

  if (index < 28) {

    Serial.println("❌ CSV parse error");

    server.send(500, "application/json",
      "{ \"error\": \"CSV_PARSE_ERROR\" }");

    return;
  }

  values[index] = line.substring(lastPos);

  Serial.println("✅ CSV parsed successfully");

  String json = "{";
  json += "\"device_id\":\"" + values[0] + "\",";
  json += "\"vehicle_id\":\"" + values[1] + "\",";
  json += "\"timestamp_ms\":" + values[2] + ",";
  json += "\"engine_oil_temp_c\":" + values[3] + ",";
  json += "\"transmission_temp_c\":" + values[4] + ",";
  json += "\"brake_temp_c\":" + values[5] + ",";
  json += "\"radiator_temp_c\":" + values[6] + ",";
  json += "\"motor_rpm\":" + values[7] + ",";
  json += "\"vehicle_speed_kmph\":" + values[8] + ",";
  json += "\"fuel_efficiency_kmpl\":" + values[9] + ",";
  json += "\"battery_voltage_v\":" + values[10] + ",";
  json += "\"battery_health_pct\":" + values[11] + ",";
  json += "\"fuel_level_pct\":" + values[12] + ",";
  json += "\"cabin_humidity_pct\":" + values[13] + ",";
  json += "\"cabin_temp_c\":" + values[14] + ",";
  json += "\"tire_pressure_fl_kpa\":" + values[15] + ",";
  json += "\"tire_pressure_fr_kpa\":" + values[16] + ",";
  json += "\"tire_pressure_rl_kpa\":" + values[17] + ",";
  json += "\"tire_pressure_rr_kpa\":" + values[18] + ",";
  json += "\"gyro_x_dps\":" + values[19] + ",";
  json += "\"gyro_y_dps\":" + values[20] + ",";
  json += "\"gyro_z_dps\":" + values[21] + ",";
  json += "\"ambient_pressure_kpa\":" + values[22] + ",";
  json += "\"output_voltage_v\":" + values[23] + ",";
  json += "\"engine_rpm_variance\":" + values[24] + ",";
  json += "\"brake_temp_rise_rate\":" + values[25] + ",";
  json += "\"vibration_rms\":" + values[26] + ",";
  json += "\"dominant_vibration_hz\":" + values[27] + ",";
  json += "\"engine_load_pct\":" + values[28];
  json += "}";

  Serial.println("📤 Sending JSON to client:");
  Serial.println(json);

  server.send(200, "application/json", json);
}

/* ================= RESET CSV ================= */
void handleReset() {

  Serial.println("\n🔄 /reset request received");

  addCORSHeaders();

  if (csvFile) {

    Serial.println("📁 Closing previous CSV file");

    csvFile.close();
  }

  csvFile = SPIFFS.open("/car_data.csv", "r");
  headerSkipped = false;

  if (!csvFile) {

    Serial.println("❌ Failed to reopen CSV");

    server.send(500, "application/json",
      "{ \"status\": \"RESET_FAILED\" }");

    return;
  }

  Serial.println("✅ CSV reset successful");

  server.send(200, "application/json",
    "{ \"status\": \"RESET_OK\" }");
}

/* ================= POST FLAGS + LED CONTROL ================= */
void handleFlags() {

  Serial.println("\n📡 /flags POST received");

  addCORSHeaders();

  if (server.method() == HTTP_OPTIONS) {

    Serial.println("📡 CORS preflight request");

    server.send(200);
    return;
  }

  if (!server.hasArg("plain")) {

    Serial.println("❌ No JSON body received");

    server.send(400, "application/json",
      "{ \"error\": \"NO_JSON_BODY\" }");

    return;
  }

  String body = server.arg("plain");

  Serial.println("📥 Received JSON:");
  Serial.println(body);

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, body);

  if (err) {

    Serial.println("❌ JSON parsing failed");

    server.send(400, "application/json",
      "{ \"error\": \"JSON_PARSE_FAILED\" }");

    return;
  }

  Serial.println("✅ JSON parsed successfully");

  float engine_oil_temp_c    = doc["engine_oil_temp_c"] | 0;
  float engine_knock_prob    = doc["engine_knock_prob"] | 0;
  float brake_temp_c         = doc["brake_temp_c"] | 0;
  float tire_pressure_fl_kpa = doc["tire_pressure_fl_kpa"] | 0;
  float battery_voltage_v    = doc["battery_voltage_v"] | 0;

  Serial.println("🔧 Updating LEDs based on received values");

  controlLED(LED_ENGINE_OIL,    engine_oil_temp_c);
  controlLED(LED_ENGINE_KNOCK,  engine_knock_prob);
  controlLED(LED_BRAKE_TEMP,    brake_temp_c);
  controlLED(LED_TIRE_PRESSURE, tire_pressure_fl_kpa);
  controlLED(LED_BATTERY,       battery_voltage_v);

  Serial.println("✅ LEDs updated successfully");

  server.send(200, "application/json",
    "{ \"status\": \"FLAGS_RECEIVED_AND_LEDS_UPDATED\" }");
}

/* ================= SETUP ================= */
void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println("\n🚀 ESP32 Starting...");

  pinMode(LED_ENGINE_OIL, OUTPUT);
  pinMode(LED_ENGINE_KNOCK, OUTPUT);
  pinMode(LED_BRAKE_TEMP, OUTPUT);
  pinMode(LED_TIRE_PRESSURE, OUTPUT);
  pinMode(LED_BATTERY, OUTPUT);

  Serial.println("💡 LEDs configured");

  digitalWrite(LED_ENGINE_OIL, LOW);
  digitalWrite(LED_ENGINE_KNOCK, LOW);
  digitalWrite(LED_BRAKE_TEMP, LOW);
  digitalWrite(LED_TIRE_PRESSURE, LOW);
  digitalWrite(LED_BATTERY, LOW);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("📶 Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi connected");
  Serial.print("🌐 ESP32 IP: ");
  Serial.println(WiFi.localIP());

  if (!SPIFFS.begin(true)) {

    Serial.println("❌ SPIFFS mount failed");
    return;
  }

  Serial.println("✅ SPIFFS mounted");

  csvFile = SPIFFS.open("/car_data.csv", "r");

  if (!csvFile) {

    Serial.println("❌ CSV file not found");
    return;
  }

  Serial.println("✅ CSV file opened");

  server.on("/next",  HTTP_GET, handleNextRow);
  server.on("/reset", HTTP_GET, handleReset);
  server.on("/flags", HTTP_POST, handleFlags);
  server.on("/flags", HTTP_OPTIONS, handleFlags);

  server.begin();

  Serial.println("🌍 HTTP server started");
}

/* ================= LOOP ================= */
void loop() {

  server.handleClient();
}
