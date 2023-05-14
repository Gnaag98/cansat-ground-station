struct Acceleration {
  float x, y, z;
};

struct Data {
  Acceleration acceleration;
  unsigned long time;
  float WP_temp;
  int sound;
  int distance;
  int air_quality;
  byte DHT11_temp_inside;
  byte DHT11_hum_inside;
  byte DHT11_temp_outside;
  byte DHT11_hum_outside;
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
      .DHT11_temp_outside = 11,
      .DHT11_hum_outside = 12
    };

    auto serialized = reinterpret_cast<const char *>(&data);

    Serial.print('0'); // Signals the start of the message.
    for (int i = 0; i < sizeof(data); ++i) {
      Serial.print(serialized[i]);
    }
    
    lastTime = now;
  }

  while (Serial.available()) {
    const char character = Serial.read();
    Serial.print(character);
  }
}
