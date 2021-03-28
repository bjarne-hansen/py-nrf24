import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env

#
# A simple NRF24L01 receiver script that receives data on 6 different addresses
# and prints result on screen.  Please note that this receiver emulates a 
# small NRF24L01 gateway which looks at the first byte in the payload to determine
# what data is being sent.
#

if __name__ == "__main__":

    print("Python NRF24 receiver example #1 ...")
    
    # Connect to pigpiod
    print("Connecting to:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24L01 communication object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    
    # Listen on a bunch of adresses.
    # PLEASE NOTE:
    # ------------
    # Listering on pipe 0 means that we cannot use this transceiver for sending 
    # with acknowledgement as pipe 0 (RF24_RX_ADDR.P0) is the acknowledgement 
    # address when sending.
    nrf.open_reading_pipe(RF24_RX_ADDR.P0, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, [0x02, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P2, [0x03, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P3, [0x04, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P4, [0x05, 0xCE, 0xFA, 0xBE, 0xBA])

    # Wait for device to settle and display the content of device registers.
    time.sleep(0.5)
    nrf.show_registers()

    #
    # Different protocol layouts.
    # protocol=1 (byte), temperature (float), humidity (float)
    # protocol=2 (byte), soil moisture 1 (int), soil moisture 2 (int)
    # protocol=3 (byte), temperature 1 (float), temperature 2 (float)
    #
    protocol_formats = {1: "<Bff", 2: "<Bhh", 3: "<Bff"}

    count = 0
    while True:

        # As long as data is ready for processing, process it.
        while nrf.data_ready():
            # Count message and record time of reception.            
            count += 1
            now = datetime.now()
            
            # Read pipe and payload for message.
            pipe = nrf.data_pipe()
            payload = nrf.get_payload()    

            # Resolve protocol number.
            protocol = payload[0] if len(payload) > 0 else -1            

            hex = ':'.join(f'{i:02x}' for i in payload)

            # Report on message received.
            print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {hex}, count: {count}")
            
            fmt = protocol_formats.get(protocol)
            if fmt is None:
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Unknown protocol {protocol}")
            else:
                try:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: protocol: {protocol}, data: {struct.unpack(fmt, payload)}")
                except:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Exception while unpacking payload of {len(payload)} bytes using {fmt}.")

        # Sleep 500 ms.
        time.sleep(0.5)
