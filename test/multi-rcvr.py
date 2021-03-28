import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env

#
# This example shows how to use more than one NRF24L01 transceiver module for receiving
# data. Each module must be wired on their own set of SPI pins on the Raspberry.
# Please refer to https://github.com/bjarne-hansen/py-nrf24 for further details.
#

#
# Function to receive data from a specific NRF24L01 module specified as parameter.
#
def receive_data(nrf):
    
    while nrf.data_ready():

        # Data is availble for reading, get a timestamp.
        now = datetime.now()        

        # Get the pipe that data was received on. This can be "translated" to the address
        # if you need to know what address the data was sent to.
        pipe = nrf.data_pipe()

        # Get the payload.
        payload = nrf.get_payload()

        # Ignore empty payloads.
        if len(payload) == 0:
            return

        # Display information about the message received.
        hex = ':'.join(f'{i:02x}' for i in payload)
        print(f"{now:%Y-%m-%d %H:%M:%S.%f}: tranceiver: {nrf.tranceiver}, pipe: {pipe}, len: {len(payload)}, bytes: {hex}")


if __name__ == "__main__":

    # Show who we are ...
    print("Python NRF24L01 multi-receiver example.")
    
    # Connect to pigpiod.
    print("Connecting to:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create transceiver #1 using GPIO 25 as CE.
    nrf1 = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf1.set_pa_level(RF24_PA.MIN)
    nrf1.open_writing_pipe([0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P1, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P2, [0x02, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P3, [0x03, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P4, [0x04, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P5, [0x05, 0xCE, 0xFA, 0xBE, 0xBA])

    # Store an attribute on the NRF24 object stating what transceiver it is ... a little dirty ...
    nrf1.tranceiver = "#1"

    # Create transceiver #1 using GPIO 12 as CE.
    nrf2 = NRF24(pi, ce=12, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, spi_channel=SPI_CHANNEL.AUX_CE2)
    nrf2.set_pa_level(RF24_PA.MAX)
    nrf2.open_writing_pipe([0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P1, [0x06, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P2, [0x07, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P3, [0x08, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P4, [0x09, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P5, [0x0A, 0xCE, 0xFA, 0xBE, 0xBA])

    # Store an attribute on the NRF24 object stating what transceiver it is ... a little dirty ...
    nrf2.tranceiver = "#2"

    # Show registers for both transceivers.
    nrf1.show_registers()
    nrf2.show_registers()

    # Run a loop receiving data from both of the transceivers.
    while True:
        receive_data(nrf1)
        receive_data(nrf2)
