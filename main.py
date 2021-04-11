# Send pysense2 sensor data to pybytes

# Copyright (c) 2021, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# See https://docs.pycom.io for more information regarding library specifics
import time
boot_t = time.time()
print('main.py', boot_t, time.ticks_ms())
YELLOW = const(0x080800) # connecting
GREEN  = const(0x000800) # connected
RED    = const(0x080000) # connection failed
PURPLE = const(0x080008) # wait for button
ORANGE = const(0x100500) # maintenance mode

import pycom
from log import *
import uos
uid = binascii.hexlify(machine.unique_id())
name = os.uname().sysname.lower() + '-' + uid.decode("utf-8")[-4:]
print("name", name)

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

def pysense_sensors():
    from SI7006A20 import SI7006A20
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

    from LTR329ALS01 import LTR329ALS01
    lt = LTR329ALS01(py)
    l = lt.light()
    log(cycle, 'luminosity(blue)', l[0], 'Lux')
    log(cycle, 'luminosity(red)', l[1], 'Lux')
    pybytes.send_signal(4, l[0])
    pybytes.send_signal(5, l[1])

    from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE
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

def battery():
    b = round(py.read_battery_voltage(),3)
    p = int(b/5*100)
    log(cycle, 'battery', b, 'V', p, '%')
    pybytes.send_signal(6, b)
    pybytes.send_battery_level(p)

def accelerometer():
    from LIS2HH12 import LIS2HH12
    li = LIS2HH12(py)
    for attempt in range(5):
        a = li.acceleration()
        if a[0]:
            break
        print(attempt, a)
    log(cycle, "Acceleration", a)
    pybytes.send_signal(7, a)
    r = li.roll()
    log(cycle, "Roll", r)
    pybytes.send_signal(8, r)
    p = li.pitch()
    log(cycle, "Pitch", p)
    pybytes.send_signal(9, p)

def pretty_reset_cause():
    mrc = machine.reset_cause()
    if mrc == machine.PWRON_RESET:
        log("reset_cause PWRON_RESET")
        return "P"
    elif mrc == machine.HARD_RESET:
        log("reset_cause HARD_RESET")
        return "H"
    elif mrc == machine.WDT_RESET:
        log("reset_cause WDT_RESET")
        return "W"
    elif mrc == machine.DEEPSLEEP_RESET:
        log("reset_cause DEEPSLEEP_RESET")
        return "D"
    elif mrc == machine.SOFT_RESET:
        log("reset_cause SOFT_RESET")
        return "S"
    elif mrc == machine.BROWN_OUT_RESET:
        log("reset_cause BROWN_OUT_RESET")
        return "B"

def pretty_wake_reason():
    mwr = machine.wake_reason()
    if mwr[0] == machine.PWRON_WAKE:
        log("wake_reason PWRON_WAKE")
        return "P"
    elif mwr[0] == machine.PIN_WAKE:
        log("wake_reason PIN_WAKE")
        return "I"
    elif mwr[0] == machine.RTC_WAKE:
        log("wake_reason RTC_WAKE")
        return "R"
    elif mwr[0] == machine.ULP_WAKE:
        log("wake_reason ULP_WAKE")
        return "U"

def get_rtc():
    # setup rtc
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    utime.sleep_ms(750)
    print('\nRTC Set from NTP to UTC:', rtc.now())
    utime.timezone(7200)
    print('Adjusted from UTC to EST timezone', utime.localtime(), '\n')

def location():
    from L76GNSS import L76GNSS
    l76 = L76GNSS(py, timeout=30)
    for attempt in range(10):
        coord = l76.coordinates()
        if coord[0]:
            break
        print(attempt, coord)
    log('location', coord)
    pybytes.send_signal(14, coord)
    # pybytes.send_signal(15, 'https://www.openstreetmap.org/#map=9/' + str(coord[0]) + '/' + str(coord[1]))
    pybytes.send_signal(15, 'https://www.openstreetmap.org/?mlat='  + str(coord[0]) + '&mlon=' + str(coord[1]))

def button(timeout_ms, verbose=True):
    ct = timeout_ms
    # start_ms = time.ticks_ms()
    s = 100
    while ct > 0:
        if py.button_pressed():
            verbose and print()
            return True
        if verbose and ct % 1000 == 0:
            print(ct, end=' ')
        time.sleep_ms(s)
        ct -= s
    # timeout reached
    verbose and print()
    return False
# print(button(3000))

def maintenance():
    pycom.rgbled(ORANGE)
    log('maintenance')
    from wlan import *
    wlan_connect()
    if not wlan_isconnected():
        print('Failed to establish wifi maintenance connection')
        sys.exit()
    raise Exception('Script stopped in maintenance mode')

def cpu_temp():
    # t = (machine.temperature()-32)/1.8
    t = (cpu_temp_f-32)/1.8
    log(cycle, 'cpu_temp', t)
    pybytes.send_signal(16, t)

def pybytes_start():
    global pybytes_started
    pybytes.start()
    print("pybytes_start", hex(id(pybytes)), pybytes.isconnected())# , (time.ticks_ms()-1)/1000)
    pybytes_started = True

