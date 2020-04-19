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
    print("Python NRF24 Receiver 02")
    
    # Connect to pigpiod
    pi = pigpio.pi("pizw03.conspicio.dk")
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24L01 communication object.
    # nrf = NRF24.NRF24(pi, ce=25, payload_size=15, channel=1, crc_bytes=2)
    nrf = NRF24(pi, ce=12, payload_size=RF24_PAYLOAD.PAYLOAD_DYNAMIC_PAYLOAD, channel=1, crc_bytes=2,
                spi_channel=SPI_CHANNEL.CHANNEL_AUX_CE2)
    
    # Configure NRF24 transceiver to communicate at 250 KBPS ob channel 1 accepting dynamic payload sizes (1-32 bytes).
    nrf.set_data_rate(RF24_DATA_RATE.DATA_RATE_250KBPS)
    nrf.open_writing_pipe("SM105")
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, "GW001")
    
    # Wait for device to settle and display the content of device registers.
    time.sleep(0.5)
    nrf.show_registers()

    protocol_formats = {0: "<Bhhh", 1: "<BHHHff", 2: "<Bhh", 3: "<Bff"}

    count = 0
    while True:

        # As long as data is ready for processing, process it.
        while nrf.data_ready():
            pipe = nrf.data_pipe()
            count += 1
            now = datetime.now()
            payload = nrf.get_payload()    
            pls = bytes_to_hex(payload)
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
