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
# starts receiving data on the address specified.  Use the companion program "simple-sender.py" to send data to it from
# a different Raspberry Pi.
#
if __name__ == "__main__":

    print("Python NRF24 Multiple NRF24L01+ Modules Receiver Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="multi-receiver.py", description="Multiple NRF24L01+ Modules Receiver Example.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address1', type=str, nargs='?', default='1SRVR', help="Address for module #1 to listen to (3 to 5 ASCII characters).")
    parser.add_argument('address2', type=str, nargs='?', default='2SRVR', help="Address for module #2 to listen to (3 to 5 ASCII characters).")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address1 = args.address1
    address2 = args.address2

    # Verify that address is between 3 and 5 characters.
    if not (2 < len(address1) < 6):
        print(f'Invalid address {address1} for module #1. Addresses must be between 3 and 5 ASCII characters.')
        sys.exit(1)
    
    # Verify that address is between 3 and 5 characters.
    if not (2 < len(address2) < 6):
        print(f'Invalid address {address2} for module #2. Addresses must be between 3 and 5 ASCII characters.')
        sys.exit(1)
    
    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        sys.exit()

    # Create NRF24 object for module #1.
    # PLEASE NOTE: PA level is set to MIN, because test sender/receivers are often close to each other, and then MIN works better.
    nrf1 = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.MIN)
    nrf1.set_address_bytes(len(address1))
    nrf1.open_reading_pipe(RF24_RX_ADDR.P1, address1)
    
    # Create NRF24 object for module #1.
    # PLEASE NOTE: PA level is set to MIN, because test sender/receivers are often close to each other, and then MIN works better.
    # PLEASE NOTE: Using a different CE PIN and SPI_CHANNEL. See https://pinout.xyz/pinout/spi#
    nrf2 = NRF24(pi, ce=12, spi_channel=SPI_CHANNEL.AUX_CE2, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.MIN)
    nrf2.set_address_bytes(len(address2))
    nrf2.open_reading_pipe(RF24_RX_ADDR.P1, address2)

    # Display the content of NRF24L01 device registers.
    print("Registers for module #1:")
    nrf1.show_registers()

    print("Registers for module #2:")
    nrf2.show_registers()

    # Enter a loop receiving data on the address specified.
    try:
        print(f'Receive from {address1} and {address2}')
        count1 = 0; count2 = 0
        while True:

            # As long as data is ready for processing, process it.
            if nrf1.data_ready():
                # Count message and record time of reception.            
                count1 += 1
                now = datetime.now()
                
                # Read pipe and payload for message.
                pipe = nrf1.data_pipe()
                payload = nrf1.get_payload()    

                # Resolve protocol number.
                protocol = payload[0] if len(payload) > 0 else -1            

                hex = ':'.join(f'{i:02x}' for i in payload)

                # Show message received as hex.
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Module #1 - pipe={pipe}, len={len(payload)}, bytes={hex}, count={count1}")

                # If the length of the message is 9 bytes and the first byte is 0x01, then we try to interpret the bytes
                # sent as an example message holding a temperature and humidity sent from the "simple-sender.py" program.
                if len(payload) == 9 and payload[0] == 0x01:
                    values = struct.unpack("<Bff", payload)
                    print(f'Module #1: protocol={values[0]}, temperature={values[1]}, humidity={values[2]}')
                
            # As long as data is ready for processing, process it.
            if nrf2.data_ready():
                # Count message and record time of reception.            
                count2 += 1
                now = datetime.now()
                
                # Read pipe and payload for message.
                pipe = nrf2.data_pipe()
                payload = nrf2.get_payload()    

                # Resolve protocol number.
                protocol = payload[0] if len(payload) > 0 else -1            

                hex = ':'.join(f'{i:02x}' for i in payload)

                # Show message received as hex.
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Module #2 - pipe={pipe}, len={len(payload)}, bytes={hex}, count={count2}")

                # If the length of the message is 9 bytes and the first byte is 0x01, then we try to interpret the bytes
                # sent as an example message holding a temperature and humidity sent from the "simple-sender.py" program.
                if len(payload) == 9 and payload[0] == 0x01:
                    values = struct.unpack("<Bff", payload)
                    print(f'Module #2: protocol={values[0]}, temperature: {values[1]}, humidity: {values[2]}')
            
    except:
        traceback.print_exc()
        nrf1.power_down()
        nrf2.power_down()
        pi.stop()
