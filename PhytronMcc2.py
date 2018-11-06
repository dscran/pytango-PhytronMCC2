#!/usr/bin/python -u
# coding: utf8
# Phytron MotorDevice
# 17.10. 1. Test im Lab, Festlegung von Verbesserungen/Aenderungen
# Aenderungen:
# ------------
# 18.10. 
# Die Module werden noch einmal nach Achsen unterteilt
# Beschreibung:
# -------------
# Device: hhg/MCC2/0.0
# Bedeutung: 1. Ziffer ist die Moduladresse auf dem Bus
#            2. Ziffer der Motor
# In dem Fall: Rs485-Adresse=0 (Modul 1), Motor: 0 (oberer Stecker)
# oder  Device: hhg/MCC2/1.1 entspricht: Modul 2, Motor 1 (unterer Stecker)
#                 
# 19.10.
# 1) Acceleration und max. Frequenz werden als Kommando implementiert
#    Hintergrund: - werden wenig benutzt, in der regel nur einmal eingestellt,
#                  deshalb mit get/set veraendert
# 

from PyTango.server import run
from PyTango import DebugIt
from PyTango.server import Device, DeviceMeta, device_property
from PyTango.server import attribute, pipe, command, class_property
from tango import AttrQuality, AttrWriteType, DispLevel, DeviceProxy
import tango
import PyTango
import time
import os
import sys

flagDebugIO = 0


class PhytronMcc2(Device): 
    __metaclass__ = DeviceMeta

    # Auslesen des Control-Device aus der Property-Liste
    # Auslesen der Achse 0/1 (ein Modul kann 2 Motore steuern)
    # Auslesen welche Adresse das Modul hat (0..15)
    
    # -----------------
    # Device Properties
    # -----------------

    CtrlDevice = device_property(
        dtype='str', default_value=""
    )
    
    Motor = device_property(
        dtype='int16'
    )
    
    Address = device_property(
        dtype='int16'
    )
     
# Definition einiger Konstanten
 
    __STX     = chr(2)    # Start of text
    __ACK     = chr(6)    # Command ok
    __NACK    = chr(0x15) # command failed
    __ETX     = chr(3)    # end of text
    __SE      = 'SE'      # Lesen erweiterter Status

# Konstante fuer &-Verknuepfung des Status
  #  __HOME     = 2     # Ref.pkt wurde angefahren
    __MOVE     = 1     # Motor bewegt sich, dann Bit = 1
    __LIM_PLUS  = 2
    __LIM_MINUS = 1

# private Status-Variablen, werden von My_State aktualisiert    
    __Limit_Minus = False
    __Limit_Plus  = False
    __Motor_Run   = False
    #__Ref         = False

# private Flag-Variable die das letzte Abfragen der Achse durch den Client anzeigt    
    __Last_Read = 0 

