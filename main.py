# pybytes examples

# this script can
# - collect sensor data (pytrack/pysense) or
# - run a pygate
# and send KPI's to pybytes
# adjust the 'config' variable for your device:
# - board: pysense/pytrack v1 or 2 or pygate
# - sleep: time in seconds and method (pic/deep)
# - pybytes: use it or not

# Note you can set pybytes_on_boot() to True or False, the script will lazy load if needed.
# Conversely, pybytes_autostart(False) doesn't make sense. pybytes_load() takes a couple of seconds and is needed either way

import time
boot_s = time.time()
print('main.py', boot_s, time.ticks_ms())

GREEN  = const(0x000800) # connected
YELLOW = const(0x080800) # connecting
BLUE   = const(0x080000) # not connected
RED    = const(0x080000) # connection failed
PURPLE = const(0x080008) # wait for button
ORANGE = const(0x100500) # maintenance mode

import pycom
from log import *
import uos
uid = binascii.hexlify(machine.unique_id())
name = os.uname().sysname.lower() + '-' + uid.decode("utf-8")[-4:]
print("name", name)
import math
import struct
import sys
try:
    lib_shell='/flash/lib_shell'
    os.stat(lib_shell)
    if lib_shell not in sys.path:
        sys.path.append(lib_shell)
        print(sys.path)
    from net import *
except Exception as e:
    print(e)

def sleep(s):
    while s > 0:
        time.sleep(1)
        s -= 1

def haversine(lat1, lon1, lat2, lon2):
	# distance between latitudes
	# and longitudes
	dLat = (lat2 - lat1) * math.pi / 180.0
	dLon = (lon2 - lon1) * math.pi / 180.0

	# convert to radians
	lat1 = (lat1) * math.pi / 180.0
	lat2 = (lat2) * math.pi / 180.0

	# apply formulae
	a = (pow(math.sin(dLat / 2), 2) +
		pow(math.sin(dLon / 2), 2) *
			math.cos(lat1) * math.cos(lat2));
	rad = 6371
	c = 2 * math.asin(math.sqrt(a))
	return rad * c

def reset_stats():
    try:pycom.nvs_erase('boot_s')
    except:pass
    try:pycom.nvs_erase('sleep_s')
    except:pass
    try:pycom.nvs_erase('nextcycle')
    except:pass
    try:pycom.nvs_erase('gps_lat')
    except:pass
    try:pycom.nvs_erase('gps_lon')
    except:pass
    try:pycom.nvs_erase('gps_sec')
    except:pass
    try:os.unlink('coord.csv')
    except:pass
    try:os.unlink('log.csv')
    except:pass
    if False:
        rmlog()

def pysense_sensors():
    from SI7006A20 import SI7006A20
    si = SI7006A20(py)
    h = round(si.humidity(),1)
    log(cycle, 'humidity', h, '%')
    pybytes_send_signal(1, h)
    t = round(si.temperature(),1)
    log(cycle, 'temperature', t, 'C')
    pybytes_send_signal(2, t)
    d = round(si.dew_point(),3)
    log(cycle, 'dew', d)
    pybytes_send_signal(3, d)

    from LTR329ALS01 import LTR329ALS01
    lt = LTR329ALS01(py)
    l = lt.light()
    log(cycle, 'luminosity(blue)', l[0], 'Lux')
    log(cycle, 'luminosity(red)', l[1], 'Lux')
    pybytes_send_signal(4, l[0])
    pybytes_send_signal(5, l[1])

    from MPL3115A2 import MPL3115A2,ALTITUDE,PRESSURE
    for attempt in range(2):
        try:
            mp = MPL3115A2(py,mode=ALTITUDE) # Returns height in meters.
            t = round(mp.temperature(),1)
            log(cycle, 'temperature', t, 'C')
            pybytes_send_signal(10, t)
            a = mp.altitude()
            log(cycle, 'altitude', a)
            pybytes_send_signal(11, a)
            break
        except:
            log('MPL3115A2 read failed')

    mp = MPL3115A2(py, mode=PRESSURE) # Returns a value in Pascals
    p = mp.pressure()
    log(cycle, 'pressure', round(p/100,1), 'hPa', round(p/100_000,1), 'bar')
    pybytes_send_signal(12, round(p/100_000,2))

