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
import sys
print(sys.path)
if '/flash/shell' not in sys.path:
    sys.path.append('/flash/shell')

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
    for attempt in range(2):
        try:
            mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters.
            t = round(mp.temperature(),1)
            log(cycle, 'temperature', t, 'C')
            pybytes.send_signal(10, t)
            a = mp.altitude()
            log(cycle, 'altitude', a)
            pybytes.send_signal(11, a)
            break
        except:
            log('MPL3115A2 read failed')

    mp = MPL3115A2(py, mode=PRESSURE) # Returns a value in Pascals
    p = mp.pressure()
    log(cycle, 'pressure', round(p/100,1), 'hPa', round(p/100_000,1), 'bar')
    pybytes.send_signal(12, round(p/100_000,2))

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

def cpu_temp(t_f=None):
    if t_f is None:
        t = (machine.temperature()-32)/1.8
    else:
        t = (cpu_temp0_f-32)/1.8
    log(cycle, 'cpu_temp', t)
    pybytes.send_signal(16, t)

def pybytes_start():
    global pybytes_started
    pybytes.start()
    print("pybytes_start", hex(id(pybytes)), pybytes.isconnected())# , (time.ticks_ms()-1)/1000)
    pybytes_started = True

def pybytes_wait_started():
    # check/ wait for async pybytes connection
    # TOOD: we could start to collect sensor data already
    # but that would take some refactoring to decouple getting sensor data and sending it
    if not pybytes_started:
        print('Wait for pybytes start')
        while not pybytes_started:
            if py:
                if button(100, False):
                    maintenance()
            else:
                time.sleep(1)
            print('.', end='')
        print()
        log(cycle, 'pybytes', hex(id(pybytes)), pybytes_started, pybytes.isconnected())

def status():
    global status_ct_not_connected
    try:
        log(cycle, 'gmt:', pretty_gmt(do_return=True), time.ticks_ms())
    except Exception as e:
        log('time:', time.time(), e )
    log('pybytes', pybytes.isconnected())
    try:
        h = http_get(kb=100, limit_b=100_000) # this takes approx 30s ... is it too much? but 10k shows a much higher network speed, maybe not representative
        print(h)
        if h[0]:
            log('connected (http_get)', h)
            status_ct_not_connected = 0
            pybytes.send_signal(18, h[6]/1000)
        else:
            status_ct_not_connected += 1
            log('not connected (ct={})'.format(status_ct_not_connected), h)
            pybytes.send_signal(18, -1)
    except Exception as e:
        log('http_get failed', e)
    try:
        cpu_temp()
    except Exception as e:
        print('no cpu ({})'.format(e))

def status_loop(interval_s=600):
    global status_loop_run
    status_loop_run = True
    log('starting status_loop', interval_s)
    while status_loop_run:
        status()
        for t in range(interval_s):
            time.sleep(1)

###############################################
# calculate uptime
print('uptime')
try:
    # print('s')
    last_sleep_t = pycom.nvs_get('sleep_t')
    # print('b')
    last_boot_t = pycom.nvs_get('boot_t')
    print(last_sleep_t, last_boot_t)
    on_s = last_sleep_t - last_boot_t
    print("boot0_t", boot0_t)
    off_s = boot0_t - last_sleep_t
    print('on=', on_s, 'off=', off_s)
    up_p = round(on_s/(off_s+on_s)*100,1)
    print(up_p, '%')
except Exception as e:
    print('Cannot determine uptime ({})'.format(e))
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
def_config = {'v':2, 'b':'Pysense', 'st':1800, 'sm':'pic', 'nets':['wifi'], 'pybytes_on_boot':False}
config = {
#   name        :  v,     Board,  sleep_s,  method
    "fipy-0220" : {                       },
    "fipy-5220" : {'v':1, 'b':'Pytrack', 'st':20,  'sm':'deep' },
    "wipy-f38c" : {       'b':'Pygate',            'sm':'no'},
    "fipy-01ec" : {'v':1, 'b':'Pysense', 'st':600, 'sm':'deep' }
}
self_config = config.get(name)

def cfg(key=None):
    if key is None:
        return self_config
    else:
        if self_config:
            v = self_config.get(key)
            if v is not None:
                return v
        # otherwise return default
        return def_config[key]

