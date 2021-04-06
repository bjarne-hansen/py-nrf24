import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
from random import normalvariate
import argparse
import sys
import random
from uuid import UUID

#
# A simple NRF24L client that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts sending request to a remote server expecting to receive a reply from it (client/server).
# Use the companion program "rr-server.py" to provide the server functionality.
#
if __name__ == "__main__":    
    print("Python NRF24 Request/Reply Client Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="rr-client.py", description="Simple NRF24 Request/Reply Client.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('client', type=str, nargs='?', default='1CLNT', help="Address of this client (3 to 5 ASCII characters).")
    parser.add_argument('server', type=str, nargs='?', default='1SRVR', help="Address of server (3 to 5 ASCII characters).")
    
    
    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    client = args.client
    server = args.server

    if not (2 < len(client) < 6):
        print(f'Invalid client address {client}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    if not (2 < len(server) < 6):
        print(f'Invalid server address {server}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    if len(client) != len(server):
        print(f'Invalid client ({client}) and server ({server}) address, they must be same length.')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.set_address_bytes(len(client))

    # Open the server address as a writing pipe (request).
    nrf.open_writing_pipe(server)

    # Open the client address as a reading pipe (response). 
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, client)
    
    nrf.show_registers()

    count = 0
    while True:

        # Pick a random command to send to the server.
        command = random.choice([0x01, 0x02])

        # Pack the request.
        request = struct.pack('<H6p', command, bytes(client, 'ascii'))
        print(f'Request: command={command}, reply_to={client}, {":".join(f"{c:02x}" for c in request)}')
        
        # Send the request.

        nrf.reset_packages_lost()
        nrf.send(request)
        while nrf.is_sending():
            time.sleep(0.0004)
        if nrf.get_packages_lost() == 0:
            print(f'Success: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}')
        else:
            print(f'Error: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}')

        if nrf.get_packages_lost() == 0:
            # If we successfully sent a request, we expect to receive a response.
            reply_start = time.monotonic()
            while True:                    

                if nrf.data_ready():
                    response = nrf.get_payload()

                    if response[0] == 0x01:
                        # The response is a response to a 0x01 command.
                        command, uuid_bytes = struct.unpack('<H16p', response)
                        uuid = UUID(bytes=uuid_bytes)
                        print(f'Response: command={command}, uuid={uuid}')

                    elif response[0] == 0x02:
                        # The response is a response to a 0x01 command.
                        command, relay = struct.unpack('<H?', response)
                        print(f'Response: command={command}, relay on={relay}')

                    else:
                        # Invalid response.
                        print('Invalid response received.')

                if time.monotonic() - reply_start > 1:
                    # If we have waited more than 1 second on a response, we time out. 
                    # This obviously depends on the application.
                    print('Timeout waiting for response.')
                    break
    
        # Wait 10 seconds before sending the next request.
        print('Wait 10 seconds before sending new request.')
        time.sleep(10)