def battery():
    global battery_voltage, battery_percentage
    battery_voltage = round(py.read_battery_voltage(),3)
    battery_percentage = int(battery_voltage/5*100)
    log(cycle, 'battery', battery_voltage, 'V', battery_percentage, '%')
    csv(battery_voltage)
    csv(battery_percentage)
    pybytes_send_signal(6, battery_voltage)
    pybytes.send_battery_level(battery_percentage)
    pybytes_send_signal(21, battery_percentage)

def accelerometer():
    from LIS2HH12 import LIS2HH12
    li = LIS2HH12(py)
    for attempt in range(5):
        a = li.acceleration()
        if a[0]:
            break
        print(attempt, a)
    log(cycle, "Acceleration", a)
    pybytes_send_signal(7, a)
    r = li.roll()
    log(cycle, "Roll", r)
    pybytes_send_signal(8, r)
    p = li.pitch()
    log(cycle, "Pitch", p)
    pybytes_send_signal(9, p)

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

def location():
    global l76
    from L76GNSS import L76GNSS
    for retry in range(3):
        try:
            l76 = L76GNSS(py, timeout=30)
            break
        except Exception as e:
            log('l76', retry, e)
            # I think this would be a way to reset the gps
            py.gps_standby(False)
            time.sleep(0.1)
    def get_gps(attempts = 10):
        for a in range(attempts):
            c = l76.coordinates()
            if c[0]:
                return c
            print(a, c)
        return c
    coord = get_gps()
    if coord[0]:
        print('fix')
        pycom.nvs_set('gps_failures', 0)
    else:
        print('no fix')
        try:
            gps_failures = pycom.nvs_get('gps_failures')
        except:
            gps_failures = 0
        gps_failures += 1
        pycom.nvs_set('gps_failures', gps_failures)
        # estimate fail time
        fail_time_s = cfg('st') * gps_failures
        print('no fix', gps_failures, fail_time_s)
        if fail_time_s >= cfg('gps_s'):
            log('gps failed for', fail_time_s, cfg('gps_s'), 'trying harder')
            # FIXME: I think this is too aggressive. Once we are in bad reception mode, we switch to high battery drain. We shouldn't ALWAYS try hard
            coord = get_gps(100)
            if coord[0]:
                print('fix')
                pycom.nvs_set('gps_failures', 0)
            else:
                print('no fix')
    log('location', coord)
    pybytes_send_signal(14, coord)
    # pybytes_send_signal(15, 'https://www.openstreetmap.org/#map=9/' + str(coord[0]) + '/' + str(coord[1]))
    pybytes_send_signal(15, 'https://www.openstreetmap.org/?mlat='  + str(coord[0]) + '&mlon=' + str(coord[1]))
    dist_km = None
    time_h = None
    speed_kmh = None
    if coord[0]:
        try:
            now_sec = time.time()
            last_lat = pycom.nvs_get('gps_lat')
            last_lon = pycom.nvs_get('gps_lon')
            last_lat = struct.unpack('f', last_lat)[0]
            last_lon = struct.unpack('f', last_lon)[0]
            last_sec = pycom.nvs_get('gps_sec')
            print(now_sec, last_sec, last_lat, last_lon)
            dist_km = haversine(last_lat, last_lon, coord[0], coord[1])
            pybytes_send_signal(18, dist_km)
            time_h = (now_sec - last_sec) / 3600
            try:
                speed_kmh = dist_km / time_h
            except Exception as e:
                print(e)
            print(dist_km, time_h, speed_kmh)
            pybytes_send_signal(19, speed_kmh)
            msg = ("moved from (" + str(last_lat) + ", " + str(last_lon) +
                  ") at " + str(last_sec) + " = " + pretty_gmt(last_sec, do_return=True) +
                  " to ("  + str(coord[0]) + ", "  + str(coord[1]) +
                  ") at " + str(now_sec)  + " = " + pretty_gmt(now_sec, do_return=True) +
                  "thats " + str(dist_km) + " km in " + str(time_h) + " h, at " + str(speed_kmh) + " km/h" )
            log(msg)
            pybytes_send_signal(13, msg)
        except Exception as e:
            print('failed to calculate trajectory', e)
        print(coord[0], coord[1], now_sec)
        pycom.nvs_set('gps_lat', struct.pack('f', coord[0]))
        pycom.nvs_set('gps_lon', struct.pack('f', coord[1]))
        pycom.nvs_set('gps_sec', now_sec)

    try:
        csv(coord[0])
        csv(coord[1])
        csv(dist_km)
        csv(time_h)
        csv(speed_kmh)
    except Exception as e:
        print(e)

