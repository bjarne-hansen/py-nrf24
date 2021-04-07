import argparse
from datetime import datetime
import struct
import sys
import time
import traceback
from uuid import uuid4

import pigpio
from nrf24 import *

#
# A simple NRF24L receiver that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts receiving data on the address specified sending a continiously increasing integer as acknowledgement payload.  
# Use the companion program "ack-sender.py" to send data to it from a different Raspberry Pi.
#
if __name__ == "__main__":

    print("Python NRF24 Receiver with Acknowledgement Payload Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="ack-receiver.py", description="Simple NRF24 Receiver with Acknowledgement Payload.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs='?', default='1ACKS', help="Address to listen to (3 to 5 ASCII characters).")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    # Verify that address is between 3 and 5 characters.
    if not (2 < len(address) < 6):
        print(f'Invalid address {address}. Addresses must be between 3 and 5 ASCII characters.')
        sys.exit(1)
    
    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        exit()

    # Create NRF24L01 communication object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.ACK, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.set_address_bytes(len(address))

    # Listen on the address specified as parameter
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, address)
    
    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    # Set the UUID that will be the payload of the next acknowledgement.
    next_id = 1
    nrf.ack_payload(RF24_RX_ADDR.P1, struct.pack('<I', next_id))
    
    try:
        # Enter a loop receiving data on the address specified.
        print(f'Receive data on {address}')
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

                # Hex the payload received.
                hex = ':'.join(f'{i:02x}' for i in payload)

                # Show message received as hex.
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {hex}, count: {count}, next_id={next_id}")

                # If the length of the message is 9 bytes and the first byte is 0x01, then we try to interpret the bytes
                # sent as an example message holding a temperature and humidity.
                if len(payload) == 9 and payload[0] == 0x01:
                    
                    values = struct.unpack("<Bff", payload)
                    print(f'Protocol: {values[0]}, temperature: {values[1]}, humidity: {values[2]}')
                    
                    # Set uuid that will be part of the next acknowledgement.
                    next_id += 1
                    nrf.ack_payload(RF24_RX_ADDR.P1, struct.pack('<I', next_id))
                
            # Sleep 1 ms.
            time.sleep(0.001)

    except:
        traceback.print_exc()
        nrf.power_down()
        pi.stop()
