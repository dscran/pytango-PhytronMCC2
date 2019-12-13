#!/bin/bash

# 28.2.2019
# Wrapper zum Starten von PySerialDS.py 
# und PhytronMcc2.py 


# Exportieren der Variable TANGO_HOST fuer die Bash-Shell

export TANGO_HOST=ampere.sxr.lab:10000

TANGOHOST=ampere.sxr.lab

#Umleiten der Ausgabe in eine Log-Datei
exec &>> /home/pi/Tango_Devices/MCC2/device.log

echo "---------------------------"
echo $(date)
echo "Tangohost: " $TANGOHOST

# Warten bis der Tangohost sich meldet
while ! timeout 0.2 ping -c 1 -n $TANGOHOST &> /dev/null
do
  :
# mache nix  
done

echo "ping Tangohost successful!"
echo "starting PhytronMCC2 device"

# Fork/exec
(
  exec /usr/bin/python /home/pi/Tango_Devices/MCC2/PhytronMCC2.py mcc01 &
) 
&>> /home/pi/Tango_Devices/MCC2/device.log 

if pgrep -fl "PhytronMcc2.py";
then 
(
  echo "starting PhytronMcc2 successful!"
)
fi

exit 0