def cat_coords():
    F='coord.csv'
    print(F, os.stat(F)[6], 'B')
    with open(F, 'r') as f:
        content = f.read()
        print(content)
    if False:
        os.unlink(F)

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
    # if pybytes_is_loaded():
    #     pybytes.disconnect()
    #     print('pybytes disconnect')
    #     time.sleep(5)
    # from wlan import *
    # wlan_connect()
    # if not wlan_isconnected():
    #     print('Failed to establish wifi maintenance connection')
    from shell import *
    # from net import *
    from hexdump import *
    raise Exception('Script stopped in maintenance mode')

def cpu_temp(t_f=None):
    if t_f is None:
        t = (machine.temperature()-32)/1.8
    else:
        t = (cpu_temp0_f-32)/1.8
    log(cycle, 'cpu_temp', t)
    pybytes_send_signal(16, t)

def pybytes_on_boot(b=None):
    if b is None:
        b = pycom.pybytes_on_boot()
        print("pybytes_on_boot", b)
        return b
    else:
        if b:
            print("enable pybytes_on_boot")
        else:
            print("disable pybytes_on_boot")
        pycom.pybytes_on_boot(b)
        return b

def pybytes_autostart(b=None):
    if b is None:
        try:
            b = pybytes.get_config('pybytes_autostart')
            print("pybytes_autostart", b)
            return b
        except Exception as e:
            print("cannot determine pybytes_autostart", e)
            return False
    else:
        if b:
            print("enabling pybytes_autostart")
        else:
            print("disabling pybytes_autostart")
    pybytes.set_config('pybytes_autostart', b)
    return b

def pybytes_debug(v=None, verbose=True):
    key = "pybytes_debug" # max 15 characters long
    if v is None:
        try:
            d = pycom.nvs_get(key)
            if verbose:
                print("current", d)
            return d
        except:
            if verbose:
                print("not set")
            return 0
    else:
        try:
            d = pycom.nvs_get(key)
            if verbose:
                print("previous", d)
        except:
            if verbose:
                print("not set yet, setting ...")
        pycom.nvs_set(key, v) # 1,2,3,4,5,6, 99
        if verbose:
            print("new", pycom.nvs_get(key))

def pybytes_wlan(verbose=True):
    try:
        print('network_type', pybytes.__pybytes_connection.__network_type)
        wlan = pybytes.__pybytes_connection.wlan
        print('isconnected', wlan.isconnected())
        print('ifconfig', wlan.ifconfig())
        return wlan
    except Exception as e:
        print(e)
        return None

def pybytes_is_started(verbose=True):
    try:
        b = pybytes.isconnected()
        if verbose:
            if b:
                print('pybytes is loaded and connected/started')
            else:
                print('pybytes is loaded, but not connected/started')
        return b
    except Exception as e:
        verbose and print('pybytes is not loaded ({})'.format(e))
        return False

def pybytes_is_loaded():
    try:
        c = pybytes.isconnected()
        print('pybytes is loaded (isconnected={})'.format(c))
        return True
    except Exception as e:
        print('pybytes is not loaded ({})'.format(e))
        return False