# Private Variable zum Speichern der Position
     
    # Zuweisen des Wertes von Property "Address" (RS485 Adresse des Moduls)
    __Addr          = 0
    
    # Zuweisen des Wertes von Property "Motor" (welche Achse)
    __Axis          = 0
    
    # ab Firmware V3.0 haben sich 2 Register geaendert
    # M0P   = mechan. Nullpunktzaehler, wird beim Homming (X0+/-) auf Null gesetzt
    # EL0P  = el. Nullpunktzaehler, wird nicht automatisch auf Null gesetzt
    # Firmware < V3.0:  P21 = MOP, P20 = EL0P
    # Firmware > V3.0:  P20 = M0P, P21 = EL0P
    
    __REG_STEP_CNT = 'P20'
    
    __Pos = 0
    
    # Initialisieren des Devices
    def init_device(self):
        Device.init_device(self)
        
        self.proxy = PyTango.DeviceProxy(self.get_name())
        
        if flagDebugIO:
            print("Get_name: %s" % (self.get_name()))
        
        self.__Addr = self.Address
        self.__Axis = self.Motor

        
        if flagDebugIO:
            print "Ctrl.Device:  %s" %( self.CtrlDevice)
            print "Modul Adresse: ",self.__Addr
            print "Motor: ",self.__Axis
            
        try:
            self.ctrl = PyTango.DeviceProxy( self.CtrlDevice)
        except:
            print "PhytronMcc2.init_device: failed to create proxy to %s" % (self.CtrlDevice)
            sys.exit( 255)
        
        # Testen ob das CtrlDevice ON ist und wenn nicht ser. Schnittstelle oeffnen
        if str(self.ctrl.state()) == "OFF":
            self.ctrl.Open()
        
            
        self.set_state(PyTango.DevState.ON)
        self.read_my_state()
        self.read_position()
        self.__Last_Read = 0 
        if flagDebugIO:
            print "Limit-: ",self.__Limit_Minus
            print "Limit+: ",self.__Limit_Plus
            print "Run: ",self.__Motor_Run
            print "Postion: ", self.__Pos
        
    def delete_device(self):
        # PROTECTED REGION ID(PhytronMCC.delete_device) ENABLED START #
        self.set_state(PyTango.DevState.OFF)
        # PROTECTED REGION END #    //  PhytronMCC.delete_device
        
        
    # ----------
    # Attributes
    # ----------

    my_state = attribute(
        dtype=('bool',),#polling_period=500,
        max_dim_x=3,
    )
  
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
        dtype=float,#polling_period=2000,
        format='%8.3f',
        access=AttrWriteType.READ_WRITE,
        label="Position",
    )
    
   
  
    # ------------------
    # Attributes methods
    # ------------------
    def read_my_state(self):
        # PROTECTED REGION ID(PhytronMCC.my_state_read) ENABLED START #
        #if self.__Last_Read == 0:
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
        #     self.__Last_Read = 1
        # print "poll Status---------" 
        # print "Adr: ", self.__Addr
        # print "Motor: ", self.__Axis
        # 

        return ([self.__Limit_Minus, self.__Limit_Plus, self.__Motor_Run])
                 
        # PROTECTED REGION END #    //  PhytronMCC.my_state_read


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

    def read_ref(self):
        # PROTECTED REGION ID(PhytronMCC.run_read) ENABLED START #
        return self.__Ref
        # PROTECTED REGION END #    //  PhytronMCC.run_read

    def read_position(self):
        # PROTECTED REGION ID(PhytronMCC.position_read) ENABLED START #
        #if (self.__Last_Read == 0):
        if (self.__Axis == 0):
            tmp = self.send_cmd('X' + self.__REG_STEP_CNT +'R')
            self.__Pos = float(tmp)
        else:
            tmp = self.send_cmd('Y' + self.__REG_STEP_CNT +'R')
            self.__Pos = float(tmp)
        self.read_my_state() 
        # print "poll Pos---------" 
        # print "Adr: ", self.__Addr
        # print "Motor: ", self.__Axis
        return (self.__Pos)
            
        # PROTECTED REGION END #    //  PhytronMCC.position_read

    def write_position(self, value):
        # PROTECTED REGION ID(PhytronMCC.position_write) ENABLED START #
        
        self.__Last_Read = 0    # Zuruecksetzen
        
        if (self.__Axis == 0):
            answer = self.send_cmd('XA{:.4f}'.format(value))
        else:
            answer = self.send_cmd('YA{:.4f}'.format(value))
        self.set_state(PyTango.DevState.MOVING)
        # PROTECTED REGION END #    //  PhytronMCC.position_write

    

    # -------------
    # Pipes methods
    # -------------

  
    # --------
    # Commands
    # --------

    # Communication    
    @command(dtype_in=str, dtype_out=str, doc_in='enter a command', doc_out='the answer')    
    def send_cmd(self,cmd):
        # den String zum Senden zusammen bauen
        s = self.__STX + str(self.__Addr) + cmd  + self.__ETX
        # senden
        # self.ctrl.Write(s)
        temp=self.ctrl.WriteRead(s)
        answer = temp.tostring()
        if self.__ACK in answer:
            tmp =  answer.lstrip(self.__STX).lstrip(self.__ACK).rstrip(self.__ETX)   
        else:
            tmp = "Command error!"
        # 50ms Warten
        #time.sleep(0.05)
        #tmp= self.read_cmd()
        return (tmp)
        
        
    @command(dtype_out=str, doc_out='the answer')    
    def read_cmd(self):
        tmp= self.ctrl.Read(1024)
        answer = tmp.tostring()
        if self.__ACK in answer:
            tmp =  answer.lstrip(self.__STX).lstrip(self.__ACK).rstrip(self.__ETX)   
        else:
            tmp = "Command error!"
        return (tmp)
    
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
    
    # Lesen der max. Frequenz
    @command(dtype_out=int, doc_out='get fmax.') 
    def get_f_max(self):
        # PROTECTED REGION ID(PhytronMCC.read_f_max) ENABLED START #
        if (self.__Axis == 0):
            return (int(self.send_cmd('XP14R')))
        else:
            return (int(self.send_cmd('YP14R')))
        # PROTECTED REGION END #    //  PhytronMCC.read_f_max

    # Setzen der max. Frequenz
    @command(dtype_in=int, doc_out='set fmax.')              
    def set_f_max(self, F_Max):
        # PROTECTED REGION ID(PhytronMCC.write_f_max) ENABLED START #
        if (self.__Axis == 0):
            answer = self.send_cmd('XP14S' + str(F_Max))
        else:
            answer = self.send_cmd('YP14S' + str(F_Max))
        # PROTECTED REGION END #    //  PhytronMCC.write_f_max
        
    @command
    @DebugIt()
    def Jog_Plus(self):
        # PROTECTED REGION ID(PhytronMCC.Jog_Plus) ENABLED START #
        self.__Last_Read = 0    # Zuruecksetzen
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
        self.__Last_Read = 0    # Zuruecksetzen
        if (self.__Axis == 0):
            answer = self.send_cmd('X0-')
        else:
            answer = self.send_cmd('Y0-')
        # PROTECTED REGION END #    //  PhytronMCC.Homing_Minus

    
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

    

if __name__ == "__main__":    
    if flagDebugIO:
        print(tango.ApiUtil.get_env_var("TANGO_HOST"))
    
    run((PhytronMcc2,))
    


    
