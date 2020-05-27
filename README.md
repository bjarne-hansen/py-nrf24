# nrf24 for Python

This package implement 2.4Ghz communication using NRF24L01 modules on a Raspberry Pi using Python.

The code is based on a modified version of some example code found on [StackExchange](https://raspberrypi.stackexchange.com/questions/77290/nrf24l01-only-correctly-retrieving-status-and-config-registers).  The author of the original code is also the author of the ```pigpio``` library found here http://abyz.me.uk/rpi/pigpio/.

I have obtained the original authors approval to modify and distribute the code anyway I want.  So, I have created a very basic Python package and published it on PyPI under a MIT license.

The ```nrf24``` packages depends on the ```pigpio``` package that is available via PyPI as well.

## Installing

    $ pip install nrf24

## Cloning

If you want to work with the source code and examples, you can clone the repository.

    $ git clone https://github.com/bjarne-hansen/py-nrf24.git

After cloning you should create a virtualenv and install requirements.

    $ pip install -r requirements.txt

Examples reads the environment variable ```PIGPIO_HOST``` in order to connect to the ```pigpiod``` daemon on the Raspberry Pi.

    $ export PIGPIO_HOST=server.example.com


## Example

The example shows a listener reading temperature and humidity data sent from an Arduino Nano.



    import pigpio
    import nrf24
    import os.environ as env

    # Connect to Raspberry Pi
    pi = pigpio.pi(env['PIGPIO_HOST'])
    
    # Set up NRF24L01 module for reading.
    radio = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC)
    radio.open_reading_pipe(RF24_RX_ADDR.P1, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])

    while True:
        while radio.data_ready(): 
            # Get pipe, payload.
            pipe = radio.data_pipe()
            payload = radio.get_payload()

            # Convert data to hex.
            hex = ':'.join(f'{i:02x}' for i in payload)
            
            print(f'Data received on pipe {pipe}: {hex}')
            
            # Unpack protocol, temperature, and humidity.
            (p, t, h) = struct.unpack('<Bff', payload)

            # Report
            print(f'Temperature: {t}, humidity: {h}')

The wiring of the Raspberry Pi and the NRF24L01 module should be along the line of that shown in the Fritzing breadboard configuration below.

![Raspberry Pi Zero Configration](doc/pizw-nrf24-1_bb.png)

The corresponding Arduino transmitter code would be along the following lines:

    #include <nRF24L01.h>
    #include <RF24_config.h>
    #include <RF24.h>

    // "DHT sensor library by Adafruit"
    //   https://github.com/adafruit/DHT-sensor-library
    #include <DHT.h>
    #include <DHT_U.h>

    #define PIN_CS   9
    #define PIN_CE  10
    #define PIN_DHT  5

    RF24 radio(PIN_CE, PIN_CS);
    const uint64_t tx_addr = 0xBABEFACE01LL;                        

    byte protocol = 1;
    byte payload[32]; 

    DHT dht(PIN_DHT, DHT11);

    void setup() {
        // Setup radio.
        radio.begin();
        radio.enableDynamicPayloads();
        radio.setAutoAck(true);
        radio.setDataRate(RF24_1MBPS);
        radio.openWritingPipe(tx_addr);
        radio.stopListening();

        // Setup sensor.
        dht.begin();
    }

    void loop() {  
        float t, h;
        
        // Read sensor.
        h = dht.readHumidity();
        t = dht.readTemperature();

        // Prepare payload.
        memcpy(payload, (byte *)(&protocol), 1);
        memcpy((payload + 1), (byte *)(&t), 4);
        memcpy((payload + 5), (byte *)(&h), 4);
    
        // Send payload.
        radio.write(payload, 9);
    }

The wiring for the Arduino Nano, the NRF24L01 module, and the DHT22 temperature sensor would be like shown in the Fritzing sketch below.

![Arduino Nano](doc/nano-nrf24-1_bb.png)

More examples can be found in the ```/test``` folder of the project.
    


