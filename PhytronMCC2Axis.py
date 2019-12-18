#!/usr/bin/python -u
# coding: utf8
# Phytron MotorDevice
# 17.10. 1. first test in the Lab, Definition of improvements/changes
# Changes:
# ------------
# 18.10.
# modules are still subdivided according to axes
# Changes:
# -------------
# Device: hhg/MCC2/0.0
# means: first number is the address of the module
#        second number is the number of motor
# in this example: Rs485-address = 0, motor: 0 (upper plug)
# or  device: hhg/MCC2/1.1 means: module 2, motor 1 (lower plug)
#
# 19.10.
# acceleration and max. frequenz are implemantet as commands
#
# 6.11.
# added movement_unit:
#  - steps, mm, zoll, degree
# added spindle_pitch
#  - pitch of spindle (Spindelsteigung siehe Handbuch Seite 50)
# changing attribute "my_state" in command and the name from "my_state" to
# "mcc_state"
#
# 8.11.
# added set_display_unit

from PyTango import Except, AttrWriteType, DevState, DebugIt, DevDouble, DeviceProxy
from PyTango.server import run
from PyTango.server import Device, DeviceMeta, device_property
from PyTango.server import attribute, command
import sys
import six

flagDebugIO = 0


@six.add_metaclass(DeviceMeta)
class PhytronMCC2Axis(Device):

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

    # definition some constants
    __STX = chr(2)         # Start of text
    __ACK = chr(6)         # Command ok
    __NACK = chr(0x15)     # command failed
    __ETX = chr(3)         # end of text
    __SE = 'SE'            # command for reading extended status
    __REG_STEP_CNT = 'P20'
    __REG_UNIT = 'P2'      # Register unit of movement
    __REG_SPINDLE = 'P3'   # Register of spindle pitch (Spindelsteigung)
    __MOVE_UNIT = ("step", "mm", "inch", "degree")
    __SPINDLE = 1.0
    __DISPL_UNIT = ("steps", "mm", "inch", "degree")
    __MOVE = 1
    __LIM_PLUS = 2
    __LIM_MINUS = 1
    # private status variables, updated by "mcc_state()"
    __Limit_Minus = False
    __Limit_Plus = False
    __Motor_Run = False
    __Alias = 'mcc2'
    __Hold_Current = 0
    __Run_Current = 0
    # other private variables
    __Addr = 0
    __Axis = 0
    __Pos = 0
    __Unit = 'step'
    __Pitch = 1.0
    __I = 0

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
            self.get_mcc_state()
            self.read_position()
            self.get_spindle_pitch()
            self.get_movement_unit()
            self.set_display_unit()
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.OFF)

        if flagDebugIO:
            print("PhytronMCCAxis2.init_device: Limit- = %s" % self.__Limit_Minus)
            print("PhytronMCCAxis2.init_device: Limit+ = %s " % self.__Limit_Plus)
            print("PhytronMCCAxis2.init_device: Run = %s" % self.__Motor_Run)
            print("PhytronMCCAxis2.init_device: Postion %s" % self.__Pos)

    limit_minus = attribute(
        dtype='bool',
        label="Limit -",
    )

    limit_plus = attribute(
        dtype='bool',
        label="Limit +",
    )

    run = attribute(
        dtype='bool',
        label="motor running",
    )

    position = attribute(
        dtype=float,
        format='%8.3f',
        access=AttrWriteType.READ_WRITE,
        label="position",
        unit='steps'
    )

    alias = attribute(
        dtype='string',
        access=AttrWriteType.READ,
        label="alias",
    )

    def delete_device(self):
        self.set_state(DevState.OFF)

    def set_display_unit(self):
        ac = self.get_attribute_config_3('position')[0]
        ac.unit = self.__Unit
        if (self.__Pitch % 1) == 0.0:
            ac.format = '%8d'
        else:
            ac.format = '%8.3f'
        self.set_attribute_config_3(ac)

    def read_limit_minus(self):
        return self.__Limit_Minus

    def read_limit_plus(self):
        return self.__Limit_Plus

    def read_run(self):
        return self.__Motor_Run

    def read_position(self):
        return (self.__Pos)

    def write_position(self, value):
        if (self.__Axis == 0):
            answer = self.send_cmd('XA{:.4f}'.format(value))
        else:
            answer = self.send_cmd('YA{:.4f}'.format(value))
        if answer != self.__NACK:
            self.set_state(DevState.MOVING)
            self.__Motor_Run = True

    def read_alias(self):
        return self.Alias

    @command(dtype_in=str, dtype_out=str, doc_in='enter a command', doc_out='the answer')
    def send_cmd(self, cmd):
        # building the string to send it
        s = self.__STX + str(self.__Addr) + cmd + self.__ETX
        temp = self.ctrl.write_read(s)
        answer = temp.tostring()
        if self.__ACK in answer:
            tmp = answer.lstrip(self.__STX).lstrip(self.__ACK).rstrip(self.__ETX)
            self.set_state(DevState.ON)
        else:
            tmp = self.__NACK
            self.set_state(DevState.FAULT)
        return (tmp)

    @command(dtype_out=str, doc_out='the version of firmware')
    def read_firmware_version(self):
        version = self.send_cmd('IVR')
        return (version)

    @command(dtype_out=float, doc_out='position')
    def get_pos(self):
        if (self.__Axis == 0):
            tmp = self.send_cmd('X' + self.__REG_STEP_CNT + 'R')
        else:
            tmp = self.send_cmd('Y' + self.__REG_STEP_CNT + 'R')
        self.__Pos = float(tmp)
        return (self.__Pos)

    @command(polling_period=200, doc_out='state of limits and moving')
    def get_mcc_state(self):
        self.get_pos()
        answer = self.send_cmd('SE')
        if (self.__Axis == 0):
            self.__Limit_Minus = bool(int(answer[2]) & self.__LIM_MINUS)
            self.__Limit_Plus = bool(int(answer[2]) & self.__LIM_PLUS)
            self.__Motor_Run = not(bool(int(answer[1]) & self.__MOVE))
        else:
            self.__Limit_Minus = bool(int(answer[6]) & self.__LIM_MINUS)
            self.__Limit_Plus = bool(int(answer[6]) & self.__LIM_PLUS)
            self.__Motor_Run = not(bool(int(answer[5]) & self.__MOVE))
        if self.__Motor_Run is False:
            self.set_state(DevState.ON)

    @command(dtype_out=int, doc_out='get acceleration')
    def get_accel(self):
        if (self.__Axis == 0):
            return (int(self.send_cmd('XP15R')))
        else:
            return (int(self.send_cmd('YP15R')))

    @command(dtype_in=int, doc_out='set acceleration')
    def set_accel(self, Acceleration):
        if (self.__Axis == 0):
            self.send_cmd('XP15S{:f}'.format(Acceleration))
        else:
            self.send_cmd('YP15S{:f}'.format(Acceleration))

    @command(dtype_out=int, doc_out='get fmax.')
    def get_f_max(self):
        if (self.__Axis == 0):
            return (int(self.send_cmd('XP14R')))
        else:
            return (int(self.send_cmd('YP14R')))

    @command(dtype_in=int, doc_out='set fmax.')
    def set_f_max(self, F_Max):
        if (self.__Axis == 0):
            self.send_cmd('XP14S{:f}'.format(F_Max))
        else:
            self.send_cmd('YP14S{:f}'.format(F_Max))

    @command
    @DebugIt()
    def Jog_Plus(self):
        if (self.__Axis == 0):
            self.send_cmd('XL+')
        else:
            self.send_cmd('YL+')

    @command
    @DebugIt()
    def Jog_Minus(self):
        self.__Last_Read = 0  # Zuruecksetzen
        if (self.__Axis == 0):
            self.send_cmd('XL-')
        else:
            self.send_cmd('YL-')

    @command
    @DebugIt()
    def Homing_Plus(self):
        self.__Last_Read = 0    # Zuruecksetzen
        if (self.__Axis == 0):
            self.send_cmd('X0+')
        else:
            self.send_cmd('Y0+')

    @command
    @DebugIt()
    def Homing_Minus(self):
        if (self.__Axis == 0):
            self.send_cmd('X0-')
        else:
            self.send_cmd('Y0-')

    @command
    @DebugIt()
    def Stop(self):
        if (self.__Axis == 0):
            self.send_cmd('XS')
        else:
            self.send_cmd('YS')
        self.__Last_Read = 0

    @command(dtype_in=str, dtype_out=str, doc_in="step\nmm\ninch\ndegree",
             doc_out='the unit')
    @DebugIt()
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

    @command(dtype_in=DevDouble, dtype_out=DevDouble,
             doc_in="spindle pitch (see manual page 50)",
             doc_out='the unit')
    @DebugIt()
    def set_spindle_pitch(self, pitch):
        if (self.__Axis == 0):
            self.send_cmd('XP3S{:f}'.format(pitch))
        else:
            self.send_cmd('YP3S{:f}'.format(pitch))
        self.__Pitch = self.get_spindle_pitch()
        self.set_display_unit()
        return(self.__Pitch)

    @command(dtype_out=float)
    def get_spindle_pitch(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP3R')
        else:
            answer = self.send_cmd('YP3R')
        self.__Pitch = float(answer)
        return float(answer)

    @command(dtype_in=str)
    def set_alias(self, mcc_name):
        self.__Alias = mcc_name
        self.db.put_device_property(self.get_name(), {'Alias': mcc_name})

    @command(dtype_in=int, dtype_out=str, doc_in="motor run current (see manual page 54)",)
    def set_run_current(self, current):
        if current not in range(1, 26):
            return 'input not in range 1..25'
        if (self.__Axis == 0):
            self.send_cmd('XP41S{:d}'.format(current))
        else:
            self.send_cmd('YP41S{:d}'.format(current))
        self.__Run_Current = self.get_run_current()
        return str(self.__Run_Current)

    @command(dtype_out=int)
    def get_run_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP41R')
        else:
            answer = self.send_cmd('YP41R')
        self.__Run_Current = int(answer)
        return self.__Run_Current

    @command(dtype_in=int, dtype_out=str, doc_in="motor hold current (see manual page 54)",)
    def set_hold_current(self, current):
        if current not in range(1, 26):
            return 'input not in range 0..25'
        if (self.__Axis == 0):
            self.send_cmd('XP40S{:d}'.format(current))
        else:
            self.send_cmd('YP40S{:d}'.format(current))
        self.__Hold_Current = self.get_hold_current()
        return str(self.__Hold_Current)

    @command(dtype_out=int)
    def get_hold_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP40R')
        else:
            answer = self.send_cmd('YP40R')
        self.__Hold_Current = int(answer)
        return self.__Hold_Current

    @command(dtype_out=str)
    def write_to_eeprom(self):
        self.send_cmd('SA')
        return 'parameter written to flash memory'


if __name__ == '__main__':
    run((PhytronMCC2Axis,))