def pybytes_load():
    global pybytes
    if not pybytes_is_loaded():
        print('loading pybytes')
        from _pybytes import Pybytes
        from _pybytes_config import PybytesConfig
        conf = PybytesConfig().read_config()
        pybytes = Pybytes(conf)

def pybytes_start():
    print("pybytes_start", hex(id(pybytes)))# , (time.ticks_ms()-1)/1000)
    pybytes.start()
    print("pybytes_start", hex(id(pybytes)), pybytes.isconnected())# , (time.ticks_ms()-1)/1000)

def pybytes_start_async():
    print('pybytes (async)', hex(id(pybytes)), 'conn=', pybytes.isconnected())
    import _thread
    _thread.start_new_thread(pybytes_start,())

def pybytes_wait_started():
    # check/ wait for async pybytes connection
    # TOOD: we could start to collect sensor data already
    # but that would take some refactoring to decouple getting sensor data and sending it
    if not pybytes_is_started(False):
        print('Wait for pybytes start')
        while not pybytes_is_started(False):
            if py:
                if button(100, False):
                    maintenance()
            else:
                time.sleep(1)
            print('.', end='')
        print()
        log(cycle, 'pybytes', hex(id(pybytes)), pybytes_is_started(), pybytes.isconnected())

def pybytes_send_signal(sig, msg):
    if use_pybytes:
        pybytes.send_signal(sig, msg)

def pybytes_wait_output_queue():
    print('pybytes_wait_output_queue', end=' ')
    try:
        t = time.ticks_ms()
        q = pybytes.__pybytes_connection.__connection.__mqtt._msgHandler._output_queue
        while q:
            print('[{}]'.format(len(q)), end='')
            time.sleep(1)
        print('\npybytes_wait_output_queue {}s'.format((time.ticks_ms()-t)/1000))
    except Exception as e:
        print(e)

def status():
    global status_ct_not_connected
    try:
        log(cycle, 'gmt:', pretty_gmt(do_return=True), time.ticks_ms())
    except Exception as e:
        log(cycle, 'time:', time.time(), e )
    try:
        log(cycle, 'pybytes', pybytes.isconnected())
    except:
        pass
    try:
        h = http_get()
        # h = http_get(kb=100, limit_b=100_000)
        # 100k takes approx 30s. this is a lot? however, smaller packets download much faster than larger packets
        print(h)
        if h[0]:
            log('connected (http_get)', h)
            status_ct_not_connected = 0
            pybytes_send_signal(20, h[6]/1000)
        else:
            status_ct_not_connected += 1
            log('not connected (ct={})'.format(status_ct_not_connected), h)
            pybytes_send_signal(18, -1)
    except Exception as e:
        log(cycle, 'http_get failed', e)
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
    last_sleep_s = pycom.nvs_get('sleep_s')
    # print('b')
    last_boot_s = pycom.nvs_get('boot_s')
    print(last_sleep_s, last_boot_s)
    on_s = last_sleep_s - last_boot_s
    print("boot0_s", boot0_s)
    off_s = boot0_s - last_sleep_s
    print('on=', on_s, 'off=', off_s)
    up_p = round(on_s/(off_s+on_s)*100,1)
    print(up_p, '%')
except Exception as e:
    print('Cannot determine uptime ({})'.format(e))
pycom.nvs_set('boot_s', boot0_s)

