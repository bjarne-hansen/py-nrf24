import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct


def bytes_to_hex(b):
    s = ''
    for i, v in enumerate(b):
        s += f'{":" if i > 0 else ""}{v:02x}'
    return s

if __name__ == "__main__":
    print("Python NRF24 Receiver 01")
    
    # Connect to pigpiod
    pi = pigpio.pi("pizw03.conspicio.dk")
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24L01 communication object.
    # nrf = NRF24.NRF24(pi, ce=25, payload_size=15, channel=1, crc_bytes=2)
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.PAYLOAD_DYNAMIC_PAYLOAD, channel=100, data_rate=RF24_DATA_RATE.DATA_RATE_250KBPS)
    # nrf = NRF24.NRF24(pi, ce=25)

    # Configure NRF24 transceiver to communicate at 250 KBPS ob channel 1 accepting dynamic payload sizes (1-32 bytes).
    #nrf.set_payload_size(RF24_PAYLOAD.PAYLOAD_DYNAMIC_PAYLOAD)  # duplicate
    #nrf.set_channel(1)                                          # duplicate
    #nrf.set_crc_bytes(2)                                        # duplicate
    #nrf.set_data_rate(RF24_DATA_RATE.DATA_RATE_250KBPS)         

    # nrf.set_local_address("GW003")      # RX_ADDR_P1
    # nrf.set_remote_address("BABE1")     # RX_ADDR_P0, TX_ADDR
    # nrf.open_writing_pipe("3GW00")      # RX_ADDR_P0, TX_ADDR
    # nrf.open_reading_pipe(0, "0EBAB")

    # nrf.open_reading_pipe(RF24_RX_ADDR.P0, "0BABE")
    # nrf.open_reading_pipe(RF24_RX_ADDR.P1, "1BABE")
    # nrf.open_reading_pipe(RF24_RX_ADDR.P2, "2BABE")
    # nrf.open_reading_pipe(RF24_RX_ADDR.P3, "3BABE")
    # nrf.open_reading_pipe(RF24_RX_ADDR.P4, "4BABE")
    # nrf.open_reading_pipe(RF24_RX_ADDR.P5, "5BABE")
    
    #nrf.set_channel(100)
    nrf.open_reading_pipe(RF24_RX_ADDR.P0, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, [0x02, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P2, [0x03, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P3, [0x04, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P4, [0x05, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf.open_reading_pipe(RF24_RX_ADDR.P5, [0x06, 0xCE, 0xFA, 0xBE, 0xBA])


    # Wait for device to settle and display the content of device registers.
    time.sleep(0.5)
    nrf.show_registers()

    protocol_formats = {0: "<Bhhh", 1: "<Bff", 2: "<Bhh", 3: "<Bff"}

    count = 0
    while True:

        # As long as data is ready for processing, process it.
        while nrf.data_ready():
            pipe = nrf.data_pipe()
            count += 1
            now = datetime.now()
            payload = nrf.get_payload()    
            pls = bytes_to_hex(payload)
            if len(payload) > 0:
                protocol = payload[0]
            else:
                protocol = -1

            print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {pls}, count: {count}")
            
            fmt = protocol_formats.get(protocol)
            if fmt is None:
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Unknown protocol {protocol}")
            else:
                try:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: protocol: {protocol}, data: {struct.unpack(fmt, payload)}")
                except:
                    print(f"{now:%Y-%m-%d %H:%M:%S.%f}: Exception while unpacking payload of {len(payload)} bytes using {fmt}.")

        # Sleep 500 ms.
        time.sleep(0.5)
