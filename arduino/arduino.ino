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

void setup() {
  Serial.begin(115200);
}

void loop() {
  const auto now = millis();
  if (now - lastTime > 2000) {
    auto data = Data{
      .acceleration = Acceleration{ random(1000), random(2000), random(3000) },
      .time = now,
      .temperature_outside = random(5000),
      .sound = random(6),
      .distance = random(7),
      .air_quality = random(8),
      .temperature_inside = random(9),
      .humidity_inside = random(10),
      .humidity_outside = random(11)
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