# set device configurations
#               =   v,     Board,         sleep_s,   method     ??               pybytes         gps max failure
def_config      = {'v':2, 'b':'Pysense', 'st':1800, 'sm':'no', 'nets':['wifi'], 'pybytes':False, 'gps_s':1800 }
config = {
#   name        :
    "fipy-0220" : {'v':2, 'b':'Pytrack', 'st':60,   'sm':'pic',                  'pybytes':True, 'gps_s':600 },
    "fipy-5220" : {'v':1, 'b':'Pytrack', 'st':20,   'sm':'deep' },
    "wipy-f38c" : {       'b':'Pygate',             'sm':'no'   },
    "fipy-01ec" : {'v':1, 'b':'Pysense', 'st':600,  'sm':'deep' },
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

board_ver = cfg('v')
board = cfg('b')
py = None
use_pybytes = cfg('pybytes')

if use_pybytes:
    if not pybytes_is_loaded():
        pycom.rgbled(YELLOW)
        pybytes_load()
    if not pybytes_is_started():
        pybytes_start_async()
    else:
        pycom.rgbled(GREEN)
else:
    pycom.rgbled(BLUE)

# init pycoproc
if board == 'Pygate' or board == 'None':
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
pybytes_is_loaded()
# pybytes_is_started()
msg = name + ' ' + board + board_ver_str
msg += ' cycle:' + str(cycle)
msg += ' t:' + str(boot_s)
try:
    msg += ' on:' + str(on_s) + ' off:' + str(off_s) + ' up:' + str(up_p) + '%'
except:
    pass
try:
    np = pybytes.get_config('network_preferences')
    msg += ' nets[{}]:'.format(len(np))
    for n in np:
        if n == 'lora_otaa':
            msg += 'Lo'
        elif n == 'wifi':
            msg += 'w'
        else:
            msg += n
except:
    msg += ' pybytes:no'
msg += ' reset:' + pretty_reset_cause()
msg += ' wake:' + pretty_wake_reason()
msg += ' sleep:' + str(sleep_m) + ':' + str(sleep_s)
log(cycle, msg)

if board == 'None':
    print('board None')
    sys.exit()

# wait for button/maintenance mode
if py:
    to = 5000
    print('Press button to stop script within', to, 'ms')
    pycom.rgbled(PURPLE)
    if button(to):
        maintenance()

if use_pybytes:
    if pybytes.isconnected():
        pycom.rgbled(GREEN)
    else:
        pycom.rgbled(YELLOW)
        pybytes_wait_started()
        if pybytes.isconnected():
            pycom.rgbled(GREEN)
        else:
            pycom.rgbled(RED)
else:
    pycom.rgbled(BLUE)

print('Start main function')
pybytes_send_signal(13, msg)
try:pybytes_send_signal(17, up_p)
except:pass
cpu_temp(cpu_temp0_f)
status()

if pybytes_is_started:
    log('rtc_ntp_sync')
    try:
        rtc_ntp_sync(timeout_s=60)
        print(time.time())
        log('gmt:', pretty_gmt(do_return=True))
    except Exception as e:
        print(e)

if board == 'Pygate':
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
else:
    file = open('log.csv', 'a')
    def csv(value):
        try:
            file.write(str(value))
            file.write(';')
        except:
            pass

    def catcsv():
        with open('log.csv', 'r') as f:
            print(f.read())

    csv(cycle)
    csv(time.time())
    # csv(time.ticks_ms())
    csv(pretty_gmt(do_return=True))
    csv(pybytes_is_started())

    battery()

    if board == 'Pytrack':
        location()
        accelerometer()
    elif board == 'Pysense':
        pysense_sensors()
    else:
        print('Board not supported', board)

    file.write('\n')
    file.close()

    with open('log.csv', 'r') as f:
        print(f.read())

log(cycle, 'done')
pycom.nvs_set('nextcycle', cycle+1)

if sleep_m == 'no':
    log('not sleeping')
    # do nothing
    pass
elif sleep_m == 'reset':
    pybytes_wait_output_queue()
    print('Resetting...')
    time.sleep(0.1)
    machine.reset()
else:
    to = 10000
    # wait for user button to stop the sleep/wake cycle
    # and give pybytes/mqtt some time to finish sending
    print('Press button to stop script within', to, 'ms')
    pycom.rgbled(PURPLE)
    if button(to):
        maintenance()
    pybytes_wait_output_queue()
    log(cycle, 'going to sleep for', sleep_s, 's via', sleep_m, 'after running for', time.time()-boot_s, 's')
    pycom.nvs_set('sleep_s', time.time())
    time.sleep_ms(10)
    if sleep_m == 'pic':
        py.setup_sleep(sleep_s)
        py.go_to_sleep()
    elif sleep_m == 'deep':
        machine.deepsleep(sleep_s * 1000)