if cfg('pybytes_on_boot') != pycom.pybytes_on_boot():
    b = cfg('pybytes_on_boot')
    print('fix pybytes_on_boot config ({}) and reboot'.format(b))
    pycom.pybytes_on_boot(b)
    time.sleep(1)
    machine.reset()

board_ver = cfg('v')
board = cfg('b')
py = None
if board == 'Pygate':
    board_ver_str = ''
else:
    if board_ver == 1:
        from pycoproc_1 import Pycoproc
        if board == 'Pytrack':
            py = Pycoproc(Pycoproc.PYTRACK)
        elif board == 'Pysense':
            py = Pycoproc(Pycoproc.PYSENSE)
        else:
            raise Exception('Unknown board type', b)
    elif board_ver == 2:
        from pycoproc_2 import Pycoproc
        py = Pycoproc()
        pid = py.read_product_id()
        if pid == Pycoproc.USB_PID_PYTRACK:
            board = 'Pytrack'
        elif pid == Pycoproc.USB_PID_PYSENSE:
            board = 'Pysense'
        else:
            raise Exception('PID not supported', pid)
    else:
        raise Exception('Unknown shield version', board_ver)
    board_ver_str = '_' + ' pid:' + hex(py.read_product_id()) + ' hw:' + str(py.read_hw_version()) + ' fw:' + str(py.read_fw_version())

sleep_s = cfg('st')
sleep_m = cfg('sm')
# read configuration from nvs
cycle = 0
try:
    cycle = pycom.nvs_get('nextcycle')
except:
    pass

# log status and configuration
msg = name + ' ' + board + board_ver_str
msg += ' cycle:' + str(cycle)
msg += ' t:' + str(boot_t)
try:
    msg += ' on:' + str(on_s) + ' off:' + str(off_s) + ' up:' + str(up_p) + '%'
except:
    pass
np = pybytes.get_config('network_preferences')
msg += ' nets[{}]:'.format(len(np))
for n in np:
    if n == 'lora_otaa':
        msg += 'Lo'
    elif n == 'wifi':
        msg += 'w'
    else:
        msg += n
msg += ' reset:' + pretty_reset_cause()
msg += ' wake:' + pretty_wake_reason()
msg += ' sleep:' + str(sleep_m) + ':' + str(sleep_s)
log(cycle, msg)

# wait for button/maintenance mode
if py:
    to = 5000
    print('Press button to stop script within', to, 'ms')
    pycom.rgbled(PURPLE)
    if button(to):
        maintenance()

pybytes_wait_started()
if pybytes.isconnected():
    pycom.rgbled(GREEN)
else:
    pycom.rgbled(RED)

print('Start main function')
pybytes.send_signal(13, msg)
try:
    pybytes.send_signal(17, up_p)
except:
    pass
cpu_temp(cpu_temp0_f)
status()
if board == 'Pygate':
    from net import *
    log('rtc_ntp_sync')
    rtc_ntp_sync()
    print(time.time())
    log('gmt:', pretty_gmt(do_return=True))
    print('\nStarting LoRaWAN concentrator')

    # Read the GW config file from Filesystem
    with open('/flash/pygate_config.json','r') as c:
        buf = c.read()

    # Start the Pygate
    machine.pygate_init(buf)

    # wait some seconds for initial startup messages from pygate
    time.sleep(12)

    # now announce start and wait a little longer to get at least one or two info blocks
    w = 60
    print('wait', w, 's for Pygate to settle')
    time.sleep(w)

    machine.pygate_debug_level(0)
    print()
    log('pygate is running, setting pygate_debug_level(0)')

    _thread.start_new_thread(status_loop,())
    if False:
        # to stop it run:
        machine.pygate_deinit()
        # to change debug level
        print(machine.pygate_debug_level())
        # machine.pygate_debug_level(0) # off
        # machine.pygate_debug_level(1)
        machine.pygate_debug_level(2) # warn:
        machine.pygate_debug_level(3) # info: regular blocks and RSSI
elif board == 'Pytrack':
    location()
    battery()
    accelerometer()
elif board == 'Pysense':
    battery()
    pysense_sensors()
else:
    raise Exception('Board not supported', board)

log(cycle, 'done')
pycom.nvs_set('nextcycle', cycle+1)

if sleep_m == 'no':
    log('not sleeping')
    # do nothing
    pass
else:
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
