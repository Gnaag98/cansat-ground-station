struct Acceleration {
  int x, y, z;
};

struct Data {
  Acceleration acceleration;
  unsigned long time;
  int temperature_outside;
  int sound;
  int distance;
  int air_quality;
  byte temperature_inside;
  byte humidity_inside;
  byte humidity_outside;
};

unsigned long lastTime = 0;
unsigned long timestamp = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  const auto now = millis();
  if (now - lastTime > 5000) {
    auto data = Data{
      .acceleration = Acceleration{ 1.0f, 2.0f, 3.0f },
      .time = ++timestamp,
      .WP_temp = 5.0f,
      .sound = 6,
      .distance = 7,
      .air_quality = 8,
      .DHT11_temp_inside = 9,
      .DHT11_hum_inside = 10,
      .DHT11_hum_outside = 11
    };

    auto serialized = reinterpret_cast<const char *>(&data);

    // Signal the start of the message.
    Serial.print("01");
    Serial.print('0');

    // Send the actual data.
    for (int i = 0; i < sizeof(data); ++i) {
      Serial.print(serialized[i]);
    }
    
    lastTime = now;
  }

  if (Serial.available()) {
    Serial.print("01");
    Serial.print('1');

    const auto start_time = millis();
    const auto timeout_duration = 500;

    unsigned long duration;
    char character;

    do {
      const auto now = millis();
      duration = now - start_time;

      if (Serial.available()) {
        character = Serial.read();
        Serial.print(character);
      }
      if (duration >= timeout_duration) {
        Serial.println();
      }
    } while (character != '\n' && duration < timeout_duration);
  }

}
