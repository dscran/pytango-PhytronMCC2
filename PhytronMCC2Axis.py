#!/usr/bin/python -u
# coding: utf8
# PhytronMCC2Axis
from PyTango import Database, Except, AttrWriteType, DevState, DeviceProxy, DispLevel
from PyTango.server import run
from PyTango.server import Device, DeviceMeta, device_property
from PyTango.server import attribute, command
import sys
import six

flagDebugIO = 0


@six.add_metaclass(DeviceMeta)
class PhytronMCC2Axis(Device):
    # device properties
    CtrlDevice = device_property(
        dtype='str', default_value=""
    )

    Axis = device_property(
        dtype='int16'
    )

    Address = device_property(
        dtype='int16'
    )

    Alias = device_property(
        dtype='str', default_value="MCC2"
    )

    # device attributes
    limit_minus = attribute(
        dtype='bool',
        label="limit -",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    limit_plus = attribute(
        dtype='bool',
        label="limit +",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    position = attribute(
        dtype=float,
        format='%8.3f',
        label="position",
        unit='steps',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
    )

    alias = attribute(
        dtype='string',
        label="alias",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    inverted = attribute(
        dtype='bool',
        label="inverted",
        memorized=True,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    acceleration = attribute(
        dtype='int',
        label="acceleration",
        unit='Hz',
        min_value=4000,
        max_value=500000,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    velocity = attribute(
        dtype='int',
        label="velocity",
        unit='Hz',
        min_value=0,
        max_value=40000,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    hold_current = attribute(
        dtype='float',
        label="hold current",
        unit='A',
        min_value=0,
        max_value=2.5,
        format='2.1f',        
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    run_current = attribute(
        dtype='float',
        label="run current",
        unit='A',
        min_value=0,
        max_value=2.5,
        format='2.1f',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    step_per_unit = attribute(
        dtype='float',
        format='%10.8f',
        label="step per unit",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    # definition some constants
    __STX = chr(2)         # Start of text
    __ACK = chr(6)         # Command ok
    __NACK = chr(0x15)     # command failed
    __ETX = chr(3)         # end of text
    __REG_STEP_CNT = 'P20'
    __MOVE_UNIT = ("step", "mm", "inch", "degree")
    __MOVE = 1
    __LIM_PLUS = 2
    __LIM_MINUS = 1
    # private status variables, updated by "mcc_state()"
    __Limit_Minus = False
    __Limit_Plus = False
    __Inverted = False
    __Alias = 'mcc2'
    # other private variables
    __Addr = 0
    __Axis = 0
    __Pos = 0
    __Unit = 'step'
    __Step_Per_Unit = 1.0

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())

        self.__Addr = self.Address
        self.__Axis = self.Axis
        self.__Alias = self.Alias

        if flagDebugIO:
            print("PhytronMCC2Axis.init_device: name = %s" % self.get_name())
            print("PhytronMCC2Axis.init_device: Ctrl.Device = %s" % self.CtrlDevice)
            print("PhytronMCC2Axis.init_device: Module Address =  %s" % self.Address)
            print("PhytronMCC2Axis.init_device: Module Axis = %s" % self.Axis)
            print("PhytronMCC2Axis.init_device: Alias = %s" % self.Alias)
        try:
            self.ctrl = DeviceProxy(self.CtrlDevice)
        except Exception:
            print("PhytronMCCAxis2.init_device: failed to create proxy to %s" % self.CtrlDevice)
            sys.exit(255)

        # check if the CrlDevice ON, if not open the serial port
        if str(self.ctrl.state()) == "OFF":
            self.ctrl.open()

        if ("MCC" in self.read_firmware_version()):
            # read memorized attributes from Database
            db = Database()
            attr = db.get_device_attribute_property(self.get_name(), ['inverted'])
            if attr['inverted']['__value'][0] == 'true':
                self.__Inverted = True
            else:
                self.__Inverted = False
            # read controller variables
            self.get_mcc_state()
            self.read_position()
            self.read_step_per_unit()
            self.get_movement_unit()
            self.set_display_unit()
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.OFF)

        if flagDebugIO:
            print("PhytronMCCAxis2.init_device: Limit- = %s" % self.__Limit_Minus)
            print("PhytronMCCAxis2.init_device: Limit+ = %s " % self.__Limit_Plus)
            print("PhytronMCCAxis2.init_device: Postion %s" % self.__Pos)

    def delete_device(self):
        self.set_state(DevState.OFF)

    def set_display_unit(self):
        ac = self.get_attribute_config_3('position')[0]
        ac.unit = self.__Unit
        if (self.__Conv_Factor % 1) == 0.0:
            ac.format = '%8d'
        else:
            ac.format = '%8.3f'
        self.set_attribute_config_3(ac)

    def get_position(self):
        if (self.__Axis == 0):
            tmp = self.send_cmd('X' + self.__REG_STEP_CNT + 'R')
        else:
            tmp = self.send_cmd('Y' + self.__REG_STEP_CNT + 'R')
        if self.__Inverted:
            self.__Pos = -1*float(tmp)
        else:
            self.__Pos = float(tmp)
        return (self.__Pos)

    # attribute read/write methods
    def read_limit_minus(self):
        return self.__Limit_Minus

    def read_limit_plus(self):
        return self.__Limit_Plus

    def read_position(self):
        return (self.__Pos)

    def write_position(self, value):
        if self.__Inverted:
            value = -1*value

        if (self.__Axis == 0):
            answer = self.send_cmd('XA{:.4f}'.format(value))
        else:
            answer = self.send_cmd('YA{:.4f}'.format(value))
        if answer != self.__NACK:
            self.set_state(DevState.MOVING)

    def read_alias(self):
        return self.Alias

    def read_inverted(self):
        return (self.__Inverted)

    def write_inverted(self, value):
        self.__Inverted = bool(value)

    def read_acceleration(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP15R')
        else:
            answer = self.send_cmd('YP15R')
        return int(answer)

    def write_acceleration(self, value):
        if (self.__Axis == 0):
            self.send_cmd('XP15S{:d}'.format(value))
        else:
            self.send_cmd('YP15S{:d}'.format(value))

    def read_velocity(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP14R')
        else:
            answer = self.send_cmd('YP14R')
        return int(answer)

    def write_velocity(self, value):
        if (self.__Axis == 0):
            self.send_cmd('XP14S{:d}'.format(value))
        else:
            self.send_cmd('YP14S{:d}'.format(value))

    def read_run_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP41R')
        else:
            answer = self.send_cmd('YP41R')
        return float(answer*0.1)

    def write_run_current(self, value):
        # motor run current (see manual page 54)
        value = int(value*10)
        if value not in range(1, 26):
            return 'input not in range 1..25'
        if (self.__Axis == 0):
            self.send_cmd('XP41S{:d}'.format(value))
        else:
            self.send_cmd('YP41S{:d}'.format(value))

    def read_hold_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP40R')
        else:
            answer = self.send_cmd('YP40R')
        return float(answer*0.1)

    def write_hold_current(self, value):
        # motor hold current (see manual page 54)
        value = int(value*10)
        if value not in range(1, 26):
            return 'input not in range 0..25'
        if (self.__Axis == 0):
            self.send_cmd('XP40S{:d}'.format(value))
        else:
            self.send_cmd('YP40S{:d}'.format(value))

    def read_step_per_unit(self):
        # spindle pitch (see manual page 50)
        if (self.__Axis == 0):
            answer = self.send_cmd('XP3R')
        else:
            answer = self.send_cmd('YP3R')
        self.__Conv_Factor = float(answer)
        return self.__Conv_Factor

    def write_step_per_unit(self, value):
        # spindle pitch (see manual page 50)
        if (self.__Axis == 0):
            self.send_cmd('XP3S{:f}'.format(value))
        else:
            self.send_cmd('YP3S{:f}'.format(value))
        # update display unit
        self.set_display_unit()

    # commands
    @command(dtype_in=str, dtype_out=str, doc_in='enter a command', doc_out='the answer')
    def send_cmd(self, cmd):
        # building the string to send it
        s = self.__STX + str(self.__Addr) + cmd + self.__ETX
        temp = self.ctrl.write_read(s)
        answer = temp.tostring()
        if self.__ACK in answer:
            tmp = answer.lstrip(self.__STX).lstrip(self.__ACK).rstrip(self.__ETX)
        else:
            tmp = self.__NACK
            self.set_state(DevState.FAULT)
        return (tmp)

    @command(dtype_out=str, doc_out='the version of firmware')
    def read_firmware_version(self):
        version = self.send_cmd('IVR')
        return (version)

    @command(dtype_in=float, doc_in='position')
    def set_position(self, value):
        if self.__Inverted:
            value = -1*value
        if (self.__Axis == 0):
            self.send_cmd('X' + self.__REG_STEP_CNT + 'S{:.4f}'.format(value))
        else:
            self.send_cmd('Y' + self.__REG_STEP_CNT + 'S{:.4f}'.format(value))

    @command(polling_period=200, doc_out='state of limits and moving')
    def get_mcc_state(self):
        self.get_position()
        answer = self.send_cmd('SE')
        if (self.__Axis == 0):
            if self.__Inverted:
                self.__Limit_Minus = bool(int(answer[2]) & self.__LIM_PLUS)
                self.__Limit_Plus = bool(int(answer[2]) & self.__LIM_MINUS)
            else:
                self.__Limit_Minus = bool(int(answer[2]) & self.__LIM_MINUS)
                self.__Limit_Plus = bool(int(answer[2]) & self.__LIM_PLUS)
            moving = not(bool(int(answer[1]) & self.__MOVE))
        else:
            if self.__Inverted:
                self.__Limit_Minus = bool(int(answer[6]) & self.__LIM_PLUS)
                self.__Limit_Plus = bool(int(answer[6]) & self.__LIM_MINUS)
            else:
                self.__Limit_Minus = bool(int(answer[6]) & self.__LIM_MINUS)
                self.__Limit_Plus = bool(int(answer[6]) & self.__LIM_PLUS)
            moving = not(bool(int(answer[5]) & self.__MOVE))
        if moving is False:
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.MOVING)

    @command
    def Jog_Plus(self):
        if (self.__Axis == 0):
            if self.__Inverted:
                self.send_cmd('XL-')
            else:
                self.send_cmd('XL+')
        else:
            if self.__Inverted:
                self.send_cmd('YL-')
            else:
                self.send_cmd('YL+')

    @command
    def Jog_Minus(self):
        self.__Last_Read = 0  # Zuruecksetzen
        if (self.__Axis == 0):
            if self.__Inverted:
                self.send_cmd('XL+')
            else:
                self.send_cmd('XL-')
        else:
            if self.__Inverted:
                self.send_cmd('YL+')
            else:
                self.send_cmd('YL-')

    @command
    def Homing_Plus(self):
        self.__Last_Read = 0    # Zuruecksetzen
        if (self.__Axis == 0):
            if self.__Inverted:
                self.send_cmd('X0-')
            else:
                self.send_cmd('X0+')
        else:
            if self.__Inverted:
                self.send_cmd('Y0-')
            else:
                self.send_cmd('Y0+')

    @command
    def Homing_Minus(self):
        if (self.__Axis == 0):
            if self.__Inverted:
                self.send_cmd('X0+')
            else:
                self.send_cmd('X0-')
        else:
            if self.__Inverted:
                self.send_cmd('Y0+')
            else:
                self.send_cmd('Y0-')

    @command
    def Stop(self):
        if (self.__Axis == 0):
            self.send_cmd('XS')
        else:
            self.send_cmd('YS')
        self.__Last_Read = 0

    @command(dtype_in=str, dtype_out=str, doc_in="step\nmm\ninch\ndegree",
             doc_out='the unit')
    def set_movement_unit(self, unit):
        if str.lower(unit) in self.__MOVE_UNIT:
            self.__Unit = str.lower(unit)
            tmp = self.__MOVE_UNIT.index(self.__Unit) + 1
            if (self.__Axis == 0):
                self.send_cmd('XP2S' + str(tmp))
            else:
                self.send_cmd('YP2S' + str(tmp))

            self.set_display_unit()
        else:
            Except.throw_exception("PhytronMCC.set_movement_unit",
                                   "Allowed unit values are step, mm, inch, degree",
                                   "set_movement_unit()")
        self.__Unit = self.get_movement_unit()
        return(self.__Unit)

    @command(dtype_out=str)
    def get_movement_unit(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP2R')
        else:
            answer = self.send_cmd('YP2R')
        self.__Unit = self.__MOVE_UNIT[int(answer)-1]
        return (self.__Unit)

    @command(dtype_in=str)
    def set_alias(self, mcc_name):
        self.__Alias = mcc_name
        self.db.put_device_property(self.get_name(), {'Alias': mcc_name})

    def write_to_eeprom(self):
        self.send_cmd('SA')
        return 'parameter written to flash memory'


if __name__ == '__main__':
    run((PhytronMCC2Axis,))
