import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
import argparse
import sys
from uuid import uuid4
import random

#
# A simple NRF24L receiver that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts receiving data on the address specified. For each request, a response message is returned.  
# Use the companion program "rr-client.py" to send requests and receive responses from this server.
#
if __name__ == "__main__":

    print("Python NRF24 Request/Response Server Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="rr-server.py", description="Simple NRF24 Request/Response Server.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs='?', default='1SRVR', help="Address to listen to (3 to 5 ASCII characters).")

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
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.set_address_bytes(len(address))

    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    # Enter a loop receiving data on the address specified.
    count = 0
    while True:
        
        # Listen on the address specified as parameter
        nrf.open_reading_pipe(RF24_RX_ADDR.P1, address)
    
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
            
            # We expect the request to be a message with a 2 byte "command", and a 6 byte char[] reply-to address.
            if len(payload) == 8:

                command, reply_to = struct.unpack("<H6p", payload)
                print(f'Request: command: 0x{command:02x}, reply address={reply_to}.')

                if command == 0x01:
                    # Command 0x01: Get UUID
                    
                    # Generate new UUID
                    uuid = uuid4()

                    # Pack payload response to command 0x01.
                    response = struct.pack('<H16p', 0x01, uuid.bytes)

                elif command == 0x02:
                    # Command 0x02: Get state of relay

                    # In this example we just select a random on/off state of the relay. In a real application we
                    # would determine the state of the relay from a GPIO PIN.
                    state = random.choice([True, False])
                    
                    # Pack payload response to command 0x02
                    response = struct.pack('<H?', 0x02, state)
                
                else:
                    # If we received a command that was not 0x01 or 0x02, just return response with that command
                    # and no additional payload.
                    response = struct.pack('<H', command)

                # Send response back.
                print(f'Response: reply_to={reply_to}, response={":".join(f"{i:02x}" for i in payload)}')

                # Open the writing pipe of the response address.
                nrf.open_writing_pipe(reply_to)

                nrf.reset_packages_lost()
                nrf.send(response)
                while nrf.is_sending():
                    time.sleep(0.0004)

                if nrf.get_packages_lost() == 0:
                    print(f'Success: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}')
                else:
                    print(f'Error: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}')
            else:
                print('Invalid request. No response sent.')

        # Sleep 1 ms.
        time.sleep(0.001)
