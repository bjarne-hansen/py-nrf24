#!/usr/bin/env python

import time
import pigpio
import sys


class NRF24:
    """
    Note that RX and TX addresses must match

    Note that communication channels must match:

    Note that payload size must match:

    The following table describes how to configure the operational
    modes.

    +----------+--------+---------+--------+-----------------------------+
    |Mode      | PWR_UP | PRIM_RX | CE pin | FIFO state                  |
    +----------+--------+---------+--------+-----------------------------+
    |RX mode   |  1     |  1      |  1     | ---                         |
    +----------+--------+---------+--------+-----------------------------+
    |TX mode   |  1     |  0      |  1     | Data in TX FIFOs. Will empty|
    |          |        |         |        | all levels in TX FIFOs      |
    +----------+--------+---------+--------+-----------------------------+
    |TX mode   |  1     |  0      |  >10us | Data in TX FIFOs. Will empty|
    |          |        |         |  pulse | one level in TX FIFOs       |
    +----------+--------+---------+--------+-----------------------------+
    |Standby-II|  1     |  0      |  1     | TX FIFO empty               |
    +----------+--------+---------+--------+-----------------------------+
    |Standby-I |  1     |  ---    |  0     | No ongoing transmission     |
    +----------+--------+---------+--------+-----------------------------+
    |Power Down|  0     |  ---    |  ---   | ---                         |
    +----------+--------+---------+--------+-----------------------------+
    """

    SPI_MAIN_CE0 = 0
    SPI_MAIN_CE1 = 1
    SPI_AUX_CE0 = 2
    SPI_AUX_CE1 = 3
    SPI_AUX_CE2 = 4

    TX = 0
    RX = 1

    ACK_PAYLOAD = -1
    DYNAMIC_PAYLOAD = 0
    MIN_PAYLOAD = 1
    MAX_PAYLOAD = 32

    def _nrf_xfer(self, data):
        b, d = self.pi.spi_xfer(self.spih, data)

        return d

    def _nrf_command(self, arg):
        if type(arg) is not list:
            arg = [arg]

        return self._nrf_xfer(arg)

    def _nrf_read_reg(self, reg, count):
        return self._nrf_xfer([reg] + [0] * count)[1:]

    def _nrf_write_reg(self, reg, arg):
        """
        Write arg (which may be one or more bytes) to reg.

        This function is only permitted in a powerdown or
        standby mode.
        """
        if type(arg) is not list:
            arg = [arg]

        self._nrf_xfer([self.W_REGISTER | reg] + arg)

    def _configure_payload(self):
        if self.payload_size >= self.MIN_PAYLOAD:                               # fixed payload
            self._nrf_write_reg(self.RX_PW_P0, self.payload_size)
            self._nrf_write_reg(self.RX_PW_P1, self.payload_size)
            self._nrf_write_reg(self.DYNPD, 0)
            self._nrf_write_reg(self.FEATURE, 0)
        else:                                                                   # dynamic payload
            self._nrf_write_reg(self.DYNPD, self.DPL_P0 | self.DPL_P1)
            if self.payload_size == self.ACK_PAYLOAD:
                self._nrf_write_reg(self.FEATURE, self.EN_DPL | self.EN_ACK_PAY)
            else:
                self._nrf_write_reg(self.FEATURE, self.EN_DPL)

    def __init__(self,
                 pi,  # pigpio PI connection
                 ce,  # GPIO for chip enable
                 spi_channel=SPI_MAIN_CE0,  # SPI channel
                 spi_speed=50e3,  # SPI bps
                 mode=RX,  # primary mode (RX or TX)
                 channel=1,  # radio channel
                 payload_size=8,  # message size in bytes
                 pad=32,  # value used to pad short messages
                 address_bytes=5,  # RX/TX address length in bytes
                 crc_bytes=1  # number of CRC bytes
                 ):
        """
        Instantiate with the Pi to which the card reader is connected.

        Optionally the SPI channel may be specified.  The default is
        main SPI channel 0.

        The following constants may be used to define the channel:

           SPI_MAIN_CE0 - main SPI channel 0
           SPI_MAIN_CE1 - main SPI channel 1
           SPI_AUX_CE0  - aux  SPI channel 0
           SPI_AUX_CE1  - aux  SPI channel 1
           SPI_AUX_CE2  - aux  SPI channel 2
        """

        self.pi = pi

        assert 0 <= ce <= 31
        self.CE = ce
        pi.set_mode(ce, pigpio.OUTPUT)
        self.unset_ce()

        assert NRF24.SPI_MAIN_CE0 <= spi_channel <= NRF24.SPI_AUX_CE2

        assert 32000 <= spi_speed <= 10e6

        if spi_channel < NRF24.SPI_AUX_CE0:
            self.spih = pi.spi_open(spi_channel, int(spi_speed))
        else:
            self.spih = pi.spi_open(
                spi_channel - NRF24.SPI_AUX_CE0, int(spi_speed), NRF24._AUX_SPI)

        self.channel = 0
        self.set_channel(channel)

        self.payload_size = 0
        self.set_payload_size(payload_size)

        self.pad = ord(' ')
        self.set_padding(pad)

        self.width = 5
        self.set_address_bytes(address_bytes)

        self.crc = 1
        self.set_crc_bytes(crc_bytes)

        self.PTX = 0

        self.power_down()

        self._nrf_write_reg(self.SETUP_RETR, 0b11111)

        self.flush_rx()
        self.flush_tx()

        self.power_up_rx()

    def set_channel(self, channel):
        assert 0 <= channel <= 125
        self.channel = channel  # frequency (2400 + channel) MHz
        self._nrf_write_reg(self.RF_CH, self.channel)

    def set_payload_size(self, payload):
        assert self.ACK_PAYLOAD <= payload <= self.MAX_PAYLOAD
        self.payload_size = payload  # 0 is dynamic payload
        self._configure_payload()

    def set_padding(self, pad):
        try:
            self.pad = ord(pad)
        except:
            self.pad = pad
        assert 0 <= self.pad <= 255

    def set_address_bytes(self, address_bytes):
        assert 3 <= address_bytes <= 5
        self.width = address_bytes
        self._nrf_write_reg(self.SETUP_AW, self.width - 2)

    def set_crc_bytes(self, crc_bytes):
        assert 1 <= crc_bytes <= 2
        if crc_bytes == 1:
            self.crc = 0
        else:
            self.crc = self.CRCO

    def show_registers(self):
        print(self.format_config())
        print(self.format_en_aa())
        print(self.format_en_rxaddr())
        print(self.format_setup_aw())
        print(self.format_setup_retr())
        print(self.format_rf_ch())
        print(self.format_rf_setup())
        print(self.format_status())
        print(self.format_observe_tx())
        print(self.format_rpd())
        print(self.format_rx_addr_px())
        print(self.format_tx_addr())
        print(self.format_rx_pw_px())
        print(self.format_fifo_status())
        print(self.format_dynpd())
        print(self.format_feature())

    def _make_fixed_width(self, msg, width, pad):

        if isinstance(msg, str):
            msg = map(ord, msg)

        msg = list(msg)

        if len(msg) >= width:
            return msg[:width]

        msg.extend([pad] * (width - len(msg)))

        return msg

    def send(self, data):
        if isinstance(data, str):
            data = list(map(ord, data))

        status = self.get_status()

        if status & (self.TX_FULL | self.MAX_RT):
            self.flush_tx()

        if self.payload_size >= self.MIN_PAYLOAD:  # fixed payload
            data = self._make_fixed_width(data, self.payload_size, self.pad)

        self._nrf_command([self.W_TX_PAYLOAD] + data)

        self.power_up_tx()

    def ack_payload(self, data):
        self._nrf_command([self.W_ACK_PAYLOAD] + data)

    def set_local_address(self, address):

        addr = self._make_fixed_width(address, self.width, self.pad)

        self.unset_ce()
        print(self.RX_ADDR_P1, type(self.RX_ADDR_P1), addr, type(addr))
        self._nrf_write_reg(self.RX_ADDR_P1, addr)
        self.set_ce()

    def set_remote_address(self, raddr):
        addr = self._make_fixed_width(raddr, self.width, self.pad)

        self.unset_ce()
        self._nrf_write_reg(self.TX_ADDR, addr)
        self._nrf_write_reg(self.RX_ADDR_P0, addr)  # Needed for auto acks

        self.set_ce()

    def data_ready(self):

        status = self.get_status()

        if status & self.RX_DR:
            return True

        status = self._nrf_read_reg(self.FIFO_STATUS, 1)[0]

        if status & self.FRX_EMPTY:
            return False
        else:
            return True

    def is_sending(self):

        if self.PTX > 0:
            status = self.get_status()

            if status & (self.TX_DS | self.MAX_RT):
                self.power_up_rx()
                return False

            return True

        return False

    def get_payload(self):

        if self.payload_size < self.MIN_PAYLOAD:  # dynamic payload
            bytes_count = self._nrf_command([self.R_RX_PL_WID, 0])[1]
        else:   # fixed payload
            bytes_count = self.payload_size

        d = self._nrf_read_reg(self.R_RX_PAYLOAD, bytes_count)

        self.unset_ce()  # added

        self._nrf_write_reg(self.STATUS, self.RX_DR)

        self.set_ce()  # added

        return d

    def get_status(self):

        return self._nrf_command(self.NOP)[0]

    def power_up_tx(self):

        self.unset_ce()

        self.PTX = 1

        config = self.EN_CRC | self.crc | self.PWR_UP

        self._nrf_write_reg(self.CONFIG, config)

        self._nrf_write_reg(self.STATUS, self.RX_DR | self.TX_DS | self.MAX_RT)

        self.set_ce()

    def power_up_rx(self):

        self.unset_ce()

        self.PTX = 0

        config = self.EN_CRC | self.crc | self.PWR_UP | self.PRIM_RX

        self._nrf_write_reg(self.CONFIG, config)

        self._nrf_write_reg(self.STATUS, self.RX_DR | self.TX_DS | self.MAX_RT)

        self.set_ce()

    def power_down(self):

        self.unset_ce()

        self._nrf_write_reg(self.CONFIG, self.EN_CRC | self.crc)

    def set_ce(self):

        self.pi.write(self.CE, 1)

    def unset_ce(self):

        self.pi.write(self.CE, 0)

    def flush_rx(self):

        self._nrf_command(self.FLUSH_RX)

    def flush_tx(self):

        self._nrf_command(self.FLUSH_TX)

    _AUX_SPI = (1 << 8)

    R_REGISTER = 0x00  # reg in bits 0-4, read 1-5 bytes
    W_REGISTER = 0x20  # reg in bits 0-4, write 1-5 bytes
    R_RX_PL_WID = 0x60
    R_RX_PAYLOAD = 0x61  # read 1-32 bytes
    W_TX_PAYLOAD = 0xA0  # write 1-32 bytes
    W_ACK_PAYLOAD = 0xA8  # pipe in bits 0-2, write 1-32 bytes
    W_TX_PAYLOAD_NO_ACK = 0xB0  # no ACK, write 1-32 bytes
    FLUSH_TX = 0xE1
    FLUSH_RX = 0xE2
    REUSE_TX_PL = 0xE3
    NOP = 0xFF  # no operation

    CONFIG = 0x00
    EN_AA = 0x01
    EN_RXADDR = 0x02
    SETUP_AW = 0x03
    SETUP_RETR = 0x04
    RF_CH = 0x05
    RF_SETUP = 0x06
    STATUS = 0x07
    OBSERVE_TX = 0x08
    RPD = 0x09
    RX_ADDR_P0 = 0x0A
    RX_ADDR_P1 = 0x0B
    RX_ADDR_P2 = 0x0C
    RX_ADDR_P3 = 0x0D
    RX_ADDR_P4 = 0x0E
    RX_ADDR_P5 = 0x0F
    TX_ADDR = 0x10
    RX_PW_P0 = 0x11
    RX_PW_P1 = 0x12
    RX_PW_P2 = 0x13
    RX_PW_P3 = 0x14
    RX_PW_P4 = 0x15
    RX_PW_P5 = 0x16
    FIFO_STATUS = 0x17
    DYNPD = 0x1C
    FEATURE = 0x1D

    # CONFIG

    MASK_RX_DR = 1 << 6
    MASK_TX_DS = 1 << 5
    MASK_MAX_RT = 1 << 4
    EN_CRC = 1 << 3  # default
    CRCO = 1 << 2
    PWR_UP = 1 << 1
    PRIM_RX = 1 << 0

    def format_config(self):

        v = self._nrf_read_reg(self.CONFIG, 1)[0]

        s = "CONFIG: "

        if v & self.MASK_RX_DR:
            s += "no RX_DR IRQ, "
        else:
            s += "RX_DR IRQ, "

        if v & self.MASK_TX_DS:
            s += "no TX_DS IRQ, "
        else:
            s += "TX_DS IRQ, "

        if v & self.MASK_MAX_RT:
            s += "no MAX_RT IRQ, "
        else:
            s += "MAX_RT IRQ, "

        if v & self.EN_CRC:
            s += "CRC on, "
        else:
            s += "CRC off, "

        if v & self.CRCO:
            s += "CRC 2 byte, "
        else:
            s += "CRC 1 byte, "

        if v & self.PWR_UP:
            s += "Power up, "
        else:
            s += "Power down, "

        if v & self.PRIM_RX:
            s += "RX"
        else:
            s += "TX"

        return s

    # EN_AA

    ENAA_P5 = 1 << 5  # default
    ENAA_P4 = 1 << 4  # default
    ENAA_P3 = 1 << 3  # default
    ENAA_P2 = 1 << 2  # default
    ENAA_P1 = 1 << 1  # default
    ENAA_P0 = 1 << 0  # default

    def format_en_aa(self):

        v = self._nrf_read_reg(self.EN_AA, 1)[0]

        s = "EN_AA: "

        for i in range(6):
            if v & (1 << i):
                s += "P{}:ACK ".format(i)
            else:
                s += "P{}:no ACK ".format(i)

        return s

    # EN_RXADDR

    ERX_P5 = 1 << 5
    ERX_P4 = 1 << 4
    ERX_P3 = 1 << 3
    ERX_P2 = 1 << 2
    ERX_P1 = 1 << 1  # default
    ERX_P0 = 1 << 0  # default

    def format_en_rxaddr(self):

        v = self._nrf_read_reg(self.EN_RXADDR, 1)[0]

        s = "EN_RXADDR: "

        for i in range(6):
            if v & (1 << i):
                s += "P{}:on ".format(i)
            else:
                s += "P{}:off ".format(i)

        return s

    # SETUP_AW

    AW_3 = 1
    AW_4 = 2
    AW_5 = 3  # default

    def format_setup_aw(self):

        v = self._nrf_read_reg(self.SETUP_AW, 1)[0]

        s = "SETUP_AW: address width bytes "

        if v == self.AW_3:
            s += "3"
        elif v == self.AW_4:
            s += "4"
        elif v == self.AW_5:
            s += "5"
        else:
            s += "invalid"

        return s

    # SETUP_RETR

    # ARD 7-4
    # ARC 3-0

    def format_setup_retr(self):

        v = self._nrf_read_reg(self.SETUP_RETR, 1)[0]

        ard = (((v >> 4) & 15) * 250) + 250
        arc = v & 15
        s = "SETUP_RETR: retry delay {} us, retries {}".format(ard, arc)

        return s

    # RF_CH

    # RF_CH 6-0

    def format_rf_ch(self):

        v = self._nrf_read_reg(self.RF_CH, 1)[0]

        s = "RF_CH: channel {}".format(v & 127)

        return s

    # RF_SETUP

    CONT_WAVE = 1 << 7
    RF_DR_LOW = 1 << 5
    PLL_LOCK = 1 << 4
    RF_DR_HIGH = 1 << 3

    # RF_PWR  2-1

    def format_rf_setup(self):

        v = self._nrf_read_reg(self.RF_SETUP, 1)[0]

        s = "RF_SETUP: "

        if v & self.CONT_WAVE:
            s += "continuos carrier on, "
        else:
            s += "no continuous carrier, "

        if v & self.PLL_LOCK:
            s += "force PLL lock on, "
        else:
            s += "no force PLL lock, "

        dr = 0

        if v & self.RF_DR_LOW:
            dr += 2

        if v & self.RF_DR_HIGH:
            dr += 1

        if dr == 0:
            s += "1 Mbps, "
        elif dr == 1:
            s += "2 Mbps, "
        elif dr == 2:
            s += "250 kbps, "
        else:
            s += "illegal speed, "

        pwr = (v >> 1) & 3

        if pwr == 0:
            s += "-18 dBm"
        elif pwr == 1:
            s += "-12 dBm"
        elif pwr == 2:
            s += "-6 dBm"
        else:
            s += "0 dBm"

        return s

    # STATUS

    RX_DR = 1 << 6
    TX_DS = 1 << 5
    MAX_RT = 1 << 4
    # RX_P_NO 3-1
    TX_FULL = 1 << 0

    def format_status(self):

        v = self._nrf_read_reg(self.STATUS, 1)[0]

        s = "STATUS: "

        if v & self.RX_DR:
            s += "RX data, "
        else:
            s += "no RX data, "

        if v & self.TX_DS:
            s += "TX ok, "
        else:
            s += "no TX, "

        if v & self.MAX_RT:
            s += "TX retries bad, "
        else:
            s += "TX retries ok, "

        p = (v >> 1) & 7

        if p < 6:
            s += "pipe {} data, ".format(p)
        elif p == 6:
            s += "PIPE 6 ERROR, "
        else:
            s += "no pipe data, "

        if v & self.TX_FULL:
            s += "TX FIFO full"
        else:
            s += "TX FIFO not full"

        return s

    # OBSERVE_TX

    # PLOS_CNT 7-4
    # ARC_CNT 3-0

    def format_observe_tx(self):

        v = self._nrf_read_reg(self.OBSERVE_TX, 1)[0]

        plos = (v >> 4) & 15
        arc = v & 15
        s = "OBSERVE_TX: lost packets {}, retries {}".format(plos, arc)

        return s

    # RPD

    # RPD 1 << 0

    def format_rpd(self):

        v = self._nrf_read_reg(self.RPD, 1)[0]

        s = "RPD: received power detector {}".format(v & 1)

        return s

    # RX_ADDR_P0 - RX_ADDR_P5

    @staticmethod
    def _byte2hex(s):
        return ":".join("{:02x}".format(c) for c in s)

    def format_rx_addr_px(self):

        p0 = self._nrf_read_reg(self.RX_ADDR_P0, 5)
        p1 = self._nrf_read_reg(self.RX_ADDR_P1, 5)
        p2 = self._nrf_read_reg(self.RX_ADDR_P2, 1)[0]
        p3 = self._nrf_read_reg(self.RX_ADDR_P3, 1)[0]
        p4 = self._nrf_read_reg(self.RX_ADDR_P4, 1)[0]
        p5 = self._nrf_read_reg(self.RX_ADDR_P5, 1)[0]

        s = "RX ADDR_PX: "
        s += "P0=" + self._byte2hex(p0) + " "
        s += "P1=" + self._byte2hex(p1) + " "
        s += "P2={:02x} ".format(p2)
        s += "P3={:02x} ".format(p3)
        s += "P4={:02x} ".format(p4)
        s += "P5={:02x}".format(p5)

        return s

    # TX_ADDR

    def format_tx_addr(self):

        p0 = self._nrf_read_reg(self.TX_ADDR, 5)

        s = "TX_ADDR: " + self._byte2hex(p0)

        return s

    # RX_PW_P0 - RX_PW_P5

    def format_rx_pw_px(self):

        p0 = self._nrf_read_reg(self.RX_PW_P0, 1)[0]
        p1 = self._nrf_read_reg(self.RX_PW_P1, 1)[0]
        p2 = self._nrf_read_reg(self.RX_PW_P2, 1)[0]
        p3 = self._nrf_read_reg(self.RX_PW_P3, 1)[0]
        p4 = self._nrf_read_reg(self.RX_PW_P4, 1)[0]
        p5 = self._nrf_read_reg(self.RX_PW_P5, 1)[0]

        s = "RX_PW_PX: "
        s += "P0={} ".format(p0)
        s += "P1={} ".format(p1)
        s += "P2={} ".format(p2)
        s += "P3={} ".format(p3)
        s += "P4={} ".format(p4)
        s += "P5={} ".format(p5)

        return s

    # FIFO_STATUS

    FTX_REUSE = 1 << 6
    FTX_FULL = 1 << 5
    FTX_EMPTY = 1 << 4
    FRX_FULL = 1 << 1
    FRX_EMPTY = 1 << 0

    def format_fifo_status(self):

        v = self._nrf_read_reg(self.FIFO_STATUS, 1)[0]

        s = "FIFO_STATUS: "

        if v & self.FTX_REUSE:
            s += "TX reuse set, "
        else:
            s += "TX reuse not set, "

        if v & self.FTX_FULL:
            s += "TX FIFO full, "
        elif v & self.FTX_EMPTY:
            s += "TX FIFO empty, "
        else:
            s += "TX FIFO has data, "

        if v & self.FRX_FULL:
            s += "RX FIFO full, "
        elif v & self.FRX_EMPTY:
            s += "RX FIFO empty"
        else:
            s += "RX FIFO has data"

        return s

    # DYNPD

    DPL_P5 = 1 << 5
    DPL_P4 = 1 << 4
    DPL_P3 = 1 << 3
    DPL_P2 = 1 << 2
    DPL_P1 = 1 << 1
    DPL_P0 = 1 << 0

    def format_dynpd(self):

        v = self._nrf_read_reg(self.DYNPD, 1)[0]

        s = "DYNPD: "

        for i in range(6):
            if v & (1 << i):
                s += "P{}:on ".format(i)
            else:
                s += "P{}:off ".format(i)

        return s

    # FEATURE

    EN_DPL = 1 << 2
    EN_ACK_PAY = 1 << 1
    EN_DYN_ACK = 1 << 0

    def format_feature(self):

        v = self._nrf_read_reg(self.FEATURE, 1)[0]

        s = "FEATURE: "

        if v & self.EN_DPL:
            s += "Dynamic payload on, "
        else:
            s += "Dynamic payload off, "

        if v & self.EN_ACK_PAY:
            s += "ACK payload on, "
        else:
            s += "ACK payload off, "

        if v & self.EN_DYN_ACK:
            s += "W_TX_PAYLOAD_NOACK on"
        else:
            s += "W_TX_PAYLOAD_NOACK off"

        return s





if __name__ == "__main__":

    if len(sys.argv) > 1:
        SENDING = False
    else:
        SENDING = True

    pi = pigpio.pi()
    if not pi.connected:
        exit()

    end_time = time.time() + 60

    nrf = NRF24(pi, ce=25, payload_size=NRF24.ACK_PAYLOAD, pad=ord('*'), address_bytes=3, crc_bytes=2)
    nrf.show_registers()

    if SENDING:
        count = 1

        nrf.set_local_address("h1")
        nrf.set_remote_address("h2")

        while time.time() < end_time:
            print(nrf.format_fifo_status())
            print(nrf.format_observe_tx())
            if not nrf.is_sending():
                print(f"tx {count}")
                nrf.send(f"msg:{count:d}")
                count += 1
            time.sleep(0.5)

    else:

        nrf.set_local_address("h2")
        nrf.set_remote_address("h1")

        while time.time() < end_time:
            print(nrf.format_fifo_status())
            # print(nrf.format_OBSERVE_TX())
            while nrf.data_ready():
                print(f"rx: {nrf.get_payload()}")
            time.sleep(0.5)

    pi.spi_close(nrf.spih)

    pi.stop()
