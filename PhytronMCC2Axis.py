#!/usr/bin/python3 -u
# coding: utf8
# PhytronMCC2Axis
from tango import Database, Except, AttrWriteType, DevState, DeviceProxy, DispLevel
from tango.server import device_property
from tango.server import Device, attribute, command
import sys
from enum import IntEnum

class MovementType(IntEnum):
    rotational = 0  # DevEnum's must start at 0
    linear = 1  # and increment by 1

class MovementUnit(IntEnum):
    # step, mm, inch, degree
    step = 0
    mm = 1
    inch = 2
    degree = 3
    
class PhytronMCC2Axis(Device):
    # device properties
    CtrlDevice = device_property(
        dtype="str", default_value=""
    )

    Axis = device_property(
        dtype="int16"
    )

    Address = device_property(
        dtype="int16"
    )

    Alias = device_property(
        dtype="str", default_value="MCC2"
    )

    # device attributes
    hw_limit_minus = attribute(
        dtype="bool",
        label="HW limit -",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    hw_limit_plus = attribute(
        dtype="bool",
        label="HW limit +",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    sw_limit_minus = attribute(
        dtype="float",
        format="%8.3f",
        label="SW limit -",
        unit="steps",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
    )
    
    sw_limit_plus = attribute(
        dtype="float",
        format="%8.3f",
        label="SW limit +",
        unit="steps",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
    )

    position = attribute(
        dtype="float",
        format="%8.3f",
        label="position",
        unit="steps",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
    )

    alias = attribute(
        dtype="string",
        label="alias",
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
    )

    inverted = attribute(
        dtype="bool",
        label="inverted",
        memorized=True,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    acceleration = attribute(
        dtype="int",
        label="acceleration",
        unit="Hz",
        min_value=4000,
        max_value=500000,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    velocity = attribute(
        dtype="int",
        label="velocity",
        unit="Hz",
        min_value=0,
        max_value=40000,
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    hold_current = attribute(
        dtype="float",
        label="hold current",
        unit="A",
        min_value=0,
        max_value=2.5,
        format="%2.1f",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    run_current = attribute(
        dtype="float",
        label="run current",
        unit="A",
        min_value=0,
        max_value=2.5,
        format="%2.1f",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )

    steps_per_unit = attribute(
        dtype="float",
        format="%10d",
        label="steps per unit",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
    )
    
    type_of_movement = attribute(
        dtype=MovementType,
        label="type of movement",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
        doc="""0 = rotational
Rotating table, 1 limit switch for mechanical zero
(referencing)
1 = linear
for XY tables or other linear systems,
2 limit switches:
Mechanical zero and limit direction -
Limit direction +"""
    )
    
    movement_unit = attribute(
        dtype=MovementUnit,
        label="unit",
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
        doc="Allowed unit values are step, mm, inch, degree"
    )

    # definition some constants
    __NACK = chr(0x15)     # command failed
    __LIM_PLUS = 2
    __LIM_MINUS = 1
    # private status variables, updated by "mcc_state()"
    __HW_Limit_Minus = False
    __HW_Limit_Plus = False
    __Inverted = False
    __Alias = "mcc2"
    # other private variables
    __Addr = 0
    __Axis = 0
    __Axis_Name = ""
    __Unit = "step"
    __Steps_Per_Unit = 1.0

    def init_device(self):
        self.info_stream("init_device()")
        self.get_device_properties(self.get_device_class())

        self.__Addr = self.Address
        self.__Axis = self.Axis
        self.__Alias = self.Alias

        if self.__Axis == 0:
            self.__Axis_Name = "X"
        else:
            self.__Axis_Name = "Y"

        self.info_stream("module address: {:d}".format(self.Address))
        self.info_stream("module axis: {:d}".format(self.Axis))
        self.info_stream("alias: {:s}".format(self.Alias))
        
        try:
            self.ctrl = DeviceProxy(self.CtrlDevice)
            self.info_stream("ctrl. device: {:s}".format(self.CtrlDevice))
        except Exception:
            self.error_stream("failed to create proxy to {:s}".format(self.CtrlDevice))
            sys.exit(255)

        # check if the CrlDevice ON, if not open the serial port
        if str(self.ctrl.state()) == "OFF":
            self.ctrl.open()
            self.info_stream("controller sucessfully opened")
        else:
            self.info_stream("controller was already open")

        if ("MCC" in self.read_firmware_version()):
            # read memorized attributes from Database
            db = Database()
            try:
                attr = db.get_device_attribute_property(self.get_name(), ["inverted"])
                if attr["inverted"]["__value"][0] == "true":
                    self.__Inverted = True
                else:
                    self.__Inverted = False
            except Exception:
                self.__Inverted = False
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.OFF)
        
        self.info_stream("HW limit-: {0}".format(self.__HW_Limit_Minus))
        self.info_stream("HW limit+: {0}".format(self.__HW_Limit_Plus))

    def delete_device(self):
        self.set_state(DevState.OFF)

    def dev_state(self):
        answer = self._send_cmd("SE")
        if (self.__Axis == 0):
            if self.__Inverted:
                self.__HW_Limit_Minus = bool(int(answer[2]) & self.__LIM_PLUS)
                self.__HW_Limit_Plus = bool(int(answer[2]) & self.__LIM_MINUS)
            else:
                self.__HW_Limit_Minus = bool(int(answer[2]) & self.__LIM_MINUS)
                self.__HW_Limit_Plus = bool(int(answer[2]) & self.__LIM_PLUS)
            moving = not(bool(int(answer[1]) & 1))
        else:
            if self.__Inverted:
                self.__HW_Limit_Minus = bool(int(answer[6]) & self.__LIM_PLUS)
                self.__HW_Limit_Plus = bool(int(answer[6]) & self.__LIM_MINUS)
            else:
                self.__HW_Limit_Minus = bool(int(answer[6]) & self.__LIM_MINUS)
                self.__HW_Limit_Plus = bool(int(answer[6]) & self.__LIM_PLUS)
            moving = not(bool(int(answer[5]) & 1))
        self.debug_stream("HW limit-: {0}".format(self.__HW_Limit_Minus))
        self.debug_stream("HW limit+: {0}".format(self.__HW_Limit_Plus))
        if moving is False:
            self.set_status("Device in ON")
            self.debug_stream("device is: ON")
            return DevState.ON
        else:
            self.set_status("Device is MOVING")
            self.debug_stream("device is: MOVING")
            return DevState.MOVING

    def set_display_unit(self):
        attributes = ["position", "sw_limit_minus", "sw_limit_plus"]
        self.warn_stream("cannot set unit for position and sw limits dynamically")
        self.info_stream(str(self.__Unit))
        #for attr in attributes:
        #    ac = self.get_attribute_config(attr)
        #    ac.unit = self.__Unit
        #    if (self.__Step_Per_Unit % 1) == 0.0:
        #        ac.format = "%8d"
        #    else:
        #        ac.format = "%8.3f"
        #    self.set_attribute_config(ac)

    # attribute read/write methods
    def read_hw_limit_minus(self):
        return self.__HW_Limit_Minus

    def read_hw_limit_plus(self):
        return self.__HW_Limit_Plus

    def read_sw_limit_minus(self):
        return float(self.send_cmd("P24R"))

    def write_sw_limit_minus(self, value):
        self.send_cmd("P24S{:f}".format(value))

    def read_sw_limit_plus(self):
        return float(self.send_cmd("P23R"))

    def write_sw_limit_plus(self, value):
        self.send_cmd("P23S{:f}".format(value))
    
    def read_position(self):
        ret = self.send_cmd("P20R")
        if self.__Inverted:
            return -1*float(ret)
        else:
            return float(ret)

    def write_position(self, value):
        if self.__Inverted:
            value = -1*value
        answer = self.send_cmd("A{:.4f}".format(value))
        if answer != self.__NACK:
            self.set_state(DevState.MOVING)

    def read_alias(self):
        return self.Alias

    def read_inverted(self):
        return self.__Inverted

    def write_inverted(self, value):
        self.__Inverted = bool(value)

    def read_acceleration(self):
        return int(self.send_cmd("P15R"))

    def write_acceleration(self, value):
        self.send_cmd("P15S{:d}".format(value))

    def read_velocity(self):
        return int(self.send_cmd("P14R"))

    def write_velocity(self, value):
        self.send_cmd("P14S{:d}".format(value))

    def read_run_current(self):
        return float(self.send_cmd("P41R"))/10

    def write_run_current(self, value):
        # motor run current (see manual page 54)
        value = int(value*10)
        if value not in range(1, 26):
            return "input not in range 1..25"
        self.send_cmd("P41S{:d}".format(value))

    def read_hold_current(self):
        return float(self.send_cmd("P40R"))/10

    def write_hold_current(self, value):
        # motor hold current (see manual page 54)
        value = int(value*10)
        if value not in range(1, 26):
            return "input not in range 0..25"
        self.send_cmd("P40S{:d}".format(value))

    def read_steps_per_unit(self):
        # inverse of spindle pitch (see manual page 50)
        self.__Steps_Per_Unit = int(1/float(self.send_cmd("P03R")))
        return self.__Steps_Per_Unit

    def write_steps_per_unit(self, value):
        # inverse of spindle pitch (see manual page 50)
        self.send_cmd("P03S{:f}".format(1/value))
        # update display unit
        self.set_display_unit()

    def read_type_of_movement(self):
        return MovementType.linear if bool(int(self.send_cmd("P01R"))) else MovementType.rotational

    def write_type_of_movement(self, value):
        self.send_cmd("P01S{:d}".format(int(value)))

    def read_movement_unit(self):
        res = int(self.send_cmd("P02R"))
        if res == 1:
            self.__Unit = MovementUnit.step
        elif res == 2:
            self.__Unit = MovementUnit.mm
        elif res == 3:
            self.__Unit = MovementUnit.inch
        elif res == 4:
            self.__Unit = MovementUnit.degree
        return self.__Unit

    def write_movement_unit(self, value):
        self.send_cmd("P02S{:d}".format(int(value+1)))
        self.read_movement_unit()
        self.set_display_unit()

    # internal methods
    def _send_cmd(self, cmd):
        # add module address to the beginning of command
        cmd = str(self.__Addr) + cmd
        res = self.ctrl.write_read(cmd)
        if res == self.__NACK:
            self.set_state(DevState.FAULT)
            self.warn_stream("command not acknowledged from controller "
                             "-> Fault State")
            return ""
        return res
    
    # commands
    @command(dtype_in=str, dtype_out=str,
             doc_in="enter a command",
             doc_out="the response")
    def send_cmd(self, cmd):
        # add axis name (X, Y) to beginning of command
        return self._send_cmd(self.__Axis_Name + cmd)        

    @command(dtype_out=str, doc_out="the version of firmware")
    def read_firmware_version(self):
        version = self._send_cmd("IVR")
        return version

    @command(dtype_in=float, doc_in="position")
    def set_position(self, value):
        if self.__Inverted:
            value = -1*value
        self.send_cmd("P20S{:.4f}".format(value))

    @command
    def Jog_Plus(self):
        if self.__Inverted:
            self.send_cmd("L-")
        else:
            self.send_cmd("L+")
        self.set_state(DevState.MOVING)

    @command
    def Jog_Minus(self):
        if self.__Inverted:
            self.send_cmd("L+")
        else:
            self.send_cmd("L-")
        self.set_state(DevState.MOVING)

    @command
    def Homing_Plus(self):
        if self.__Inverted:
            self.send_cmd("0-")
        else:
            self.send_cmd("0+")
        self.set_state(DevState.MOVING)

    @command
    def Homing_Minus(self):
        if self.__Inverted:
            self.send_cmd("0+")
        else:
            self.send_cmd("0-")
        self.set_state(DevState.MOVING)

    @command
    def Stop(self):
        self.send_cmd("S")
        self.set_state(DevState.ON)
        
    @command
    def Abort(self):
        self.send_cmd("SN")
        self.set_state(DevState.ON)

    @command(dtype_in=str)
    def set_alias(self, mcc_name):
        self.__Alias = mcc_name
        self.db.put_device_property(self.get_name(), {"Alias": mcc_name})

    @command
    def write_to_eeprom(self):
        self.send_cmd("SA")
        self.info_stream("parameters written to EEPROM")
        return "parameters written to EEPROM"
    
    @command(dtype_out=str)
    def dump_config(self):
        parameters = range(1, 50)
        res = ""
        for par in parameters:
            cmd = "P{:02d}R".format(par)
            res = res + "P{:02d}: {:s}\n".format(par, str(self.send_cmd(cmd)))
        return res


if __name__ == "__main__":
    PhytronMCC2Axis.run_server()
