import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
import argparse
import sys

#
# A simple NRF24L01 receiver script that receives data on 6 different addresses
# and prints result on screen.  Please note that this receiver emulates a 
# small NRF24L01 gateway which looks at the first byte in the payload to determine
# what data is being sent.
#

if __name__ == "__main__":

    print("Python NRF24 Simple Receiver Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="simple-receiver.py", description="Simple NRF24 receiver.")
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

    # Create NRF24L01 communication object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    
    # Listen on the address specified as parameter
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, )
    
    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    #
    # We use a protocol layout together with the Python "struct" pack/unpack
    # feature to deserialize bytes into values.
    #
    # The first byte of a payload is expected to be a value that tells us
    # what "protocol" we are using, ie. how the following bytes are structured.
    #
    # In this simple example we use 3 different protocol layouts.
    #
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

        # Sleep 100 ms.
        time.sleep(0.1)
