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
# changing attribute "my_state" in command and the name from "my_state" to "mcc_state"
# 
# 8.11.
# added set_display_unit

from PyTango.server import run
from PyTango import DebugIt
from PyTango.server import Device, DeviceMeta, device_property
from PyTango.server import attribute, pipe, command, class_property
from PyTango import AttrQuality, AttrWriteType, DispLevel, DeviceProxy, UserDefaultAttrProp
import PyTango
import tango
import sys


flagDebugIO = 1


class PhytronMcc2(Device): 
    #__metaclass__ = DeviceMeta

    # read the name of the CtrlDevice from the properties
    # read number of axise 0 or 1 ( one Module can control two motors)
    # read the address of the module (0..15)
    
    # -----------------
    # Device Properties
    # -----------------

    

    
    db = PyTango.Database()
     
# definition some constants
 
    __STX     = chr(2)    # Start of text
    __ACK     = chr(6)    # Command ok
    __NACK    = chr(0x15) # command failed
    __ETX     = chr(3)    # end of text
    __SE      = 'SE'      # command for reading extended status
    
    __REG_STEP_CNT = 'P20'
    __REG_UNIT     = 'P2'  # Register unit of movement
    __REG_SPINDLE  = 'P3'  # Register of spindle pitch (Spindelsteigung)
    
    __MOVE_UNIT = ("step" , "mm", "inch", "degree")
    __SPINDLE   = 1.0
    __DISPL_UNIT= ("steps" , "mm", "inch", "degree")
    
    
    __MOVE      = 1     
    __LIM_PLUS  = 2
    __LIM_MINUS = 1

# private status variables, updated by "mcc_state()"
    __Limit_Minus = False
    __Limit_Plus  = False
    __Motor_Run   = False
    __Motor_Name  = 'mcc2'
    __Hold_Current= 0
    __Run_Current = 0
    
