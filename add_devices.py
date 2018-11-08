# Register Phytron-devices automatically in the database of Tangohost
# and also set the right properties

from PyTango import Database, DbDevInfo, DeviceProxy


db = Database()


number_of_axis = 5

new_device =[]

new_device_info_mcc = DbDevInfo()
new_device_info_mcc._class = "PhytronMcc2"
new_device_info_mcc.server = "PhytronMcc2/hhg"



for i in range(number_of_axis):
    if not i%2:
        new_device.append ("hhg/MCC2/"+ str((i)/2) + "." + "0")
        
    else:
        new_device.append ("hhg/MCC2/"+ str((i)/2) + "." + "1")
    
    print("Creating device: %s" %new_device[i])
    # new_device_info_mcc.name = new_device[i]
    # db.add_device(new_device_info_mcc)
    # 
    
# now we create the properties    
property_names = ['Address','Motor','CtrlDevice']
property_values = []

# for i in range(number_of_axis):
#     if not i%2:
#         axis = DeviceProxy("hhg/MCC2/"+ str((i)/2) + "." + "0")
#         axis_prop = axis.get_property(property_names)
#         
#         for prop in axis_prop:
#             axis_prop[prop]= i/2
#             print (prop)
#             
#     else:
#         axis = DeviceProxy("hhg/MCC2/"+ str((i)/2) + "." + "1")
#         axis.get_property(property_names)
#         for prop in axis_prop:
#             print (prop)
# print axis_prop

prop_dict ={}
for i in range(number_of_axis):
    if not i%2:
        property_values[i] =  i/2
        property_values[i+1] =  0
        property_values[i+2] = "hhg/SerialDS/1"
       
    else:
        property_values[i] =  i/2
        property_values[i+1] =  1
        property_values[i+2] = "hhg/SerialDS/1"


# prop_dict = zip(property_names,property_values)
# for k,v in prop_dict.items():
#     print k,v