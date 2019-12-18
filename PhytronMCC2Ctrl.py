#!/usr/bin/python -u
# coding: utf8
# PhytronMCC2Ctrl
from PyTango import DevState, DevVarCharArray, DevUShort, DevUChar, AttrWriteType, DispLevel
from PyTango.server import Device, DeviceMeta, attribute, command, device_property, run
import time
import sys
import serial
import array
import six

flagDebugIO = 0


@six.add_metaclass(DeviceMeta)
class PhytronMCC2Ctrl(Device):
    # device properties
    port = device_property(
        dtype='str', default_value="/dev/ttyMCC"
    )

    baudrate = device_property(
        dtype='int16', default_value="115200"
    )
    
    # device attributes
    port = attribute(
        dtype='str',
        label="port",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    baudrate = attribute(
        dtype='int',
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

        self.serial.baudrate = self.baudrate
        self.serial.port = self.port

        if flagDebugIO:
            print("PhytronMCC2Ctrl.init_device: port = %s " % self.port)
            print("PhytronMCC2Ctrl.init_device: baudrate = %s " % self.baudrate)

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

    def always_executed_hook(self):
        self.info_stream("In %s::always_excuted_hook()" % self.get_name())

    # attribute read/write methods
    def read_port(self):
        return self.port

    def read_baudrate(self):
        return self.baudrate

    # commands
    @command
    def open(self):
        self.info_stream("In %s::open()" % self.get_name())

        if self.configure:
            self.serial.baudrate = self.baudrate
            self.serial.port = self.port
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
            print("PhytronMcc2Ctrl.open: failed to open %s " % self.port)
            sys.exit(255)

        if flagDebugIO:
            print("PhytronMcc2Ctrl.open: connected to %s " % self.port)

    def is_open_allowed(self):
        if self.get_state() in [DevState.ON, DevState.FAULT]:
            return False
        return True

    @command
    def close(self):
        self.info_stream("In %s::close()" % self.get_name())
        try:
            self.serial.close()
            self.set_state(DevState.OFF)
        except Exception:
            pass

    def is_close_allowed(self):
        if self.get_state() in [DevState.OFF]:
            return False
        return True

    @command
    def flush_input(self):
        self.info_stream("In %s::flush_input()" % self.get_name())
        try:
            self.serial.flush_input()
        except Exception:
            pass

    def is_flush_input_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True

    @command
    def flush_output(self):
        self.info_stream("In %s::flush_output()" % self.get_name())
        try:
            self.serial.flush_output()
        except Exception:
            pass

    def is_flush_output_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True

    @command(dtype_in=str, dtype_out=DevVarCharArray)
    def write_read(self, cmd):
        self.serial.write(cmd.encode())
        self.serial.flush()
        # 20ms wait time
        time.sleep(0.02)
        argout = []
        s = ''
        s = self.serial.readline()
        self.debug_stream(s)
        b = array.array('B', s)
        argout = b.tolist()
        return argout

    @command(dtype_in=str)
    def write(self, cmd):
        self.info_stream("In %s::write()" % self.get_name())
        self.serial.write(cmd.encode())

    def is_write_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True

    @command(dtype_in=DevUShort, dtype_out=DevVarCharArray)
    def read(self, argin):
        self.info_stream("In %s::read()" % self.get_name())
        argout = []
        s = self.serial.read(argin)
        self.debug_stream(s)
        b = array.array('B', s)
        argout = b.tolist()
        return argout

    def is_read_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True

    @command(dtype_out=DevVarCharArray)
    def read_line(self):
        self.info_stream("In %s::read_line()" % self.get_name())
        argout = []
        s = self.serial.readline(eol=self.terminatorchar)
        self.debug_stream(s)
        b = array.array('B', s)
        argout = b.tolist()
        return argout

    def is_read_line_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True

    @command(dtype_in=DevUChar, dtype_out=DevVarCharArray)
    def read_until(self, c):
        self.info_stream("In %s::read_until()" % self.get_name())
        argout = []
        s = self.serial.read_until(c)
        self.debug_stream(s)
        b = array.array('B', s)
        argout = b.tolist()
        return argout

    def is_read_until_allowed(self):
        if self.get_state() in [DevState.FAULT, DevState.OFF]:
            return False
        return True


if __name__ == '__main__':
    run((PhytronMCC2Ctrl, ))
