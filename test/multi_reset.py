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

    # Create transceiver #1 using GPIO 25 as CE.
    nrf1 = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf1.open_reading_pipe(RF24_RX_ADDR.P1, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P2, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P3, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P4, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_reading_pipe(RF24_RX_ADDR.P5, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf1.open_writing_pipe([0x00, 0x00, 0x00, 0x00, 0x00])

    # Create transceiver #1 using GPIO 12 as CE.
    nrf2 = NRF24(pi, ce=12, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, spi_channel=SPI_CHANNEL.AUX_CE2)
    nrf2.open_reading_pipe(RF24_RX_ADDR.P1, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P2, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P3, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P4, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_reading_pipe(RF24_RX_ADDR.P5, [0x00, 0x00, 0x00, 0x00, 0x00])
    nrf2.open_writing_pipe([0x00, 0x00, 0x00, 0x00, 0x00])

    nrf1.show_registers()
    nrf2.show_registers()
    