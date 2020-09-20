import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env


def receive_data(nrf):
    
    while nrf.data_ready():
        now = datetime.now()        
        pipe = nrf.data_pipe()
        payload = nrf.get_payload()
        if len(payload) == 0:
            return
        hex = ':'.join(f'{i:02x}' for i in payload)
        print(f"{now:%Y-%m-%d %H:%M:%S.%f}: tranceiver: {nrf.tranceiver}, pipe: {pipe}, len: {len(payload)}, bytes: {hex}")


if __name__ == "__main__":

    print("Basic Python NRF24 Receiver.")
    
    # Connect to pigpiod
    print("Connecting to:", env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    pi = pigpio.pi(env.get('PIGPIO_HOST', 'localhost'), env.get('PIGPIO_PORT', 8888))
    if not pi.connected:
        print("Not connected to Raspberry PI...goodbye.")
        exit()

    # Create NRF24L01 communication object.
    # On a Raspberry Pi with multiple nrf24l01 transceiver modules we can use one or the other.  Actually, several can be installed and used.
    # Please refer to https://pinout.xyz/pinout/spi for information on SPI0: CE0 and CE1, SPI1: CE0, CE1, and CE2 (up to 5 in total).
     
    nrf1 = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS)
    nrf1.set_pa_level(RF24_PA.LOW)
    nrf1.open_reading_pipe(RF24_RX_ADDR.P1, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf1.tranceiver = "#1"

    nrf2 = NRF24(pi, ce=12, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, spi_channel=SPI_CHANNEL.AUX_CE2)
    nrf2.set_pa_level(RF24_PA.LOW)
    nrf2.open_reading_pipe(RF24_RX_ADDR.P1, [0x02, 0xCE, 0xFA, 0xBE, 0xBA])
    nrf2.tranceiver = "#2"

    time.sleep(0.5)
    nrf1.show_registers()
    nrf2.show_registers()

    while True:
        receive_data(nrf1)
        receive_data(nrf2)
