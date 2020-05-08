import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env

if __name__ == "__main__":
    #
    # Example receiving date/time information using NRF24.
    #
    print("Python NRF24 date/time receiver.")

    # Connecto to a pigpio daemon.
    print("Connecting to Raspberry:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24 object.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf.open_reading_pipe(1, "DTCLI")

    # We only look for the date/time protocol (0xfe)
    protocol_formats = {0xfe: "<B4sHBBBBBB"}

    count = 0
    while True:

        # As long as data is ready for processing, process it.
        while nrf.data_ready():
            pipe = nrf.data_pipe()
            count += 1
            now = datetime.now()
            payload = nrf.get_payload()    
            pls = ':'.join(f'{i:02x}' for i in payload)
            protocol = payload[0]

            print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {pls}, count: {count}")
            
            fmt = protocol_formats.get(protocol)
            if fmt is None:
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Unknown protocol {payload[0]}")
            else:
                try:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: protocol: {protocol}, data: {struct.unpack(fmt, payload)}")
                except:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Exception while unpacking payload of {len(payload)} bytes using {fmt}.")

        # Sleep 500 ms.
        time.sleep(0.5)
