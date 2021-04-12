# import sys
import time
import machine
# import pycom
# from log import *

# print(sys.path)
# if '/flash/shell' not in sys.path:
#     sys.path.append('/flash/shell')
# from net import *

# from wlan import *
# wlan_connect()

# log('rtc_ntp_sync')
# rtc_ntp_sync()
# print(time.time())
# log('gmt:', pretty_gmt(do_return=True))

print('\nStarting LoRaWAN concentrator')

# # Define callback function for Pygate events
# def machine_cb (arg):
#     evt = machine.events()
#     if (evt & machine.PYGATE_START_EVT):
#         # Green
#         # pycom.rgbled(0x001100)
#         print('PYGATE_START_EVT', arg)
#     elif (evt & machine.PYGATE_ERROR_EVT):
#         # Red
#         pycom.rgbled(0x110000)
#         print('PYGATE_ERROR_EVT', arg)
#     elif (evt & machine.PYGATE_STOP_EVT):
#         # RGB off
#         pycom.rgbled(0x000000)
#         print('PYGATE_STOP_EVT', arg)
#
# # register callback function
# machine.callback(trigger = (machine.PYGATE_START_EVT | machine.PYGATE_STOP_EVT | machine.PYGATE_ERROR_EVT), handler=machine_cb)

# Read the GW config file from Filesystem
with open('/flash/pygate_config.json','r') as c:
    buf = c.read()

# Start the Pygate
machine.pygate_init(buf)
# disable degub messages
# machine.pygate_debug_level(1)
machine.pygate_debug_level(0)
