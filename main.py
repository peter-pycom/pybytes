# Send pysense2 sensor data to pybytes

# Copyright (c) 2021, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# See https://docs.pycom.io for more information regarding library specifics
import pycom
pycom.heartbeat(False)
pycom.rgbled(0x000800)

import time
ts = time.time()

cycle = 0
try:
    cycle = pycom.nvs_get('nextcycle')
except:
    pass

do_sleep = True
try:
    do_sleep = pycom.nvs_get('do_sleep')
except:
    pass

from log import *

import uos
# import _thread

from pycoproc_2 import Pycoproc
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE

def pbyytes_has_wifi():
    try:
        np = pybytes.get_config('network_preferences')
        return 'wifi' in np
    except:
        return 'na'

def pybytes_enable_wifi():
    np = pybytes.get_config('network_preferences')
    if 'wifi' in np:
        pass
    else:
        np.append('wifi')
        pybytes.set_config('network_preferences', np)

def pybytes_disable_wifi():
    np = pybytes.get_config('network_preferences')
    if 'wifi' in np:
        pybytes.set_config('network_preferences', ['lora_otaa'])

def enable_sleep():
    do_sleep = True
    pycom.nvs_set('do_sleep', do_sleep)

def disable_sleep():
    do_sleep = False
    pycom.nvs_set('do_sleep', do_sleep)

def reset_kpis():
    print('fixme')
    # delete cycle,
    # ? boot_t boot0_t sleep_t

def send_pysense_data():
    si = SI7006A20(py)
    h = round(si.humidity(),1)
    log(cycle, 'humidity', h, '%')
    pybytes.send_signal(1, h)
    t = round(si.temperature(),1)
    log(cycle, 'temperature', t, 'C')
    pybytes.send_signal(2, t)
    d = round(si.dew_point(),3)
    log(cycle, 'dew', d)
    pybytes.send_signal(3, d)

    lt = LTR329ALS01(py)
    l = lt.light()
    log(cycle, 'luminosity(blue)', l[0], 'Lux')
    log(cycle, 'luminosity(red)', l[1], 'Lux')
    pybytes.send_signal(4, l[0])
    pybytes.send_signal(5, l[1])

    b = round(py.read_battery_voltage(),1)
    log(cycle, 'battery', b, 'V')
    pybytes.send_signal(6, b)

    li = LIS2HH12(py)
    a = li.acceleration()
    log(cycle, "Acceleration", a)
    pybytes.send_signal(7, a)
    r = li.roll()
    log(cycle, "Roll", r)
    pybytes.send_signal(8, r)
    p = li.pitch()
    log(cycle, "Pitch", p)
    pybytes.send_signal(9, p)

    mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters.
    t = round(mp.temperature(),1)
    log(cycle, 'temperature', t, 'C')
    pybytes.send_signal(10, t)
    a = mp.altitude()
    log(cycle, 'altitude', a)
    pybytes.send_signal(11, a)

    mp = MPL3115A2(py, mode=PRESSURE) # Returns a value in Pascals
    p = mp.pressure()
    log(cycle, 'pressure', round(p/100,1), 'hPa', round(p/100_000,1), 'bar')
    pybytes.send_signal(12, round(p/100_000,1))

###############################################
sleep_s =   60 # 1 min
sleep_s =  600 # 10 min
sleep_s = 1800 # 30 min
msg = 'start C=' + str(cycle) + ' ts=' + str(ts) + ' c=' + str(pybytes.isconnected()) + ' w=' + str(has_wifi()) + ' s=' + str(do_sleep) + str(sleep_s)
log(cycle, msg)
pybytes.send_signal(13, msg)
py = Pycoproc()
pid = py.read_product_id()
if pid == Pycoproc.USB_PID_PYTRACK:
    print('Pytrack') #, hex(py.read_))
elif pid == Pycoproc.USB_PID_PYSENSE:
    print('Pysense')
    send_pysense_data()
else:
    raise Exception('PID not supported', pid)

log(cycle, 'done')
pycom.rgbled(0x080800) # yellow
pycom.nvs_set('nextcycle', cycle+1)

if do_sleep:
    sleep = True
    S = 20
    print('wait', S, 's')
    # wait for user button to stop the sleep/wake cycle and give pybytes some time to finish sending
    for s in range(S*10,0,-1):
        if s % 10 == 0:
            print(s)
        if py.button_pressed():
            log(cycle, 'stop')
            pycom.rgbled(0x0a0700) # orange
            sleep = False
            break
        time.sleep_ms(100)

    if sleep:
        log(cycle, 'sleep', sleep_s, 's', time.time()-ts)
        pycom.rgbled(0x000008) # blue
        time.sleep(1)
        py.setup_sleep(sleep_s)
        py.go_to_sleep()
