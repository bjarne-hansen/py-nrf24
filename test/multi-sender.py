import argparse
from datetime import datetime
from random import normalvariate
import struct
import sys
import time
import traceback

import pigpio
from nrf24 import *

#
# A simple NRF24L sender that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts sending data on the address specified.  Use the companion program "simple-receiver.py" to receive the data
# from it on a different Raspberry Pi.
#
def tranmission_result(nrf:NRF24):
    if nrf.get_packages_lost() == 0:
        print(f"Success: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")
    else:
        print(f"Error: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")

if __name__ == "__main__":    
    print("Python NRF24 Multiple NRF24L01+ Modules Sender Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="simple-sender.py", description="Multiple NRF24L01+ Modules Sender Example.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address1', type=str, nargs='?', default='1SRVR', help="Address for module #1 to send to (3 to 5 ASCII characters).")
    parser.add_argument('address2', type=str, nargs='?', default='2SRVR', help="Address for module #2 to send to (3 to 5 ASCII characters).")
    
    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address1 = args.address1
    address2 = args.address2

    if not (2 < len(address1) < 6):
        print(f'Invalid address #1 {address1}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    if not (2 < len(address2) < 6):
        print(f'Invalid address #2 {address2}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        sys.exit()

    # Create NRF24 object for module #1 (controlled by CE PIN GPIO 25).
    # PLEASE NOTE: PA level is set to MIN, because test sender/receivers are often close to each other, and then MIN works better.
    nrf1 = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.MIN)
    nrf1.set_address_bytes(len(address1))
    nrf1.open_writing_pipe(address1)

    # Create NRF24 object for module #2 (controlled by CE PIN GPIO 12).
    # PLEASE NOTE: PA level is set to MIN, because test sender/receivers are often close to each other, and then MIN works better.
    nrf2 = NRF24(pi, ce=12, spi_channel=SPI_CHANNEL.AUX_CE2, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.MIN)
    nrf2.set_address_bytes(len(address2))
    nrf2.open_writing_pipe(address2)
    
    
    # Display the content of NRF24L01 device registers.
    print("Registers for module #1:")
    nrf1.show_registers()

    print("Registers for module #2:")
    nrf2.show_registers()

    try:
        print(f'Send to {address1} and {address2}')
        count = 0
        while True:

            # Module #1: Send simulated sensor readings using NRF24L01+
            temperature = normalvariate(23.0, 0.5); humidity = normalvariate(62.0, 0.5)
            payload = struct.pack("<Bff", 0x01, temperature, humidity)
            print(f'Module #1 sensor values: temperature={temperature}, humidity={humidity}')
            nrf1.reset_packages_lost()
            nrf1.send(payload)

            # Module #2: Send simulated sensor readings using NRF24L01+
            temperature = normalvariate(23.0, 0.5); humidity = normalvariate(62.0, 0.5)
            payload = struct.pack("<Bff", 0x01, temperature, humidity)
            print(f'Module #2 sensor values: temperature={temperature}, humidity={humidity}')
            nrf2.reset_packages_lost()
            nrf2.send(payload)

            # Check if message sent via module #1 was successful.
            timeout1 = False
            try:
                nrf1.wait_until_sent()
            except TimeoutError:
                timeout1 = True

            # Check if message sent via module #2 was successful.
            timeout2 = False
            try:
                nrf2.wait_until_sent()
            except TimeoutError:
                timeout2 = True

            # Display results of send operations.
            if not timeout1:
                print("Module #1 Result:")
                tranmission_result(nrf1)
            else:
                print("Module #1 timed out while getting acknowledgement.")
            
            if not timeout1:
                print("Module #2 Result:")
                tranmission_result(nrf2)
            else:
                print("Module #2 timed out while getting acknowledgement.")
                
            # Wait 10 seconds before sending the next reading.
            time.sleep(10)
    except:
        traceback.print_exc()
        nrf1.power_down()
        nrf2.power_down()
        pi.stop()





