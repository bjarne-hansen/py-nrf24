# nrf24 for Python

This package implement 2.4Ghz communication using NRF24L01 modules on a Raspberry Pi using Python.

The code is based on a modified version of some example code found on [StackExchange](https://raspberrypi.stackexchange.com/questions/77290/nrf24l01-only-correctly-retrieving-status-and-config-registers).

The original author is the author of the pigpio library found here http://abyz.me.uk/rpi/pigpio/.

I have obtained the original authors approval to modify and distribute the code anyway I want.  So, I have created a very basic Python package and published it on PyPI under a MIT license.

The ```nrf24``` packages depends on the ```pigpio``` package that is available via PyPI as well.

## Installing

    pip install nrf24

## Example

Creating a simple listener running on the same host (localhost) as the pigpiod daemon (Raspberry Pi).  You may run this on a laptop connecting remotely to the Raspberry Pi, if your pigpiod has been configured for remote access.

    import pigpio
    import nrf24

    pi = pigpio.pi("localhost")

    #
    # CE PIN = 25.
    # Payload size = dynamic.
    # Data rate = 1 Mbps.
    # Channel = 76.
    # SPI channel = MAIN_CE0.
    #
    # Raspberry Wiring:
    #
    #
    #
    radio = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC)

    radio.open_reading_pipe(RF24_RX_ADDR.P1, [0x01, 0xCE, 0xFA, 0xBE, 0xBA])

    while True:
        while radio.data_ready(): 
            pipe = radio.data_pipe()
            payload = radio.get_payload()
            hex = ':'.join(f'{i:02x}' for i in payload)
            print(f'Data received on pipe {pipe}: {hex}')

More examples can be found in the ```/test``` folder of the project.
    


