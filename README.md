
# Phytron MCC2 Tango device server

This a Tango device server written in PyTango for a Phytron MCC2 stepper motor controller using the RS485 serial interface.
It consits of a PhytronMCC2Ctrl device server that handles the communication with the RS485 bus and one to many PhytronMCC2Axis device servers implementing the actual interface to the stepper axis.

## Getting Started

This Tango device server is meant to run on a Raspberry PI connected to the Phytron MCC2 modules via a RS485 serial to USB converter.

## Installation

### USB Serial converter

Create a udev rule in order to mount the USB Serial converter always under the same link, e.g. `/dev/ttyMCC`

First check the VendorID, ProductID, and SerialNumber using `dmesg`
Then add a new udev rule
    
    sudo nano /etc/udev/rules.d/55-usbcom.rules
    SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="A106K4W0", SYMLINK+="ttyMCC", MODE="0666"

Relaod and apply the udev rule by

    sudo udevadm control --reload
    sudo udevadm trigger --action=add


### Jive Server Wizard
In order to create the PhytronMCC2 device servers in the TangoDB use **Jive** and **Tools/Server Wizard**
The **Server name** is the name of the python script (without .py) that needs to be started

    PhytronMCC2

The **Instance name** is the argument that needs to be given when running the script above. Lets use the hostname of the Raspi as instance name, e.g.

    mcc01

With in the **Class Selection** you find the two different classes for the controller and axis. First select the **PhytronMCC2Ctrl** class and click **Declare Device**.
As a **Device name**, which must be a unique identifier within the Tango DB, use the following syntax:

    Domain/Family/Member
  
So in this case lets use

    sxr/PhytronMCC2/ctrl01

Click next and add the correct values for the **baudrate** and **port**.
Before clicking *Finish* use the *New Class* button to define/configure one or multiple **PhytronMCC2Axis** 
Set the **Device Name**:

    sxr/PhytronMCC2/ctrl01_axis_0_0
or

    sxr/PhytronMCC2/MyMotorAlias

Remember that the Device name needs to be unique!
Enter the following properties accordingly.
- Alias: something that describes your motor axis
- Axis 0/1: index of the axis on the selected MCC2 module
- Address 0-5: index of the MCC2 module in the controller
- CtrlDevice: Device name of the PhytronMCC2Ctrl linked to the axis,

e.g.

    sxr/PhytronMCC2/ctrl01

### Systemd Service

Copy the file `tango_mcc2.service` to `/etc/systemd/system` and make it executable `sudo chmod +x tango_mcc2.service`.
Check that the paths and are set correctly in the file. Then enable it as a system service by:

    sudo systemctl daemon-reload 
    sudo systemctl start tango_mcc2.service
    sudo systemctl enable tango_mcc2.service

## Authors

* **Dirk Rohloff**
* Daniel Schick


