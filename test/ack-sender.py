import argparse
from datetime import datetime
from random import normalvariate
import struct
import sys
import time
import traceback
from uuid import UUID

import pigpio
from nrf24 import *

#
# A simple NRF24L sender that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts sending data on the address specified expecting an acknowledgement with a payload.  
# Use the companion program "ack-receiver.py" to receive the data from it on a different Raspberry Pi.
#
if __name__ == "__main__":    
    print("Python NRF24 Sender with Acknowledgement Payload Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="ack-sender.py", description="Simple NRF24 Sender with Acknowledgement Payload.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs='?', default='1ACKS', help="Address to send to (3 to 5 ASCII characters).")
    
    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    if not (2 < len(address) < 6):
        print(f'Invalid address {address}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.ACK, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.set_address_bytes(len(address))
    nrf.set_retransmission(5, 15)
    nrf.open_writing_pipe(address)

    # Show registers.
    nrf.show_registers()

    try:
        # Enter a loop sending data to the address specified.
        print(f"Send data to: {address}")
        while True:

            # Emulate that we read temperature and humidity from a sensor, for example
            # a DHT22 sensor.  Add a little random variation so we can see that values
            # sent/received fluctuate a bit.
            temperature = normalvariate(23.0, 0.5)
            humidity = normalvariate(62.0, 0.5)
            print(f'Sensor values: temperature={temperature}, humidity={humidity}')

            # Pack temperature and humidity into a byte buffer (payload) using a protocol 
            # signature of 0x01 so that the receiver knows that the bytes we are sending 
            # are a temperature and a humidity (see "simple-receiver.py").
            payload = struct.pack("<Bff", 0x01, temperature, humidity)

            # Send the payload to the address specified above.
            nrf.reset_packages_lost()
            nrf.send(payload)            
            try:
                nrf.wait_until_sent()
            except TimeoutError:
                print("Timeout waiting for transmission to complete.")
                continue

            if nrf.get_packages_lost() == 0:
                # The package we sent was successfully received by the server.
                print(f"Success: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")

                # Check if an acknowledgement package is available.
                if nrf.data_ready():
                    # Get payload.
                    pipe = nrf.data_pipe()
                    payload = nrf.get_payload()

                    # If the payload is 4 bytes, we expect it to be an acknowledgement payload.
                    if len(payload) == 4:
                        (next_id, ) = struct.unpack('<I', payload)
                    else:
                        next_id = -1

                    # We have received some bytes ...
                    print(f'Received: payload={":".join(f"{c:02x}" for c in payload)}, next_id={next_id}')
                
                else:
                    # No acknowledgement package seems to be available.
                    print('No acknowledgement package.')
            else:
                # The package we sent was lost.
                print(f"Error: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")

            # Wait 10 seconds before sending the next reading.
            time.sleep(10)

    except Exception as e:
        traceback.print_exc()
        nrf.power_down()
        pi.stop()





