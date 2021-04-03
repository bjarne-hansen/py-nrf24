import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
from random import normalvariate
import argparse
import sys

#
# A simple NRF24L01 sender script that pretends to be a soil mosture and humidity
# sensor sending data that can be received by test/rcvr-01.py.
#
if __name__ == "__main__":    
    print("Python NRF24 Simple Sender Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="simple-sender.py", description="Simple NRF24 transmitter.")
    parser.add_argument('-h' '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p' '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, default='1SNSR', help="Address to listen to (1 to 5 characters).")
    
    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    if not (len(address) > 0 and len(address) < 6):
        print(f'ERROR: invalid address {address}')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.open_writing_pipe(address)

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





