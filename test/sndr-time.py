import pigpio
import time
from datetime import datetime
from nrf24 import *
import struct
from os import environ as env
from configparser import ConfigParser

if __name__ == "__main__":
    #
    # Example sending date/time information using NRF24.
    #
    print("Python NRF24 date/time sender.")
    
    # Create NRF24 from configuration.
    config = ConfigParser()
    config.read('etc/sndr-time.ini')
    nrf, pi = NRF24.from_config(config)
    
    # Publish date/time information every 5 seconds.
    delay = 5
    published = 0
    while True:
        if (time.monotonic() - published >= delay):
                # Get UTC timestamp.               
                now = datetime.utcnow()
                print(datetime.isoformat(now, timespec='milliseconds'))

                # Create payload as bytes.
                payload = struct.pack("<B4sHBBBBBB", 0xfe, b'TIME', now.year, now.month, now.day, \
                    now.hour, now.minute, now.second, \
                    now.weekday())
                
                # Send the payload to whoever may be listening.
                nrf.send(payload)                
                published = time.monotonic()                
        time.sleep(0.5)