###############################################
# calculate uptime
print('uptime')
try:
    print('s')
    last_sleep_t = pycom.nvs_get('sleep_t')
    print('b')
    last_boot_t = pycom.nvs_get('boot_t')
    print(last_sleep_t, last_boot_t)
    on_s = last_sleep_t - last_boot_t
    print("boot0_t", boot0_t)
    off_s = boot0_t - last_sleep_t
    print('on=', on_s, 'off=', off_s)
    up_p = round(on_s/(off_s+on_s)*100,1)
    print(up_p, '%')
except:
    print('Cannot determine uptime')
    pass
pycom.nvs_set('boot_t', boot0_t)

# check pybytes connection
try:
    print('pybytes (sync)', hex(id(pybytes)), 'conn=', pybytes.isconnected())
    # pybytes has already been loaded on boot
    pybytes_started = True
    if pybytes.isconnected():
        print('pybytes connected')
        pycom.rgbled(GREEN)
    if not pybytes.isconnected():
        print('pybytes not connected')
        pycom.rgbled(RED)
except:
    print('pybytes connecting asynchronously')
    pycom.rgbled(YELLOW)
    pybytes_started = False
    from _pybytes import Pybytes
    from _pybytes_config import PybytesConfig
    conf = PybytesConfig().read_config()
    pybytes = Pybytes(conf)
    print('pybytes (async)', hex(id(pybytes)), 'conn=', pybytes.isconnected())
    import _thread
    _thread.start_new_thread(pybytes_start,())

# set device configurations
config = {
#   name        :  v,     Board,  sleep_s,  method
    "fipy-5220" : [1, 'Pytrack',       20, 'deep' ],
    # "wipy-f38c" : [0, '', ],
    "fipy-01ec" : [1, 'Pysense',      600, 'deep' ],
}
try:
    cfg = config[name]
    print('found config for', name, cfg)
except:
    print('no config for', name, 'try shield2')
    cfg = [2,'']

if cfg[0] == 1:
    from pycoproc_1 import Pycoproc
    # todo, should we rather hardcode
    if cfg[1] == 'Pytrack':
        py = Pycoproc(Pycoproc.PYTRACK)
    elif cfg[1] == 'Pysense':
        py = Pycoproc(Pycoproc.PYSENSE)
    else:
        raise Exception('Unknown board type', cfg[1])
elif cfg[0] == 2:
    from pycoproc_2 import Pycoproc
    py = Pycoproc()
    pid = py.read_product_id()
    if pid == Pycoproc.USB_PID_PYTRACK:
        cfg[1] = 'Pytrack'
    elif pid == Pycoproc.USB_PID_PYSENSE:
        cfg[1] = 'Pysense'
    else:
        raise Exception('PID not supported', pid)
else:
    raise Exception('Unknown shield version', cfg[0])
# configure deepsleep time
sleep_s =   60 # 1 min
sleep_s =  600 # 10 min
sleep_s = 1800 # 30 min
# sleep method
sleep_m = 'pic'
try:
    sleep_s = cfg[2]
    sleep_m = cfg[3]
except:
    pass
# read configuration from nvs
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

# log status and configuration
msg = name + ' ' + cfg[1] + '_' +str(cfg[0])
msg += ' pid:' + hex(py.read_product_id())
msg += ' hw:' + str(py.read_hw_version())
msg += ' fw:' + str(py.read_fw_version())
msg += ' cycle:' + str(cycle)
msg += ' t:' + str(boot_t)
try:
    msg += ' on:' + str(on_s) + ' off:' + str(off_s) + ' up:' + str(up_p) + '%'
except:
    pass
msg += ' wifi:' + str(has_wifi())
msg += ' reset:' + pretty_reset_cause()
msg += ' wake:' + pretty_wake_reason()
if do_sleep:
    msg += ' sleep:' + str(sleep_s) + ' ' + sleep_m
log(cycle, msg)

to = 5000
print('Press button to stop script within', to, 'ms')
pycom.rgbled(PURPLE)
if button(to):
    maintenance()

# check/ wait for async pybytes connection
# TOOD: we could start to collect sensor data already
# but that would take some refactoring to decouple getting sensor data and sending it
if not pybytes_started:
    print('Wait for pybytes start')
    while not pybytes_started:
        if button(100, False):
            maintenance()
        print('.', end='')
    print()
log(cycle, 'pybytes', hex(id(pybytes)), pybytes_started, pybytes.isconnected())
if pybytes.isconnected():
    pycom.rgbled(GREEN)
else:
    pycom.rgbled(RED)

print('Collect sensor data')
pybytes.send_signal(13, msg)
try:
    pybytes.send_signal(17, up_p)
except:
    pass
cpu_temp()
if cfg[1] == 'Pytrack':
    location()
    battery()
    accelerometer()

elif cfg[1] == 'Pysense':
    pysense_sensors()
else:
    raise Exception('Board not supported', cfg[1])

log(cycle, 'done')
pycom.nvs_set('nextcycle', cycle+1)

if do_sleep:
    to = 20000

    # wait for user button to stop the sleep/wake cycle
    # and give pybytes/mqtt some time to finish sending
    print('Press button to stop script within', to, 'ms')
    pycom.rgbled(PURPLE)
    if button(to):
        maintenance()

    log(cycle, 'sleep', sleep_s, 's', time.time()-boot_t)
    pycom.nvs_set('sleep_t', time.time())
    time.sleep_ms(10)
    if sleep_m == 'pic':
        py.setup_sleep(sleep_s)
        py.go_to_sleep()
    elif sleep_m == 'deep':
        machine.deepsleep(sleep_s * 1000)
