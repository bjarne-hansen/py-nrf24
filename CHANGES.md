# Changelog

This is the the change log for the NRF24 project.

## Version 2.0.0

Version 2.0.0 has breaking changes compared to version 1.1.1 which was the previous version released to pypi.org.
Please make sure to continue to use version 1.1.1, or please make the necessary changes to comply with the new API.

This release also have an updated set of test / example programs in the `/test` folder. Make sure to consult those
as well.

### Breaking Changes


* **Removed** `set_local_address(address)` which is basically a way to do the same as `open_reading_pipe(RF24_RX_ADDR.P1, address)` so it has been removed to consolidate the code a bit.

* **Removed** `set_remote_address(address)` which is basically a way to do the same as `open_writing_pipe(address)`so it has been removed to consolidate the code a bit.

* **Removed** `from_config(...)` that supported reading configuration from a `ConfigParser` instance. Since different projects usually wants different ways of doing configuration, this function seemed most of all like dead code walking.

* **Changed** `open_writing_pipe(address)` so that it does NOT pad addresses anymore.  This means that you must provide an address of the same length as what has been specified in the `set_address_bytes(size)` function. If the size of the address does not match an exception is raised.  Please refer to the new `make_address()` method which is used to check addresses.

* **Changed** `open_reading_pipe(pipe, address)` so that it does NOT pad addresses anymore.  This means that you must provide an address of the same length as what has been specified in the `set_address_bytes(size)` function. If the size of the address does not match an exception is raised.  Please refer to the new `make_address()` method which is used to check addresses.

### Other Changes

* **Added** `make_address(address)` which take an address argument and converts it to a list of bytes to be used when updating addresses in the NRF24L01 module. The `make_address()` method is using in `open_reading_pipe()` and `open_writing_pipe()` to ensure correct addresses are specified.  For flexibility you can specify a string (Python `str`) of ASCII characters, Python `bytes` or `bytearray`, a Python `list` of integers (0 <= n < 256) or a Python `int` which will be converted to bytes using  `address.to_bytes(width, 'little')`. This means that all the following addresses are valid (assuming a 5 byte address width):

    * `'1SNSR'` - string of ASCII characters.

    * `b'\x01SNSR'` or `bytes('1SNSR', 'ascii')` - bytes.

    * `bytearray('1SNSR', 'ascii')` - byte array.

    * `[1, 83, 78, 83, 82]` or `[49, 83, 78, 83, 82]` - list of integers.

    * `0xDEADBEEF01` - integer which will be encoded as `[1, 239, 190, 173, 222]`. Notice the byte value `1` at the first position in the array. This is because the integer is converted as little endian.

* **Added** `get_writing_address()` which returns the transmission address as `bytes`.

* **Added** `get_reading_address(pipe)` which returns the reception address as bytes.  **PLEASE NOTE**: When returning addresses for P2, P3, P4, and P4, the address of P1 is first read and the first byte is replaced by the one-byte address of P2, P3, P4, or P5. After that the byte array is truncated to the width of the address as set by `set_address_bytes()`.

* **Added** `get_retries()` which returns the number of retries for the last sent package. The maximum number of retries can be set with the new `set_retransmission` method. See below.

* **Added** `get_packages_lost()` which returns the number of packages lost since the `PLOS_CNT` in the `OBSERVE_TX` register was last reset.  You can reset the value before sending by using the new method `reset_packages_lost()` method, and then check if it is greater than 0 after transmission to see if your package was lost.

* **Added** `reset_packages_lost()` which resets the `PLOS_CNT` of the `OBSERVE_TX` register.

* **Added** `close_reading_pipe(pipe)` which closes the pipe specified for reception of packages until it is reopened. **PLEASE NOTE** If you close the P0 RX address you will not be able to get acknowledgements for packages sent until you call `open_writing_pipe(address)` again, or you call `open_reading_pipe(RF24_RX_ADDR.P0, address)` where `address` is the address of the writing pipe.

* **Added** `close_all_reading_pipes()` which closes all reading pipes, including P0 which is used for receiving acknowledgements for packages sent. See above.

* **Added** `reset_reading_pipes()` which disable reading from address specified for P2, P3, P4, and P5, while P0 and P1 are kept open.

* **Added** `get_channel()` which returns the channel the NRF24L01 module is communicating on.

* **Added** `get_address_bytes()` which returns the number of significant bytes in addresses.

* **Added** `get_crc_bytes()` which returns the number of CRC bytes used.  The number of CRC bytes can be set using `set_crc_bytes(crc_bytes)` with `RF24_CRC.DISABLED`, `RF24_CRC.BYTES_1`, or `RF24_CRC.BYTES_2` as valid values.

* **Added** `get_data_rate()` which returns the current data rate as a `RF24_DATA_RATE` enumeration value.

* **Added** `set_retransmission(delay, count)` that sets the retransmission properties of the NRF24L01 module. The `delay` parameter accepts values between 0 and 15 and determining the delay between retransmissions.  The delay is calculated as `(delay + 1) * 250` yielding a value between 250 µs and 4000 µs (4 ms.). The `count` parameter accepts a value between 0 and 15 and determins the number of retransmissions attempted.  The default value set is 1 and 15 giving up to 15 retransmissions with a 500 µs delay between each retransmission.

* **Added** `get_retransmission()` returning a (delay, count) tuple for the current retransmission configuration. See details above.

* **Added** `disable_crc()` which disables the use of CRC. This is the same as calling `set_crc_bytes(RF24_CRC.DISABLED)`. 

* **Added** `enable_crc()` which enables CRC checks.

* **Added** `is_crc_enabled()` which return `True` or `False` depending on if CRC is enabled or not.

* **Changed** `power_up_tx()`, `power_up_rx()`, `power_down()` to reflect changes to CRC enable/disable.

* **Changed** `set_payload_size(size)` does not update NRF24L01 module, but sets the payload size as default to be used with `open_reading_pipe()`.

* **Changed** `open_reading_pipe(pipe, address, size=None)` to take an additional `size` parameter determining the payload size for the particular pipe being opened. If no value is provided for `size` the value set by `set_payload_size(size)` is used instead.  This should ensure backward compatibility.

* **Added** NRF24 contructor parameter `pa_level` with a default of `RF24_PA.MAX`.

* **Added** `wait_until_sent` method polling the status of NRF24L01 module until package has been sent or a timeout occurs.



