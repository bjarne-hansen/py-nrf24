# nrf24 for Python

**PLEASE NOTE**: The new version 2.0.0 contains **breaking** changes compared to previous version 1.1.1.  Please make sure to consult the `CHANGES.md` for details.

This package implements 2.4Ghz communication using NRF24L01 modules on a Raspberry Pi using Python via the pigpio daemon.

The code is based on a modified version of some example code found on [StackExchange](https://raspberrypi.stackexchange.com/questions/77290/nrf24l01-only-correctly-retrieving-status-and-config-registers).  The author of the original code is also the author of the ```pigpio``` library found here http://abyz.me.uk/rpi/pigpio/.

I have obtained the original authors approval to modify and distribute the code anyway I want.  So, I have created a very basic Python package and published it on PyPI under a MIT license.

The ```nrf24``` packages depends on the ```pigpio``` package that is available via PyPI as well.

For further information please refer to the github project page at https://github.com/bjarne-hansen/py-nrf24.

