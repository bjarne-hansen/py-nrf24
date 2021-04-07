import argparse
from datetime import datetime
import struct
import sys
import time
import traceback

import pigpio
from nrf24 import *

#
# A simple NRF24L receiver that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts receiving data on the two addresses. The first address used a fixed payload size, and the second address uses
# a dynamic payload size.  
# Use the companion program "mixed-sender.py" to send data to it from a different Raspberry Pi.
# 
if __name__ == "__main__":

    print("Python NRF24 Mixed Receiver Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="mixed-receiver.py", description="Simple NRF24 Receiver with Mixed Payload Sizes.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs=2, help="Address to receive on (5 ASCII characters)")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    if not (len(address[0]) == 5): 
        print(f'Invalid address {address[0]}. Address must be 5 ASCII characters long.')
        sys.exit(1)

    if not (len(address[1]) == 5): 
        print(f'Invalid address {address[1]}. Address must be 5 ASCII characters long.')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        sys.exit()

    # Create NRF24L01 communication object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)

    # Listen of first address with 9 bytes as payload size.
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, address[0], size=9)

    # Listen on second address with dynamic payload size.
    nrf.open_reading_pipe(RF24_RX_ADDR.P2, address[1], size=RF24_PAYLOAD.DYNAMIC)

    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    # Enter a loop receiving data on the address specified.
    try:
        print(f'Receive on {address[0]} (fixed) and {address[1]} (dynamic)')
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

                # Show message received as hex.
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {hex}, count: {count}")

                # If the length of the message is 9 bytes and the first byte is 0x01, then we try to interpret the bytes
                # sent as an example message holding a temperature and humidity sent from the "simple-sender.py" program.
                if len(payload) == 9 and payload[0] == 0x01:
                    values = struct.unpack("<Bff", payload)
                    print(f'Protocol: {values[0]}, temperature: {values[1]}, humidity: {values[2]}')
                else:
                    print(f'Dynamic message: pipe: {pipe}, len: {len(payload)}')
                
            # Sleep 100 ms.
            time.sleep(0.1)
    except:
        traceback.print_exc()
        nrf.power_down()
        pi.stop()
