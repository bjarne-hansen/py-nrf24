import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
from random import normalvariate

#
# A simple NRF24L01 sender script that pretends to be a soil mosture and humidity
# sensor sending data that can be received by test/rcvr-01.py.
#
if __name__ == "__main__":

    # Tell what we are ...
    print("Python NRF24L01 Sender Example 01 ...")

    # Establish connection to the pigpiod daemon.
    print("Connecting to:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.open_writing_pipe([0x01, 0xCE, 0xFA, 0xBE, 0xBA])

    # Take a small break to let tranceiver settle and then show registers of the NRF24L01 device.
    time.sleep(0.5)
    nrf.show_registers()

    count = 0
    while True:

        # Emulate that we read temperature and humidity from a sensor, for example
        # a DHT22 sensor.  Add a little random variation so we can see that values
        # sent/received fluctuate a bit.
        temperature = normalvariate(23.0, 0.5)
        humidity = normalvariate(62.0, 0.5)
        print(f'Sensor values: temperature={temperature}, humidity={humidity}')

        # Pack temperature and humidity into a byte buffer (payload) using a protocol 
        # signature of 0x01 so that the receiver knows that the bytes we are sending 
        # are a temperature and a humidity (see rcvr-01.py).
        payload = struct.pack("<Bff", 0x01, temperature, humidity)

        # Send the payload to the address specified above.
        nrf.send(payload)

        # Wait 10 seconds before sending the next reading.
        time.sleep(10)





