#!/usr/bin/python3 -u
# coding: utf8
# PhytronMCC2Ctrl
from tango import DevState, DevVarCharArray, DevUShort, DevUChar, AttrWriteType, DispLevel, DebugIt
from tango.server import Device, attribute, command, device_property
import time
import sys
import serial
import array

class PhytronMCC2Ctrl(Device):
    # device properties
    Port = device_property(
        dtype="str",
        default_value="/dev/ttyMCC",
    )

    Baudrate = device_property(
        dtype="int",
        default_value="115200",
    )

    # device attributes
    port = attribute(
        dtype="str",
        label="port",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    baudrate = attribute(
        dtype="int",
        label="baudrate",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    PARITIES = ["none", "odd", "even"]
    FLOWCONTROL = ["none", "software", "hardware", "sw/hw"]
    TERMINATOR = ["LF/CR", "CR/LF", "CR", "LF", "NONE"]
    TERMINATORCHAR = ["\n\r", "\r\n", "\r", "\n", ""]

    def init_device(self):
        self.info_stream("In %s::init_device()" % self.get_name())
        self.get_device_properties(self.get_device_class())
        self.set_state(DevState.OFF)

        self.configure = True
        self.serial = serial.Serial()

        self.serial.baudrate = self.Baudrate
        self.serial.port = self.Port

        
        self.info_stream("PhytronMCC2Ctrl.init_device: port = %s " % self.Port)
        self.info_stream("PhytronMCC2Ctrl.init_device: baudrate = %s " % self.Baudrate)

        self.bytesize = 8
        self.serial.bytesize = self.bytesize

        self.parity = PhytronMCC2Ctrl.PARITIES[0]
        self.current_parity = self.parity
        self.serial.parity = serial.PARITY_NONE

        self.stopbits = 1
        self.serial.stopbits = self.stopbits

        self.timeout = 0
        self.serial.timeout = self.timeout

        self.flowcontrol = PhytronMCC2Ctrl.FLOWCONTROL[0]
        self.current_flowcontrol = self.flowcontrol
        self.serial.xonxoff = 0
        self.serial.rtscts = 0

        self.terminator = PhytronMCC2Ctrl.TERMINATOR[0]
        self.terminatorchar = chr(3)    # end of text PhytronMcc2Ctrl.TERMINATORCHAR[0]

        # open serial port
        self.open()

    # attribute read/write methods
    def read_port(self):
        return self.Port

    def read_baudrate(self):
        return int(self.Baudrate)

    # commands
    @command
    def open(self):
        self.info_stream("In %s::open()" % self.get_name())

        if self.configure:
            self.serial.baudrate = self.Baudrate
            self.serial.port = self.Port
            self.serial.bytesize = self.bytesize
            self.serial.stopbits = self.stopbits

            self.serial.timeout = self.timeout
            self.current_flowcontrol = self.flowcontrol

            if self.current_flowcontrol == "none":
                self.serial.xonxoff = 0
                self.serial.rtscts = 0
            elif self.current_flowcontrol == "software":
                self.serial.xonxoff = 1
                self.serial.rtscts = 0
            elif self.current_flowcontrol == "hardware":
                self.serial.xonxoff = 0
                self.serial.rtscts = 1
            elif self.current_flowcontrol == "sw/hw":
                self.serial.xonxoff = 1
                self.serial.rtscts = 1

            self.current_parity = self.parity
            if self.current_parity == PhytronMCC2Ctrl.PARITIES[0]:
                self.serial.parity = serial.PARITY_NONE
            elif self.current_parity == PhytronMCC2Ctrl.PARITIES[1]:
                self.serial.parity = serial.PARITY_ODD
            elif self.current_parity == PhytronMCC2Ctrl.PARITIES[1]:
                self.serial.parity = serial.PARITY_EVEN

        try:
            self.serial.open()
            self.set_state(DevState.ON)
            self.configure = False
        except Exception:
            self.error_stream("PhytronMcc2Ctrl.open: failed to open %s " % self.Port)
            sys.exit(255)

        self.info_stream("PhytronMcc2Ctrl.open: connected to %s " % self.Port)

    def is_open_allowed(self):
        if self.get_state() in [DevState.ON, DevState.FAULT]:
            return False
        return True

    @command
    def close(self):
        try:
            self.serial.close()
            self.set_state(DevState.OFF)
        except Exception:
            pass

    def is_close_allowed(self):
        if self.get_state() in [DevState.OFF]:
            return False
        return True

    @command(dtype_in=str, dtype_out=str)
    def write_read(self, cmd):
        self.debug_stream(cmd)
        self.serial.write(cmd.encode('utf-8'))
        self.serial.flush()
        # 20ms wait time
        time.sleep(0.02)
        res = self.serial.readline()
        #b = array.array('B', s)
        #argout = b.tolist()
        
        return res.decode('utf-8')

    def is_write_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True


if __name__ == '__main__':
    PhytronMCC2Ctrl.run_server()
