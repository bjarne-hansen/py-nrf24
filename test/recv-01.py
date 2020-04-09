import pigpio
from nrf24.nrf24 import NRF24

if __name__ == "__main__":
    print("Python NRF24 Receiver 01")

    hostname = "pizw03"
    port = 8888
    show_errors = True

    ce_pin = 25
    payload_size = NRF24.DYNAMIC_PAYLOAD
    channel = 100
    crc_bytes = 2

    # Connect to raspberry pi
    pi = pigpio.pi(hostname, port, show_errors)
    if not pi.connected:
        print(f'Not connected to Raspberry Pi at {hostname}.')
        exit()

    # Configure NRF24L01
    nrf = NRF24(pi, ce=ce_pin, payload_size=payload_size, channel=channel, crc_bytes=crc_bytes)


