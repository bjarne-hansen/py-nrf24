#include <printf.h>
#include <RF24.h>

#define PIN_RF24_CSN             9                // CSN PIN for RF24 module.
#define PIN_RF24_CE             10                // CE PIN for RF24 module.

#define NRF24_CHANNEL          100                // 0 ... 125
#define NRF24_CRC_LENGTH         RF24_CRC_16      // RF24_CRC_DISABLED, RF24_CRC_8, RF24_CRC_16 for 16-bit
#define NRF24_DATA_RATE          RF24_250KBPS     // RF24_2MBPS, RF24_1MBPS, RF24_250KBPS
#define NRF24_DYNAMIC_PAYLOAD    1
#define NRF24_PAYLOAD_SIZE      32                // Max. 32 bytes.
#define NRF24_PA_LEVEL           RF24_PA_MIN      // RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH, RF24_PA_MAX    
#define NRF24_RETRY_DELAY       10                // Delay bewteen retries, 1..15.  Multiples of 250µs.
#define NRF24_RETRY_COUNT       15                // Number of retries, 1..15.
                                      
byte rf24_tx[6] = "1SRVR";                        // Address used when transmitting data.
byte rf24_rx[6] = "1CLNT";                        // Address used when receiving data.
byte payload[32];                                 // Payload bytes. Used both for transmitting and receiving

unsigned long ms_between_requests = 10000;        // 10000 ms = 10 seconds
unsigned long last_reading = 0;                   // Milliseconds since last measurement was read.

RF24 radio(PIN_RF24_CE, PIN_RF24_CSN);            // Instance of RF24.

void setup() {
  // Initialize serial communication.
  Serial.begin(115200);
  printf_begin();
  delay(100);
  
  // Show that program is starting.
  Serial.println("\n\nNRF24L01 Arduino Request/Response Client.");

  // Configure the NRF24 tranceiver.
  Serial.println("Configure NRF24 ...");
  nrf24_setup();
  
  // Show debug information for NRF24 tranceiver.
  radio.printDetails();
}

void loop() {
  if (millis() - last_reading > ms_between_requests) {
    // Send a request once in a while ...
    send_request();
  }
}

void send_request() {
    // Step out of listening mode ...
    radio.stopListening();
    radio.flush_tx();
     
    // Chose a random command 0x01 or 0x02 ...
    unsigned int cmd = random(1, 3);
    byte addr_len = 5;

    // Prepare payload ...
    int offset = 0;  
    memcpy(payload + offset, (byte *)(&cmd), sizeof(cmd)); offset += sizeof(cmd); 
    memcpy(payload + offset, &addr_len, sizeof(addr_len)); offset += sizeof(addr_len); 
    memcpy(payload + offset, (byte *)(&rf24_rx), sizeof(rf24_rx)); offset += sizeof(rf24_rx) - 1;

    // Send request ...
    Serial.print("Request: cmd="); Serial.println(cmd);
    if (radio.write(payload, offset)) {
      // Request was successful.
      Serial.print("Success. Retries="); Serial.println(radio.getARC());
      
      // Read response to our request.
      read_response();      
    }
    else {
      Serial.print(">>> ERROR. Retries="); Serial.println(radio.getARC());
      radio.startListening();
    }  
    
    last_reading = millis();
    
}

void read_response() {
  unsigned int cmd;
  boolean relay;

  radio.startListening();
  // Wait here until we get a response, or timeout
  unsigned long started_waiting_at = millis();
  bool timeout = false;
  while (!radio.available() && !timeout) {
    if (millis() - started_waiting_at > 500 ) {
      timeout = true;
    }
  }

  if (timeout) {
    Serial.println("Timeout waiting for response.");
    return;
  }

  uint8_t plen = radio.getDynamicPayloadSize();
  radio.read(&payload, plen);

  // Extract command from payload
  memcpy(&cmd, payload, sizeof(cmd));
  Serial.print("Response: cmd="); Serial.println(cmd);
    
  if (cmd == 0x01) {
    // Response to command #1.
    Serial.print("Response #1: uuid=");
    print_bytes(payload, 2, 16);
    Serial.println();
  }
  else if (cmd == 0x02) {
    // Response to command #2.
    Serial.print("Response #2: relay=");
    memcpy(&relay, payload + 2, sizeof(relay));  
    Serial.println(relay);    
  }
  else {
    // We process only responses to command 0x01 (get uuid) and 0x02 (get relay state).
    Serial.print(">>> BAD response received: "); Serial.println(cmd);
  }
}

void print_bytes(byte *buffer, int start, int count) {
  for (int i = start; i < start + count; i++) {    
      if (i > start) Serial.print(":");
      if (buffer[i] < 16) Serial.print("0");
      Serial.print(buffer[i], HEX);
    }
}

void nrf24_setup()
{
  radio.begin();
  radio.enableDynamicPayloads();
  radio.setAutoAck(true);                 
  radio.setPALevel(NRF24_PA_LEVEL);
  radio.setRetries(NRF24_RETRY_DELAY, NRF24_RETRY_COUNT);              
  radio.setDataRate(NRF24_DATA_RATE);          
  radio.setChannel(NRF24_CHANNEL);
  radio.setCRCLength(NRF24_CRC_LENGTH);
  radio.setPayloadSize(NRF24_PAYLOAD_SIZE);
  radio.openWritingPipe(rf24_tx);
  radio.openReadingPipe(1, rf24_rx);
  radio.startListening();
}
