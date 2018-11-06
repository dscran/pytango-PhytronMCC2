#!/bin/bash

# 10.10.2018
# Wrapper zum Starten von PySerialDS.py 
# und PhytronMcc2.py 


# Exportieren der Variable TANGO_HOST fuer die Bash-Shell

#export TANGO_HOST=angstrom:10000
export TANGO_HOST=10.6.16.78:10000

#TANGOHOST=angstrom
TANGOHOST=10.6.16.78

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
echo "starting PySerialDS device"

# Fork/exec
(
  exec /usr/bin/python /home/pi/Tango_Devices/MCC2/PySerialDS.py hhg &
) 
&>> /home/pi/Tango_Devices/MCC2/device.log 

sleep 1

# Testen, ob der PySerialDS- Prozess laeuft, 
# dann das Achsen-Device starten

if pgrep -fl "PySerialDS.py";
then 
(
  echo "starting PhytronMcc2"
  exec /usr/bin/python /home/pi/Tango_Devices/MCC2/PhytronMcc2.py hhg &
) 
&>> /home/pi/Tango_Devices/MCC2/device.log  
fi

if pgrep -fl "PhytronMcc2.py";
then 
(
  echo "starting PhytronMcc2 successful!"
)
fi

exit 0
