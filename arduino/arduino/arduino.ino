#include <SPI.h>
#include <RF24.h>

#define RADIO_CE_PIN 9
#define RADIO_CSN_PIN 10

const uint8_t ground_station_address[6] = { "GRND4" };
const uint8_t can_sat_address[6] = { "CANS4" };

RF24 radio(RADIO_CE_PIN, RADIO_CSN_PIN);

struct Vector {
  int x, y, z;
};

struct Data {
  Vector acceleration;
  Vector gyroscope;
  unsigned long time;
  int temperature_outside;
  int distance;
  int air_quality;
  int sound;
  byte temperature_inside;
  byte humidity_inside;
  byte humidity_outside;
};

struct DropData {
  Vector acceleration;
  Vector gyro;
  unsigned long time;
};

struct Command {
  byte action;
  byte value;
};

enum HeaderByte : char {
  data_header_byte = '0',
  drop_header_byte,
  text_header_byte
};

enum CommandTypes {
  accelerationCommand = 0,
  gyroCommand = 1,
  waterproofCommand = 2,
  ultrasonicCommand = 3,
  airQualityCommand = 4,
  soundCommand = 5,
  dhtInsideCommand = 6,
  dhtOutsideCommand = 7,
  onCommand = 8,
  radioChannelCommand = 9
};

enum class ReceiveState {
    header,
    action,
    value
};

const char radioErrorMessage[] = "Radio hardware is not responding!";

unsigned long lastTime = 0;

const int startingRadioChannel = 111;

const char headerBytes[] = { '0', '1' };
int headerIndex = 0;
ReceiveState receiveState = ReceiveState::header;
Command receivedCommand;
unsigned long receiveStart;

void sendHeader(const char type) {
  for (int i = 0; i < sizeof(headerBytes); ++i) {
    Serial.print(headerBytes[i]);
  }
  Serial.print(type);
}

void sendData(const Data &data) {
  sendHeader(data_header_byte);

  const auto byteInterpretation = reinterpret_cast<const char *>(&data);

  for (int i = 0; i < sizeof(data); ++i) {
    Serial.print(byteInterpretation[i]);
  }
}

void sendDropData(const DropData &data) {
  sendHeader(drop_header_byte);

  const auto byteInterpretation = reinterpret_cast<const char *>(&data);

  for (int i = 0; i < sizeof(data); ++i) {
    Serial.print(byteInterpretation[i]);
  }
}

void sendText(const char *text) {
  sendHeader(text_header_byte);
  Serial.println(text);
}

void transmitCommand(Command command) {
  radio.txStandBy();
  radio.stopListening();

  const auto transmitStart = millis();
  unsigned long duration;

  bool wasTransmitted;
  do {
    duration = millis() - transmitStart;
    wasTransmitted = radio.write(&command, sizeof(command));

    if (wasTransmitted && command.action == radioChannelCommand) {
      radio.setChannel(command.value);
    }

  } while (!wasTransmitted && duration < 100);

  radio.startListening();
}

void setup() {
  Serial.begin(115200);
  
  //Radio Transmitter
  if (!radio.begin()) {
    sendText(radioErrorMessage);
    while (true);  // Hold in an infinite loop.
  }
  radio.setDataRate(RF24_2MBPS);
  radio.setPALevel(RF24_PA_MAX);
  radio.setChannel(startingRadioChannel);
  radio.enableDynamicPayloads();
  radio.openWritingPipe(ground_station_address);
  radio.openReadingPipe(1, can_sat_address);
  radio.startListening();

  lastTime = millis();
}

void loop() {
  if (radio.available()) {
    const auto receivedSize = radio.getDynamicPayloadSize();
    if (receivedSize == sizeof(Data)) {
      Data data;
      radio.read(&data, sizeof(data));
      sendData(data);
    } else if (receivedSize == sizeof(DropData)) {
      DropData data;
      radio.read(&data, sizeof(data));
      sendDropData(data);
    } else {
      sendText("Error received");
      radio.flush_rx();
    }
  }

  while (Serial.available()) {
    const char character = Serial.read();

    const auto now = millis();
    const auto duration = now - receiveStart;

    switch (receiveState) {
    case ReceiveState::header:
      if (character == headerBytes[headerIndex]) {
        ++headerIndex;
        if (headerIndex == sizeof(headerBytes)) {
          receiveState = ReceiveState::action;
          headerIndex = 0;
          receiveStart = millis();
        }
      } else {
        headerIndex = 0;
      }
      break;

    case ReceiveState::action:
      if (duration > 100) {
        receiveState = ReceiveState::header;
        sendText("Arduino timeout");
        break;
      }
      receivedCommand.action = (byte)character;
      receiveState = ReceiveState::value;
      break;
    
    case ReceiveState::value:
      if (duration > 100) {
        receiveState = ReceiveState::header;
        sendText("Arduino timeout");
        break;
      }
      receivedCommand.value = (byte)character;
      receiveState = ReceiveState::header;
      transmitCommand(receivedCommand);
      break;
    }
  }
}