# other private variables
    __Addr          = 0
    __Axis          = 0
    __Pos  = 0
    __Unit = 'step'
    __Pitch = 1.0
    __I = 0
    
    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In __init__()")
        PhytronMcc2.init_device(self)
        #----- PROTECTED REGION ID(NewFocusPico8742.__init__) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#  //  NewFocusPico8742.__init__
    
    # Initializing the Device
    def init_device(self):
        self.get_device_properties(self.get_device_class())
        
        self.proxy = DeviceProxy(self.get_name())
        
        if flagDebugIO:
            print("Get_name: %s" % (self.get_name()))
        
        # get the properties of the attribute "position" from the database
        self.attrib = self.get_attribute_config_3('position')[0]

        self.__Addr         = self.Address
        self.__Axis         = self.Motor
        self.__Motor_Name   = self.Alias
        
        if flagDebugIO:
            print("Ctrl.Device:  %s" %( self.CtrlDevice))
            print("Modul Adresse: ",self.__Addr)
            print("Motor: ",self.__Axis)
            print("Motor_Name:  %s" %(self.__Motor_Name))
        try:
            self.ctrl = PyTango.DeviceProxy( self.CtrlDevice)
        except:
            print("PhytronMcc2.init_device: failed to create proxy to %s" % (self.CtrlDevice))
            sys.exit( 255)
        
        # check if the CrlDevice ON, if not open the serial port
        if str(self.ctrl.state()) == "OFF":
            self.ctrl.Open()
        
        
        # try to read some parameters from device MCC2
        
        if ("MCC" in self.read_firmware_version()):
            self.get_mcc_state()
            self.read_position()
            self.get_spindle_pitch()
            self.get_movement_unit()
            self.set_display_unit()
            self.set_state(PyTango.DevState.ON)  
        else:
            self.set_state(PyTango.DevState.OFF)
        
        if flagDebugIO:
            ("Limit-: ",self.__Limit_Minus)
            print("Limit+: ",self.__Limit_Plus)
            print("Run: ",self.__Motor_Run)
            print("Postion: ", self.__Pos)
        
        
    def delete_device(self):
        # PROTECTED REGION ID(PhytronMCC.delete_device) ENABLED START #
        self.set_state(PyTango.DevState.OFF)
        # PROTECTED REGION END #    //  PhytronMCC.delete_device
    
    # set new properties ("unit", "format") for attribute "position"    
    def set_display_unit(self):
        self.attrib.unit= self.__Unit
        if (self.__Pitch%1) == 0.0:
            self.attrib.format = '%8d'
        else:
            self.attrib.format = '%8.3f'
        # write properties to the database
        self.set_attribute_config_3(self.attrib)
       
       
       
    
    # ------------------
    # Attributes methods
    # ------------------
    
    
    def read_limit_minus(self):
        # PROTECTED REGION ID(PhytronMCC.limit_minus_read) ENABLED START #
        return self.__Limit_Minus
        # PROTECTED REGION END #    //  PhytronMCC.limit_minus_read

    def read_limit_plus(self):
        # PROTECTED REGION ID(PhytronMCC.limit_plus_read) ENABLED START #
        return self.__Limit_Plus
        # PROTECTED REGION END #    //  PhytronMCC.limit_plus_read

    def read_run(self):
        # PROTECTED REGION ID(PhytronMCC.run_read) ENABLED START #
        return self.__Motor_Run
        # PROTECTED REGION END #    //  PhytronMCC.run_read

    def read_position(self):
        # PROTECTED REGION ID(PhytronMCC.position_read) ENABLED START #
        return (self.__Pos)         
         # PROTECTED REGION END #    //  PhytronMCC.position_read

    def write_position(self, value):
        # PROTECTED REGION ID(PhytronMCC.position_write) ENABLED START #
        
        if (self.__Axis == 0):
            answer = self.send_cmd('XA{:.4f}'.format(value))
        else:
            answer = self.send_cmd('YA{:.4f}'.format(value))
        if answer <> self.__NACK:
            self.set_state(PyTango.DevState.MOVING)
            self.__Motor_Run = True
            
        # PROTECTED REGION END #    //  PhytronMCC.position_write
   
    def read_name(self):
        # PROTECTED REGION ID(PhytronMCC.read_name) ENABLED START #
        return self.__Motor_Name
        # PROTECTED REGION END #    //  PhytronMCC.read_name
    
    
    # -------------
    # Pipes methods
    # -------------

  
    # --------
    # Commands
    # --------

    # communication  (write/read)
    # ------------- ------------- 
    @command(dtype_in=str, dtype_out=str, doc_in='enter a command', doc_out='the answer')    
    def send_cmd(self,cmd):
        # building the string to send it 
        s = self.__STX + str(self.__Addr) + cmd  + self.__ETX
        temp = self.ctrl.WriteRead(s)
        answer = temp.tostring()
        if self.__ACK in answer:
            tmp =  answer.lstrip(self.__STX).lstrip(self.__ACK).rstrip(self.__ETX)   
        
            self.set_state(PyTango.DevState.ON)
        else:
            tmp = self.__NACK
            self.set_state(PyTango.DevState.FAULT)
        return (tmp)
    

    # read firmwareversion of device MCC2
    # ------------------------------------    
    @command(dtype_out=str, doc_out='the version of firmware')    
    def read_firmware_version(self):
        version = self.send_cmd('IVR')
        return (version)
        
        
    
    # read the actual position
    # ------------------------
    @command(dtype_out=float, doc_out='position')    
    def get_pos(self):
        if (self.__Axis == 0):
            tmp = self.send_cmd('X' + self.__REG_STEP_CNT +'R')
        else:
            tmp = self.send_cmd('Y' + self.__REG_STEP_CNT +'R')
        self.__Pos = float(tmp)
        return (self.__Pos)
        
    
    # read the extended status    
    # --------------------------------
    @command(polling_period=200, doc_out='state of limits and moving' )   
    def get_mcc_state(self):
        # PROTECTED REGION ID(PhytronMCC.get_mcc_state) ENABLED START #
        self.get_pos()
        answer = self.send_cmd('SE')
        if (self.__Axis == 0):
            self.__Limit_Minus = bool(int(answer[2]) & self.__LIM_MINUS)
            self.__Limit_Plus  = bool(int(answer[2]) & self.__LIM_PLUS)
            self.__Motor_Run = not(bool(int(answer[1]) & self.__MOVE))            
        else:
            self.__Limit_Minus = bool(int(answer[6]) & self.__LIM_MINUS)
            self.__Limit_Plus  = bool(int(answer[6]) & self.__LIM_PLUS)
            self.__Motor_Run = not(bool(int(answer[5]) & self.__MOVE))
        if self.__Motor_Run == False:
            self.set_state(PyTango.DevState.ON)
                
        # PROTECTED REGION END #    //  PhytronMCC..get_mcc_state
        
        
    # begin get and set acceleration
    # --------------------------------
    @command(dtype_out=int, doc_out='get acceleration')  
    def get_accel(self):
         # PROTECTED REGION ID(PhytronMCC.read_accel) ENABLED START #
        if (self.__Axis == 0):
            return (int(self.send_cmd('XP15R')))
        else:
            return (int(self.send_cmd('YP15R')))
        # PROTECTED REGION END #    //  PhytronMCC.read_accel
        
        
    @command(dtype_in=int, doc_out='set acceleration')        
    def set_accel(self, Acceleration):
         # PROTECTED REGION ID(PhytronMCC.write_accel) ENABLED START #
        if (self.__Axis == 0):
            answer = self.send_cmd('XP15S' + str(Acceleration))    
        else:
            answer = self.send_cmd('YP15S' + str(Acceleration))    
        # PROTECTED REGION END #    //  PhytronMCC.write_accel
    # --------------------------------
    # end get and set acceleration
    
    
    
    # begin get and set frequency
    # --------------------------------
    @command(dtype_out=int, doc_out='get fmax.') 
    def get_f_max(self):
        # PROTECTED REGION ID(PhytronMCC.read_f_max) ENABLED START #
        if (self.__Axis == 0):
            return (int(self.send_cmd('XP14R')))
        else:
            return (int(self.send_cmd('YP14R')))
        # PROTECTED REGION END #    //  PhytronMCC.read_f_max

    
    @command(dtype_in=int, doc_out='set fmax.')              
    def set_f_max(self, F_Max):
        # PROTECTED REGION ID(PhytronMCC.write_f_max) ENABLED START #
        if (self.__Axis == 0):
            answer = self.send_cmd('XP14S' + str(F_Max))
        else:
            answer = self.send_cmd('YP14S' + str(F_Max))
        # PROTECTED REGION END #    //  PhytronMCC.write_f_max
    # --------------------------------
    # end get and set frequency
    
    
    
    # begin joging functions
    # ----------------------
    @command
    @DebugIt()
    def Jog_Plus(self):
        # PROTECTED REGION ID(PhytronMCC.Jog_Plus) ENABLED START #
        if (self.__Axis == 0):
            answer = self.send_cmd('XL+')
        else:
            answer = self.send_cmd('YL+')
        # PROTECTED REGION END #    //  PhytronMCC.Jog_Plus

    @command
    @DebugIt()
    def Jog_Minus(self):
        # PROTECTED REGION ID(PhytronMCC.Jog_Minus) ENABLED START #
        self.__Last_Read = 0    # Zuruecksetzen
        if (self.__Axis == 0):
            answer = self.send_cmd('XL-')
        else:
            answer = self.send_cmd('YL-')
        # PROTECTED REGION END #    //  PhytronMCC.Jog_Minus
    # --------------------------------
    # end joging functions
    
    
    
    # begin homing functions
    # ----------------------
    @command
    @DebugIt()
    def Homing_Plus(self):
        # PROTECTED REGION ID(PhytronMCC.Homing_Plus) ENABLED START #
        self.__Last_Read = 0    # Zuruecksetzen
        if (self.__Axis == 0):
            answer = self.send_cmd('X0+')
        else:
            answer = self.send_cmd('Y0+')
        # PROTECTED REGION END #    //  PhytronMCC.Homing_Plus

    @command
    @DebugIt()
    def Homing_Minus(self):
        # PROTECTED REGION ID(PhytronMCC.Homing_Minus) ENABLED START #
        if (self.__Axis == 0):
            answer = self.send_cmd('X0-')
        else:
            answer = self.send_cmd('Y0-')
        # PROTECTED REGION END #    //  PhytronMCC.Homing_Minus
    # --------------------------------
    # end homing functions
    
    
    # emergency stop 
    # ----------------
    @command
    @DebugIt()
    def Stop(self):
        # PROTECTED REGION ID(PhytronMCC.Stop) ENABLED START #
            
        if (self.__Axis == 0):
            answer = self.send_cmd('XS')
        else:
            answer = self.send_cmd('YS')    
        self.__Last_Read = 0     
        # PROTECTED REGION END #    //  PhytronMCC.Stop
    # ----------------
    
    
    # set movement unit register R2 
    @command(dtype_in=str,dtype_out=str, doc_in="step\nmm\ninch\ndegree",
            doc_out='the unit')
    @DebugIt()
    def set_movement_unit(self, unit):
        if str.lower(unit) in self.__MOVE_UNIT:
            self.__Unit = str.lower(unit)
            tmp = self.__MOVE_UNIT.index(self.__Unit) + 1
            if (self.__Axis == 0):
                answer = self.send_cmd('XP2S' + str(tmp))
                self.set_display_unit()
            else:
                answer = self.send_cmd('YP2S' + str(tmp))
                self.set_display_unit()      
        else:
            PyTango.Except.throw_exception("PhytronMCC.set_movement_unit", "Allowed unit values are step, mm, inch, degree", "set_movement_unit()")
        self.__Unit = self.get_movement_unit()
        return(self.__Unit)
    
    
    # Read movement unit register R2
    # ------------------------------
    @command(dtype_out = str)
    def get_movement_unit(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP2R')
        else:
            answer = self.send_cmd('YP2R')
        self.__Unit = self.__MOVE_UNIT[int(answer)-1]
       
        return (self.__Unit)
   
    
    # Set spindle_pitch R3
    # --------------------
    @command(dtype_in=float, dtype_out=float, doc_in="spindle pitch (see manual page 50)",
            doc_out='the unit')
    @DebugIt()
    def set_spindle_pitch(self, pitch):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP3S' + str(pitch))
        else:
            answer = self.send_cmd('YP3S' + str(pitch))
        self.__Pitch =  self.get_spindle_pitch()
        self.set_display_unit()
        return(self.__Pitch )
        
    
    
    # Read spindle_pitch R3
    # ----------------------
    @command(dtype_out = float)
    def get_spindle_pitch(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP3R')
        else:
            answer = self.send_cmd('YP3R')
        self.__Pitch = float(answer)
        return float(answer)
    
    
    # Set alias motor name
    # -------------------- 
    @command(dtype_in = str)    
    def set_name(self,mcc_name):
        # PROTECTED REGION ID(PhytronMCC.set_name) ENABLED START #
        self.__Motor_Name = mcc_name
        self.db.put_device_property(self.get_name(),{'Alias':mcc_name})
        # PROTECTED REGION END #    //  PhytronMCC.set_name

   
    # Set running motor current
    # -------------------- 
    @command(dtype_in=int, dtype_out=str, doc_in="motor run current (see manual page 54)",
            )    
    def set_run_current(self, current):
        if current not in range(1,26):
            return 'input not in range 1..25'
        if (self.__Axis == 0):
            answer = self.send_cmd('XP41S' + str(current))
        else:
            answer = self.send_cmd('YP41S' + str(current))
        self.__Run_Current =  self.get_run_current()
        return str(self.__Run_Current)
    
    # Read running motor current
    # ----------------------
    @command(dtype_out = int)
    def get_run_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP41R')
        else:
            answer = self.send_cmd('YP41R')
        self.__Run_Current = int(answer)
        return self.__Run_Current
    
    # Set hold current
    # -------------------- 
    @command(dtype_in=int, dtype_out=str, doc_in="motor hold current (see manual page 54)",
            )    
    def set_hold_current(self, current):
        if current not in range(1,26):
            return 'input not in range 0..25'
        if (self.__Axis == 0):
            answer = self.send_cmd('XP40S' + str(current))
        else:
            answer = self.send_cmd('YP40S' + str(current))
        self.__Hold_Current =  self.get_hold_current()
        return str(self.__Hold_Current)
    
    # Read hold current
    # ----------------------
    @command(dtype_out = int)
    def get_hold_current(self):
        if (self.__Axis == 0):
            answer = self.send_cmd('XP40R')
        else:
            answer = self.send_cmd('YP40R')
        self.__Hold_Current = int(answer)
        return self.__Hold_Current        
    
    # Write to EEProm
    # --------------- 
    @command(dtype_out = str)
    def write_to_eeprom(self):
        # PROTECTED REGION ID(PhytronMCC.set_name) ENABLED START #
        answer = self.send_cmd('SA')
        return 'parameter written to flash memory'
        # PROTECTED REGION END #    //  PhytronMCC.set_name

class PhytronMcc2Class(PyTango.DeviceClass):

    

    class_property_list = {
        }
    
    device_property_list = {
        'CtrlDevice':
        [PyTango.DevString, "The name of the controller Device",
         ["sxr/PhytronMCC2/ctrl01"] ], 
        'Motor':
        [PyTango.DevULong, "The name of the controller Device",
         [0] ],
        'Address':
        [PyTango.DevULong, "The name of the controller Device",
         [0] ],
        'Alias':
        [PyTango.DevString, "The name of the controller Device",
         ["none"] ], 
        }
    
    cmd_list = {}
    
    attr_list = {'position':
                [[PyTango.DevFloat,
                PyTango.SCALAR,
                PyTango.READ_WRITE],
                {
                    'Memorized':"true",
                } ],}
    # ----------
    # Attributes
    # ----------

   
  
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
    
    
    name = attribute(
        dtype='string',
        access= AttrWriteType.READ,
        label="name",
    )   
  

def main():
    #try:
    py = PyTango.Util(sys.argv)
    import PhytronMcc2Ctrl
    try:
        py.add_class(PhytronMcc2Ctrl.PhytronMcc2CtrlClass, PhytronMcc2Ctrl.PhytronMcc2Ctrl,'PhytronMcc2Ctrl')
    except:
        print("Error adding class PhytronMcc2Ctrl,  Device will not be created")
    #
    # the sequence is important, the controller has to start first
    #
    py.add_class(PhytronMcc2Class, PhytronMcc2,'PhytronMcc2')

    #----- PROTECTED REGION END -----#  //  NewFocusPico8742.add_classes

    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()

    #except PyTango.DevFailed as e:
    #    print('-------> Received a DevFailed exception:',e)
    #except Exception as e:
    #    print('-------> An unforeseen exception occured....',e)

if __name__ == '__main__':
    main()

        


    
