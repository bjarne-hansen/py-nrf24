#include <DHT.h>
#include <printf.h>
#include <RF24.h>

#define PIN_DHT                  2              // PIN for DHT sensor communication.

#define PIN_RF24_CSN             9              // CSN PIN for RF24 module.
#define PIN_RF24_CE             10              // CE PIN for RF24 module.

#define NRF24_CHANNEL          100              // 0 ... 125
#define NRF24_CRC_LENGTH         RF24_CRC_16    // RF24_CRC_DISABLED, RF24_CRC_8, RF24_CRC_16 for 16-bit
#define NRF24_DATA_RATE          RF24_250KBPS   // RF24_2MBPS, RF24_1MBPS, RF24_250KBPS
#define NRF24_DYNAMIC_PAYLOAD    1
#define NRF24_PAYLOAD_SIZE      32              // Max. 32 bytes.
#define NRF24_PA_LEVEL           RF24_PA_MAX    // RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH, RF24_PA_MAX    
#define NRF24_RETRY_DELAY        5              // Delay bewteen retries, 1..15.  Multiples of 250µs.
#define NRF24_RETRY_COUNT       15              // Number of retries, 1..15.

#define PROTOCOL 0x01                           // 0x01 (byte), temperature (float), humidity (float)
                                                // Python 1: "<Bff"

#define DHT_TYPE              DHT22             // Type of DHT sensor:
                                                // DHT11, DHT12, DHT21, DHT22 (AM2302), AM2301
                                      
RF24 radio(PIN_RF24_CE, PIN_RF24_CSN);          // Cretate NRF24L01 radio.
DHT dht(PIN_DHT, DHT_TYPE);                     // Create DHT sensor.

byte rf24_tx[6] = "1ACKS";                      // Address used when transmitting data.
byte payload[32];                               // Payload bytes. Used both for transmitting and receiving

unsigned long last_reading = 0;                 // Milliseconds since last measurement was read.
unsigned long ms_between_reads = 10000;         // 10000 ms = 10 seconds

void setup() {
  // Initialize serial.
  Serial.begin(115200);
  printf_begin();
  delay(100);
  
  // Show that program is starting.
  Serial.println("\n\nNRF24L01 Arduino Simple Sender.");

  // Configure the NRF24 tranceiver.
  Serial.println("Configure NRF24 ...");
  nrf24_setup();
  
  // Show debug information for NRF24 tranceiver.
  radio.printDetails();
  
  // Initialise the DHT sensor.
  dht.begin();
}

void loop() {

  if (millis() - last_reading > ms_between_reads) {
    // Read sensor values every "ms_between_read" milliseconds.
  
    // Read the humidity and temperature.
    float t, h;
    h = dht.readHumidity();
    t = dht.readTemperature();
    
    // Report the temperature and humidity.    
    Serial.print("Sensor values: temperature="); Serial.print(t); 
    Serial.print(", humidity="); Serial.println(h);

    // Stop listening on the radio (we can't both listen and send).
    radio.stopListening();

    // Send the data ...
    send_reading(PROTOCOL, t, h);

    // Start listening again.
    radio.startListening();

    // Register that we have read the temperature and humidity.
    last_reading = millis();
  }
}

void send_reading(byte protocol, float temperature, float humidity)
{
  int offset = 0;  
  Serial.println("Preparing payload.");
  memcpy(payload + offset, (byte *)(&protocol), sizeof(protocol)); offset += sizeof(protocol); 
  memcpy(payload + offset, (byte *)(&temperature), sizeof(temperature)); offset += sizeof(temperature);
  memcpy(payload + offset, (byte *)(&humidity), sizeof(humidity)); offset += sizeof(humidity);
  Serial.print("Bytes packed: "); Serial.println(offset);

  if (radio.write(payload, offset)) {
    if (!radio.available()) {
      Serial.println("No acknowledgement payload.");
    }
    else {
      radio.read(&payload, sizeof(payload));
      long next_id;
      memcpy(&next_id, payload, 4);
      Serial.print("Acknowledgement payload: "); Serial.println(next_id);
    }
    Serial.print("Payload sent successfully. Retries="); Serial.println(radio.getARC());
  }
  else {
    Serial.print("Failed to send payload. Retries="); Serial.println(radio.getARC());
  }   
}

void nrf24_setup()
{
  radio.begin();
  radio.setAutoAck(true);                 
  radio.enableAckPayload();
  radio.setPALevel(NRF24_PA_LEVEL);
  radio.setRetries(NRF24_RETRY_DELAY, NRF24_RETRY_COUNT);              
  radio.setDataRate(NRF24_DATA_RATE);          
  radio.setChannel(NRF24_CHANNEL);
  radio.setCRCLength(NRF24_CRC_LENGTH);
  radio.setPayloadSize(NRF24_PAYLOAD_SIZE);
  radio.openWritingPipe(rf24_tx);  
  radio.stopListening();
}
