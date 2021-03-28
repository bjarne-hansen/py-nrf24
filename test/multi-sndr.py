import pigpio
import time
from datetime import datetime
from nrf24 import *
from os import environ as env

#
# A sender script alternating to send data to two different addresses.  This can be
# used to test the test/multi-rcvr.py script which shows how to receive data using
# multiple NRF24L01 modules.
#
if __name__ == "__main__":

    # Tell what we are ...
    print("Python NRF24L01 multi-sender example ...")

    # Establish connection to the pigpiod daemon.
    print("Connecting to:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)

    # Define addresses to send to (see test/multi-rcvr.py).
    addresses = [
        [0x01, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #1, Pipe #1 
        [0x06, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #2, Pipe #1
        [0x02, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #1, Pipe #2
        [0x07, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #2, Pipe #2
        [0x03, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #1, Pipe #3
        [0x08, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #2, Pipe #3
        [0x04, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #1, Pipe #4
        [0x09, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #2, Pipe #4
        [0x05, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #1, Pipe #5
        [0x0A, 0xCE, 0xFA, 0xBE, 0xBA],     # Module #2, Pipe #5
        ]
    
    # Show configuration.
    nrf.show_registers()

    # Start by sending to the address at index 0.
    address_index = 0
    
    while True:

        # Get the address we want to send to next.
        address = addresses[address_index]
        
        # Open a writing pipe for the address specified.
        nrf.open_writing_pipe(address)
        
        nrf.show_registers()

        # Prepare a boring payload.
        payload = [0xDE, 0xAD, 0xBE, 0xEF, address_index]

        # Get timestamp, convert address to hex, convert payload to hex and print message. 
        now = datetime.now()
        addr_hex = ':'.join(f'{i:02x}' for i in address)
        payload_hex = ':'.join(f'{i:02x}' for i in payload)
        print(f"{now:%Y-%m-%d %H:%M:%S.%f}: address: {addr_hex}, bytes: {len(payload)}, payload: {payload_hex}")
            
        # Send the payload.
        nrf.send(payload)
        
        # Get index of next address (wrap and start over if index surpasses last address).
        address_index = (address_index + 1) % len(addresses)
        
        # Wait some seconds before sending the next message.
        time.sleep(5)
        