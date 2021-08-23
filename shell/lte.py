import time
import machine
from network import LTE
import socket
import sys
import os
import binascii
import pycom

# from sleep import sleep
try: from http_get import http_get
except: pass
try: import sqnsupgrade
except: pass
try: from whoami import whoami
except: pass
try: from ntp import *
except: pass
try: from shell import *
except: pass

use_edrx = False
use_psm = False
lte_debug = False
# lte_debug = True

attach_timeout_s = 1800

# *) if you run this script multiple times via Play button the following try/except avoids unnecesary re-initialization
# *) if you import this from another script `from lte import *` you also get the global variable
# try:
#     l
#     # print("l exists, no initialization needed")
# except:
#     # print("initialize l=None")
#     l = None

band_to_earfcn = [
#   ( low, mid,high)  # band
    (-1,-1,-1), # dummy entry for index 0
    (   0, 300, 599), # 1
    ( 600, 900,1199), # 2
    (1200,1575,1949), # 3
    (1950,2175,2399), # 4
    (2400,2525,2649), # 5
    (2650,2700,2749), # 6
    (2750,3100,3449), # 7
    (3450,3625,3799), # 8
    (3800,3975,4149), # 9
    (4150,4450,4749), # 10
    (4750,4850,4949), # 11
    (5010,5090,5179), # 12
    (5180,5230,5279), # 13
    (5280,5330,5379), # 14
    (-2,-2,-2), # 15
    (-3,-3,-3), # 16
    (5730,5790,5849), # 17
    (5850,5925,5999), # 18
    (6000,6075,6149), # 19
    (6150,6300,6449), # 20
    (6450,7125,6599), # 21
]

earfcn_to_band = {}
for band in range(1, len(band_to_earfcn)):
    earfcn_to_band[band_to_earfcn[band]] = band

def find_band(earfcn, verbose=False):
    if isinstance(earfcn, str):
        earfcn = int(earfcn)
    for b in range(len(band_to_earfcn)):
        x = band_to_earfcn[b]
        if x[0] <= earfcn and x[2] >= earfcn:
            if verbose:
                print("EARFCN", earfcn, "is in range", x, "which is band", b)
            return b
    return None

def band():
    try:
        mn = moni(do_return=True)
        print(mn)
        # +SQNMONI: 20416 Cc:204 Nc:16 RSRP:-80.20 CINR:0.00 RSRQ:-12.90 TAC:31 Id:222 EARFCN:3700 PWR:-59.52 PAGING:64
        # +SQNMONI: NL KPN Cc:204 Nc:08 RSRP:-90.00 CINR:18.00 RSRQ:-7.70 TAC:64503 Id:176 EARFCN:6400 PWR:-74.52 PAGING:64
        # +SQNMONI: Amarisoft Network Cc:001 Nc:01 RSRP:-88.20 CINR:-1.30 RSRQ:-13.30 TAC:2 Id:1 EARFCN:6309 PWR:-67.12 PAGING:128
        return find_band(int(mn.split(':')[9].split(' ')[0]), verbose=True)
    except Exception as e:
        print(e)

_mcc_region = {
    '0':"Test network",
    '2':"Europe",
    '3':"North Americ and Carribean",
    '4':"Asia and Middle East",
    '5':"Australia and Oceania",
    '6':"Africa",
    '7':"South and Central America",
    '9':"Worldwide",
}
def mcc_region(r):
    try:
        return _mcc_region[r]
    except:
        return "unknown"

# https://en.wikipedia.org/wiki/List_of_country_calling_codes
_country = {
    "882": "XV - International Networks",
    "883": "XV - International Networks",
    "31":"NL - Netherlands",
    "44":"UK - UK, Guernsy, Isle of Man, Jersey",
    "86":"CN - China",
}
def country(cc):
    try:
        return _country[cc]
    except:
        return "unknown"

# https://en.wikipedia.org/wiki/Mobile_country_code
_mcc = {
    "001":"Test networks",
    "204":"NL",
    "234":"GB, GG, IM, JE",
    "901":"International operators",
}
def mcc(c):
    try:
        return _mcc[c]
    except:
        return "unknown"

# https://en.wikipedia.org/wiki/Mobile_country_code
# An "MCC/MNC tuple" uniquely identifies a mobile network operator (carrier)
# MCC is three digits, MNC is two or three digits
_operator = {
    "00101":"Test Network",
    "20408":"KPN",
    "20416":"T-Mobile",
    "23450":"Jersey Telecom",
    "90128":"Vodafone",
}
def find_operator(mcc_mnc_tuple=None, mcc=None, mnc=None):
    if mcc_mnc_tuple is None:
        if mcc is None:
            return "(no mcc)",None
        elif mnc is None:
            return "(mcc={}, no mnc)".format(mcc),None
        else:
            mcc_mnc_tuple = mcc + mnc
    mnc_len = len(mcc_mnc_tuple) - 3
    try:
        # firstly try to find as is
        return (_operator[mcc_mnc_tuple],mnc_len)
    except:
        if mnc_len == 3:
            # secondly, try whether there is a 2 digit mnc
            try:
                return _operator[mcc_mnc_tuple[:-1]],2
            except:
                pass
    # lastly, we just don't know
    return "unknown({})".format(mcc_mnc_tuple),None

def sleep(s, verbose=False):
    if verbose:
        print("sleep(", s, ") ", end="")
    while s > 0:
        if verbose:
            print(s, end=" ")
            if s % 30 == 0:
                print()
        time.sleep(1)
        s -= 1
    if verbose:
        print("")

def test_connection(attempts = 3):
    for a in range(attempts):
        try:
            r = http_get(timeout_s=5, quiet=True)
            if r[0]:
                return True
            print('.', end='')
        except:
            print('x', end='')
            pass
    return False

def lte_cb_handler(arg):
    print("\n\n\n#############################################################")
    print("CB LTE Callback Handler")
    ev = arg.events() # NB: reading the events clears them
    t = time.ticks_ms()
    print("CB", t, ev)
    pycom.heartbeat(False)
    pycom.rgbled(0x222200)
    if ev & LTE.EVENT_COVERAGE_LOSS:
        print("CB", t, "coverage loss")
    if ev & LTE.EVENT_BREAK:
        print("CB", t, "uart break signal")
    # investiage the situation. Generally speaking, it will be one of the following:
    # - the modem lost connection, but will automatically reestablish it by itself if we give it some time, e.g. new
    # - the modem can't automatically reconnect, we can try to suspend/resume or reattach
    # - last resort, if all else fails, we can reset the ESP32 and pray that this helps
    print("CB", t, "test connection")
    if test_connection():
        print("CB", t, "connection ok")
    else:
        print("CB", t, "connection not ok, try susp/res")
        # if suspendresume():
        #     print("CB suspendresume ok")
        #     if test_connection():
        #         print("CB connection ok")
        #     else:
        #         l.deinit()
        #         l.init()
        #         lte_attach()
        #         lte_connect()
    print("CB", t, ev, " done #############################################################")

def lte_init_psm_on():
    global l
    print("lte_init_psm_on")
    l = LTE(psm_period_value=12, psm_period_unit=LTE.PSM_PERIOD_1H,
          psm_active_value=5, psm_active_unit=LTE.PSM_ACTIVE_2S, debug=lte_debug)
    return l

def lte_init_psm_off():
    global l
    print("lte_init_psm_off")
    try:
        l = LTE(psm_period_value=1, psm_period_unit=LTE.PSM_PERIOD_DISABLED,
                  psm_active_value=5, psm_active_unit=LTE.PSM_ACTIVE_DISABLED, debug=lte_debug)
    except Exception as e:
        print("Exception:", e)
        print("try without psm args")
        try:
            l = LTE(debug=lte_debug)
        except Exception as e:
            print("Exception:", e)
            print("try without debug")
            l = LTE()
    return l

def lte_init(use_psm=use_psm):
    try:
        if l is not None:
            return l
    except:
        pass
    if use_psm:
        return lte_init_psm_on()
    else:
        return lte_init_psm_off()

def at(cmd='', verbose=False, quiet=True, do_return=False, raise_on_error=True):
    global l
    if l is None:
        lte_init()
    if cmd == '':
        cmd='AT'
        quiet=False
    if verbose:
        print(cmd)
    response = l.send_at_cmd(cmd)
    lines = response.split('\r\n')
    retval = ""
    for line in lines:
        if ( len(line) == 0 ):
            continue
        elif quiet and line == 'OK':
            continue
        else:
            if do_return:
                if line == 'ERROR' and raise_on_error:
                    raise Exception('AT cmd "' + cmd + '" returned ERROR: "' + response + '"')
                retval += line + '\n'
            else:
                print(line)
    if do_return:
        return retval.strip()

def at_log(cmd):
    resp = ""
    last_resp = ""
    while True:
        resp = at(cmd, do_return=True, raise_on_error=False).strip()
        if resp != last_resp:
            print(time.time(), resp)
            last_resp = resp
        sleep(1)

def lte_version(debug=False):
    if not l:
        lte_init()
    if debug:
        at('AT!="showver"')
        at('AT!="get_sw_version"')
        # at('AT+CGMR')
        # UE5.2.0.3
    rat = None # radio access technologie
    lrv = None
    lrnum = None
    try:
        ver = at('ATI1', quiet=True, do_return=True, raise_on_error=True)
        lr = ver.split('\n')[1]
        lrv, lrnum = lr.split('-')
        print(ver)
        import re
        if re.search('^LR5', lrv):
            rat = 'CAT-M1'
        elif re.search('^LR6', lrv):
            rat = 'NB-IoT'
        print("rat", rat)
    except Exception as e:
        print(e)
    return (rat, lrv, lrnum)

def smod():
    at('AT+SMOD?')

def bmod():
    at('AT+BMOD?')

def bands():
    if l is None:
        lte_init()
    import re
    # <vendor>GM01Q-REV4 configuration SQN3330 A1A3 SKY68001-31 17 bands R03</vendor>  1 2 3 4 5 8 12 13 14 17 18 19 20 25 26 28 66
    # <vendor>EVK41-A configuration SQN3330 A1A3 SKY68001-31 R01</vendor>                  3 4     12 13             20       28
    # grep('band ', at('AT+SMDD', do_return=True))
    # todo: how to detect missing SMDD? line==ERROR? or try/except?
    for line in at('AT+SMDD', do_return=True).split('\n'):
        if re.search('vendor', line):
            # print(line)
            # hexdump(buf=line)
            line = line.strip()
            if line == '<vendor>EVK41-A configuration SQN3330 A1A3 SKY68001-31 R01</vendor>':
                print('6 bands, I guess')
            elif line == '<vendor>GM01Q-REV4 configuration SQN3330 A1A3 SKY68001-31 17 bands R03</vendor>':
                print('17 bands, I guess')
            else:
                print('not sure which band set we have ... ')

def imsi(do_cfun=True, attempts=5):
    attempt = 0
    _imsi = at("AT+CIMI", do_return=True, raise_on_error=False)
    while _imsi == "ERROR" and attempt < attempts:
        print("imsi failed, attempt [", attempt, "]... ")
        if attempt == 0 and cfun() == 0:
            # it doesn't work in CFUN=0, so first time, try to fix it
            print('cfun 4')
            cfun(4)
            time.sleep(0.1)
        else:
            time.sleep(0.5)
        _imsi = at("AT+CIMI", do_return=True, raise_on_error=False)
        attempt += 1
    return _imsi

def imsi_decode(_imsi=None, verbose=True):
    if _imsi is None:
        _imsi = imsi()
    if verbose:
        # print("imsi", _imsi)
        print("# IMSI (International Mobile Subscriber Identity) MCC+MNC+MSIN")
        print("# subscriber identification") # stored on SIM
        print("IMSI", _imsi)
    # IMSI (International Mobile Subscriber Identity)
    # It is stored inside the SIM.  It consists of three part.
    #
    #     Mobile Country Code (MCC) : First 3 digits of IMSI gives you MCC.
    #                                 e.g. 310 for USA
    #     Mobile Network Code (MNC) : Next 2 or 3 digits give you this info.
    #                                 e.g. 410 for AT&T
    #     Mobile Station ID (MSID)  : Rest of the digits. Gives away the network you
    #                                 are using like IS-95, TDMA , GSM etc.
    #
    #     Mobile network code (MNC) is used in combination with a mobile country
    #     code (MCC) (also known as a "MCC / MNC tuple") to uniquely identify a
    #     mobile phone operator/carrier.
    _mcc = _imsi[0:3]
    if verbose:
        print("  MCC region:", _mcc[0], '-', mcc_region(_mcc[0]))
        print("  MCC (Mobile Country Code):", _mcc, '-', mcc(_mcc))
    op,mnc_len = find_operator(_imsi[0:6])
    if mnc_len is None:
        if verbose:
            print("  Can't find operator")
            return (_mcc,None,None)
    _mnc=_imsi[3:3+mnc_len]
    _msin=_imsi[3+mnc_len:]
    if verbose:
        print("  Operator: ", _mcc, _mnc, " - ", op, sep='')
        print("  MNC (Mobile Network Code):", _mnc )
        print("  MSIN (Mobile Subsciption Identification Number):", _msin)
    return (_mcc,_mnc,_msin)

def cfun(fun=None):
    if fun is not None:
        a = 'AT+CFUN='+str(fun)
        print(a)
        f = at(a, do_return=True).strip()
    else:
        f = at('AT+CFUN?', do_return=True).strip()
        import re
        return int(re.search('[0-9]$', f).group(0))

def cgatt(state=None):
    if state is not None:
        a = 'AT+CGATT=' + str(state)
        at(a)
    else:
        r = at('AT+CGATT?', do_return=True).strip()
        print(r)

def cereg(n=None):
    if n is None:
        r = at('AT+CEREG?', do_return=True).strip()
        print(r)
        try:
            r = r.split('+CEREG: ')[1]
            #print('_', r ,'_', sep='')
            v = r.split(',')
            n = int(v[0])
            print('  n=', n, sep='', end='')
            if n == 0: print(': no urc')
            elif n == 1: print(': reg urc')
            elif n == 2: print(': reg+loc urc')
            else: print()
            s = int(v[1])
            print('  stat=', s, sep='', end='')
            if s == 0: print(': not registered, not searching')
            elif s == 1: print(': registered')
            elif s == 2: print(': searching')
            elif s == 5: print(': registered, roaming')
            else: print()
            if len(v) > 2:
                tac = v[2].strip('"')
                ci = v[3].strip('"')
                act = v[4]
                print('  tac=', tac, ' ci=', ci, ' act=', act, sep='')
            return (n,s)
        except:
            return None
    else:
        at('AT+CEREG='+str(n))
        return cereg()

def psm():
    if not l:
        lte_init()
    p = l.psm()
    if p[0]:
        print("psm enabled: period=", p[1], end='*')
        P = int(p[1])
        if p[2] == LTE.PSM_PERIOD_2S:
            P *= 2
            print("2s = ", P, "s" , sep='', end=', ')
        elif p[2] == LTE.PSM_PERIOD_30S:
            P *= 30
            print("30s = ", P, "s", sep='', end=', ')
        elif p[2] == LTE.PSM_PERIOD_1M:
            print("1m", sep='', end=', ')
        elif p[2] == LTE.PSM_PERIOD_1H:
            print("1h", end=', ')
        else:
            # PSM_PERIOD_10M
            # PSM_PERIOD_10H
            # PSM_PERIOD_320H
            # PSM_PERIOD_DISABLED
            print("FIXME", p[2])

        print('active=', p[3], end='*' )
        if p[4] == LTE.PSM_ACTIVE_2S:
            print("2s = ", p[3]*2, 's', sep='', end=' ')
        else:
            print('FIXME', p[4], end=' ')
            # PSM_ACTIVE_1M
            # PSM_ACTIVE_6M
            # PSM_ACTIVE_DISABLED
    else:
        print("psm disabled", end=' ')
    print(p)

# def edrx():
#     at('AT+SQNEDRX?') # "0010"')
#     # +SQNEDRX: 2,4,"0101","0000"
#     # AT+CEDRXS=[<mode>,[,<AcTtype>[,<Requested_eDRX_value>]]
#     # mode:
#     #   0: Disable the use of eDRX
#     #   1: Enable the use of eDRX
#     #   2 Enable the use of eDRX and enable the URC
#     #     +CEDRXP: [,[,<NW- provided_eDRX_value>[,<Paging_time_window>]]]
#     # AcTtype: 4 for E-UTRAN (WB-S1 mode)
#     # Requested_eDRX_value, e.g. 0101 = 81.92s
#
# def edrx_on():
#     print("turn edrx ON")
#     at('AT+SQNEDRX=2,4,"0101","0000"') # 81.92s
#
# def edrx_off():
#     print("turn edrx OFF"),
#     at('AT+SQNEDRX=3')

def lpmc():
    LPM = 'disablelog 1\nsetlpm airplane=1 enable=1'
    #print('# lpm 60:')
    try:
        lpm = at('AT!="cat /fs/sqn/etc/scripts/60-lpm-enable.cli"', do_return=True)
        if lpm == LPM:
            print("lpm is configured (60)")
            return True
        elif len(lpm) == 0:
            pass
        else:
            print("lpm: 60-lpm-enable.cli:<", lpm, ">", sep='')
    except Exception as e:
        pass
        print("Exception while reading lpm 60:", e)

    # print('# lpm 61:')
    try:
        lpm = at('AT!="cat /fs/sqn/etc/scripts/61-lpm-enable.cli"', do_return=True)
        if lpm == LPM:
            print("lpm is configured (61)")
            return True
        elif len(lpm) == 0:
            pass
        else:
            print("lpm: 61-lpm-enable.cli:<", lpm, ">", sep='')
    except Exception as e:
        pass
        print("Exception while reading lpm 61:", e)

    print("lpm is not configured")
    return False

def lpmc_unconfigure():
    try:
        at('AT!="rm /fs/sqn/etc/scripts/60-lpm-enable.cli"')
    except Exception as e:
        print("lpm rm 60", e)
    try:
        at('AT!="rm /fs/sqn/etc/scripts/61-lpm-enable.cli"')
    except Exception as e:
        print("lpm rm 61", e)
    lpmc()

def lpmc_configure():
    try:
        at('AT!="echo setlpm 1 0 0 1 > /fs/sqn/etc/scripts/60-lpm-enable.cli"')
        time.sleep(.1)
        at('AT!="echo disablelog 1 >> /fs/sqn/etc/scripts/60-lpm-enable.cli"')
    except Exception as e:
        print("lpm enable 60", e)
    lpmc()

def provider(_imsi=None):
    apn = None
    band = None
    dns0 = None
    dns1 = None
    rat = (None, None) # (CAT-M1, NB-IoT)
    name = None
    # dns0 = '8.8.8.8'
    # dns1 = '9.9.9.9'
    if _imsi is None:
        _imsi = imsi()
    if _imsi is None:
        print("Can't get IMSI")
        raise Exception("Can't get IMSI")
    mcc,mnc,msin = imsi_decode(_imsi, verbose=True)
    op = mcc + mnc
    if op == "00101":
        name = "Test"
        rat = (True, True)
    elif op == "20408":
        name = "KPN"
        apn = 'simpoint.m2m'
    elif op == "23450":
        name = "JT"
        band = 8
        rat = (True, False)
    elif op == "90128":
        apn = "pycom.io" # this is for test cards, maybe we need iccid to distinguish?
        dns0 = "172.31.16.100"
        dns1 = "172.31.32.100"
        # >>> lte_ifconfig()
        # APN: "pycom.io.mnc028.mcc901.gprs"
        # IP: "10.200.2.128
        # mask: 255.255.255.255"
        name = "Vodafone Int"
        rat = ['CAT-M1', 'NB-IoT']
    print("provider: APN=", apn, " band=", band, " DNS=", dns0, "/", dns1, " rat:", rat, " op=", op, " name=", name, sep='')
    return ( apn, band, dns0, dns1, rat, op, name )

def fsm(write_file=False, do_return=False):
    if write_file:
        log = at('AT!="fsm"', do_return=True)
        f = open('/flash/fsm.log', 'w')
        f.write("time ")
        f.write(str(time.time()))
        f.write(", isattached:")
        f.write(str(l.isattached()))
        f.write('\n')

        f.write(log)
        f.close()
    elif do_return:
        return at('AT!="fsm"', do_return=do_return)
    else:
        at('AT!="fsm"')

def cat_fsm():
    cat('/flash/fsm.log')

def showphy(do_return=False):
    if do_return:
        return at('AT!="showphy"', do_return=do_return)
    else:
        at('AT!="showphy"')

def stat_log():
    if l is None:
        lte_init()
    # import hashlib
    # m = hashlib.md5()
    f = at('AT!="fsm"', do_return=True)
    s = at('AT!="showphy"', do_return=True)
    r = at('AT+CSQ', do_return=True)
    a = l.isattached()
    #h = m.update(f)
    print(time.time(), a, f, s, r)
    while True:
        f2 = at('AT!="fsm"', do_return=True)
        a2 = l.isattached()
        s2 = at('AT!="showphy"', do_return=True)
        r2 = at('AT+CSQ', do_return=True)
        #h2 = m.update(f2)
        if a != a2:
            f = f2
            s = s2
            a = a2
            r = r2
            print(time.time(), a, f, s, r)
        else:
            if f != f2:
                f = f2
                s = s2
                print(time.time(), a, f, s)
            # if s != s2:
            #     s = s2
            #     print(time.time(), s)
            if r != r2:
                r = r2
                print(time.time(), a, r)

def rssi_old():
    at('AT+CSQ')
    at('AT+VZWRSRP')
    at('AT+VZWRSRQ')
    # fipy-4624 41019
    # time att       rssi                   rsrp                     rsrq
    # 120 False +CSQ: 18,99 +VZWRSRP: 1,6309,-95.60 +VZWRSRQ: 1,6309,-12.10
    # 121 False +CSQ: 20,99 +VZWRSRP: 1,6309,-91.70 +VZWRSRQ: 1,6309,-11.40
    # 122 True +CSQ: 19,99 +VZWRSRP: 1,6309,-92.00 +VZWRSRQ: 1,6309,-11.50
    # 124 True +CSQ: 20,99 +VZWRSRP: 1,6309,-91.90 +VZWRSRQ: 1,6309,-11.20
    # 127 True +CSQ: 18,99 +VZWRSRP: 1,6309,-104.40 +VZWRSRQ: 1,6309,-21.60
    # 137 True +CSQ: 18,99 +VZWRSRP: 1,6309,-91.80 +VZWRSRQ: 1,6309,-11.10
    # 145 True +CSQ: 15,99 +VZWRSRP: 1,6309,-104.90 +VZWRSRQ: 1,6309,-15.70
    # 149 True +CSQ: 17,99 +VZWRSRP: 1,6309,-99.70 +VZWRSRQ: 1,6309,-13.80

    # gpy-b678
    # LR6.0.0.0-41019
    # time att       rssi                   rsrp                     rsrq
    # 58 False +CSQ: 20,99 +VZWRSRP: 1,6309,-90.70  +VZWRSRQ: 1,6309,-11.20
    # 73 False +CSQ: 13,99 +VZWRSRP: 1,6309,-180.10 +VZWRSRQ: 1,6309,-87.20
    # 81 False +CSQ: 20,99 +VZWRSRP: 1,6309,-92.20  +VZWRSRQ: 1,6309,-12.80
    # 84 False +CSQ: 20,99 +VZWRSRP: 1,6309,-91.00  +VZWRSRQ: 1,6309,-11.80
    # 84 True  +CSQ: 20,99 +VZWRSRP: 1,6309,-91.00  +VZWRSRQ: 1,6309,-11.80
    # 85 True  +CSQ: 20,99 +VZWRSRP: 1,6309,-91.60  +VZWRSRQ: 1,6309,-12.60
    # 97 True  +CSQ: 21,99 +VZWRSRP: 1,6309,-90.10  +VZWRSRQ: 1,6309,-11.40
    pass

def rssi(log=False):
    if l is None:
        lte_init()
    csq = at('AT+CSQ', do_return=True).strip()
    rsrp = ""
    rsrq = ""
    rsrp2 = ""
    rsrq2 = ""
    try:
        rsrp = at('AT+VZWRSRP', do_return=True).strip()
        rsrq = at('AT+VZWRSRQ', do_return=True).strip()
    except:
        pass
    a = l.isattached()
    print(time.time(), a, csq, rsrp, rsrq)
    while log:
        a2 = l.isattached()
        csq2 = at('AT+CSQ', do_return=True).strip()
        try:
            rsrp2 = at('AT+VZWRSRP', do_return=True).strip()
            rsrq2 = at('AT+VZWRSRQ', do_return=True).strip()
        except:
            pass
        if a != a2 or csq != csq2 or rsrp != rsrp2 or rsrq != rsrq2:
            a = a2
            csq = csq2
            rsrp = rsrp2
            rsrq = rsrq2
            print(time.time(), a, csq, rsrp, rsrq)

def rsrpq(log=False, do_return=False):
    msg = ""
    last_msg = ""
    while True:
        r = at('AT+CESQ', do_return=True).strip()
        # +CESQ: <rxlev>,<ber>,<rscp>,<ecno>,<rsrq>,<rsrp>
        rr = r.split(' ')[1].split(',')
        # RSRP Reference Signal Receive Power [dBm]
        try:
            rsrp = int(rr[5])
        except Exception as e:
            print('Exception (int(rr[5])):', e, rr)
            # can happen, e.g. when URC comes:
            # Exception invalid syntax for integer with base 10 ['99', '99', '255', '255', '16', '51\n+CEDRXP:']
            # raise(e)
            continue
        msg = 'RSRP=' + str(rsrp) + ':'
        if rsrp == 0:
            msg += ' < -140 dBm (poor)'
        elif rsrp == 255:
            msg += ' unknown'
        else:
            dBm = -140 + rsrp
            msg += ' ' + str(dBm) + 'dBm'
            if dBm < - 100:
                msg += ' (poor)'
            elif dBm < -90:
                msg += ' (fair)'
            elif dBm < -80:
                msg += ' (good)'
            else:
                msg += ' (excellent)'
        # RSRQ Reference Signal Receive Quality [dB]
        rsrq = int(rr[4])
        msg += ', RSRQ=' + str(rsrq) + ':'
        if rsrq == 0:
            msg += ' < -19.5dB (poor)'
        elif rsrq == 255:
            msg += ' unknown'
        else:
            dB = -19.5 + 0.5 * rsrq
            msg += ' ' + str(dB) + 'dB'
            if dB < -20:
                msg += ' (poor)'
            elif dB < -15:
                msg += ' (fair)'
            elif dB < -10:
                msg += ' (good)'
            else:
                msg += ' (excellent)'
        if msg != last_msg:
            if do_return:
                return msg
            print(time.time(), msg)
            last_msg = msg
        if not log:
            break
    # rssi - Received signal strength indication.
    #     0 -113 dBm or less
    #     1 -111 dBm
    #     2 .. 30 -109 .. -53 dBm
    #     31 -51 dBm or greater
    #     99 not known or not detectable
    # ber - Channel bit error rate (in percent).
    #     0 .. 7 as RXQUAL values in the table in 3GPP TS 45.008 [20]
    #     99 not known or not detectable
    # at('AT+CSQ')

    # Reference Signal Receive Power [dBm]
    # +VZWRSRP Verizon Wireles RSRP values for all cells which the UE is measuring
    # <cellID>1, <EARFCN>1, <RSRP>1,
    # <cellID>2,<EARFCN>2, <RSRP>2,
    # ...,
    # <cellID>n, <EARFCN>n, <RSRP>n
    # at('AT+VZWRSRP')
    # +VZWRSRP: 1,6309,-86.00
    # +VZWRSRP: 1,6309,-86.70

    # Reference Signal Receive Quality
    # +VZWRSRQ Verizon Wireless RSRQ [dB]
    # values for all cells which the UE is measuring
    # up to 8 cells. in both RRC_IDLE and RRC_CONNECTED modes
    # <cellID>1, <EARFCN>1, <RSRQ>1,
    # <cellID>2, <EARFCN>2, <RSRQ>2,
    # ...,
    # <cellID>n, <EARFCN>n, <RSRQ>n
    # at('AT+VZWRSRQ')
    # +VZWRSRQ: 1,6309,-12.20
    # +VZWRSRQ: 1,6309,-12.10

    # at('AT+SQNINS=0')
    # # +SQNINS: 0,4,7,,,,,,,,
    # # +SQNINS: 0,13,7,,,,,,,,
    #
    # at('AT+SQNINS=1')
    # # +SQNINS: 1,4,7,,,,,,,,
    # # +SQNINS: 1,13,7,,,,,,,,

    #                RSSI         RSRP          RSRQ         SNR
    # ----------+-----------+-------------+-------------+-----------
    # Excellent |            >-80          > -10
    # Good      |            -80 to -90    -10 to -15
    # Fair      |            -90 to -100   -15 to -20
    # Poor      |            < -100        < -20
    pass

def moni(m=9, do_return=False, verbose=False):
    mn = at('AT+SQNMONI=' + str(m), do_return=True, raise_on_error=False).strip()
    # if verbose:
    #     print(mn)
    if do_return:
        return mn
    else:
        if verbose:
            r = mn.split(' ')
            # ['+SQNMONI:', '20416', 'Cc:204', 'Nc:16', 'RSRP:-78.70', 'CINR:0.00', 'RSRQ:-9.70', 'TAC:31', 'Id:445', 'EARFCN:3700', 'PWR:-61.22', 'PAGING:64']
            assert(len(r) == 12) # for n=9. there are probably other cases, but they need code fixes below
            assert(r[0] == '+SQNMONI:')
            i = 1
            if ':' not in r[i]:
                print('  netname', r[i])
                i += 1
            _mcc = None
            while ( i < len(r) ):
                k,v=r[i].split(':')
                if k == 'Cc':
                    _mcc = v
                    print('  Cc (country)', v, mcc(v))
                elif k == "Nc":
                    print('  Nc (Network operator code)', v, find_operator(mcc=_mcc, mnc=v)[0])
                elif k == "RSRP":
                    print('  RSRP (Reference Signal Received Power)', v)
                elif k == "CINR":
                    print('  CINR (Carrier to Interference-plus-Noise Ratio)', v)
                elif k == "RSRQ":
                    print('  RSRQ (Reference Signal Received Quality)', v)
                elif k == 'TAC':
                    print('  TAC (Tracking Area Code)', v)
                elif k == 'EARFCN':
                    print('  EARFCN (E-UTRA Assigned Radio Channel)', v, 'band', find_band(v))
                elif k == 'Id':
                    print('  Id (cell identifier)', v)
                else:
                    # paging
                    # DRX cycle in number of radio frames (1 frame = 10ms).
                    # dBm
                    # received signal strength in dBm
                    # drx
                    # Discontinuous reception cycle length
                    # n
                    # progressive number of adjacent cell
                    print(' ', k, v)
                i += 1
        else:
            print(mn)

def lte_set_callback():
    # l.lte_callback(LTE.EVENT_COVERAGE_LOSS, lte_cb_handler)
    trigger = 0xFF
    handler = lte_cb_handler
    print("set lte_callback", trigger, handler)
    l.lte_callback(trigger, handler)

def lte_remove_callback():
    # l.lte_callback(LTE.EVENT_COVERAGE_LOSS, lte_cb_handler)
    l.lte_callback(0, None)

def try_set_dns(i,dns):
    if dns:
        print("set dnsserver[{}] = {}".format(i,dns))
        socket.dnsserver(i,dns)

def lte_post_attach_config():
    # rssi()
    lte_set_callback()
    cereg() # show whether we're roaming
    # moni()
    band() # show moni and earfcn/band
    psm()
    #edrx()
    lte_ifconfig()
    print(l.time())

def try_fix_dns():
    if socket.dnsserver()[0] == '0.0.0.0':
        print("DNS:", socket.dnsserver(), " attempt cfg via provider()")
        cfg = provider()
        try_set_dns(0, cfg[2])
        try_set_dns(1, cfg[3])
    print("DNS:", socket.dnsserver())

def lte_attach(apn=None, band=None, timeout_s = attach_timeout_s, do_fsm_log=True, do_rssi_log=True):
    if not l:
        lte_init()
    if l.isattached():
        print("already attached")
    else:
        print("cfun", cfun())
        l.imei()
        v = lte_version()
        lpmc()
        try:
            whoami()
        except:
            pass
        cfg = provider()
        if not apn:
            apn = cfg[0]
        if not band:
            band = cfg[1]
        if v[0] == 'CAT-M1' and not cfg[4][0]:
            print("WARNING: I don't think ", cfg[6], "(", cfg[5], ") supports", v[0])
        elif v[0] == 'NB-IoT' and not cfg[4][1]:
            print("WARNING: I don't think ", cfg[6], "(", cfg[5], ") supports", v[0])
        print("attach(apn=", apn, ", band=", band, ")", sep='')
        t = time.ticks_ms()
        # if apn:
        #     if band:
        l.attach(apn=apn, band=band)
        # else:
        #     l.attach(apn=apn)
        # else:
        #     if band:
        #         l.attach(band=band)
        #     else:
        #         l.attach()
        print("attach (", (time.ticks_ms() - t ) / 1000, ")" ) # e.g., 0.124 , I think this is usually fast
        lte_waitattached(timeout_s, do_fsm_log=do_fsm_log, do_rssi_log=do_rssi_log)
        print("attaching took", (time.ticks_ms() - t ) / 1000 )
        lte_post_attach_config()

def lte_attach_manual(apn=None, band=None, timeout_s = attach_timeout_s, do_fsm_log=True, do_rssi_log=True):
    if not l:
        lte_debug = True
        lte_init()
    if l.isattached():
        print("already attached")
    else:
        if band is None:
            raise Exception('specify band')
        t = time.ticks_ms()
        at()
        #at('AT')
        #at('AT+CGATT?')
        cgatt()
        #at('AT+CEREG?')
        cereg()
        #at('AT+CFUN?')
        cfun()
        at('AT+SQNCTM?')
        # SMDD
        at('AT!="showver"')
        at('AT!="clearscanconfig"')
        at('AT!="RRC::addScanBand band=' + str(band) + '"')
        at('AT!=disablelog 1')
        at('AT+CFUN=1')
        at('AT!=setlpm airplane=1 enable=1')
        # if apn:
        #     if band:
        #         l.attach(apn=apn, band=band)
        #     else:
        #         l.attach(apn=apn)
        # else:
        #     if band:
        #         l.attach(band=band)
        #     else:
        #         l.attach()
        print("attach took", (time.ticks_ms() - t ) / 1000 )
        lte_waitattached(timeout_s, do_fsm_log=do_fsm_log, do_rssi_log=do_rssi_log)
        print("attaching took", (time.ticks_ms() - t ) / 1000 )
        at('AT+CEREG?')
        # at('AT+SQNMONI=7')
        moni()
        psm()
        # edrx()
        lte_ifconfig()
        d = socket.dnsserver()
        if d[0] == '0.0.0.0':
            print("setting dns server 8.8.8.8")
            socket.dnsserver(0, '8.8.8.8')
        print("DNS:", socket.dnsserver())

def lte_isattached_manual():
    cmds=['AT+CEREG?', 'AT+CGATT?', ]
    for cmd in cmds:
        print(at(cmd, do_return=True).strip(), end=', ')
    rsrpq()
    print()

def lte_isattached():
    if l.isconnected():
        print("isconnected", True)
    else:
        try:
            rsrpq()
            moni()
        except Exception as e:
            print('Failed to rsrpq() or moni() ... nevermind, carry on ({})'.format(e))
    r = l.isattached()
    print('isattached', r)
    return r

def lte_waitattached(timeout_s = attach_timeout_s, do_fsm_log=True, do_rssi_log=True, sleep_time_s=0.1):
    if timeout_s is not None:
        timeout_ms = timeout_s * 1000
    t = time.ticks_ms()
    r = None
    f = None
    if l.isconnected():
        print("isconnected")
    elif l.isattached():
        print("isattached")
    else:
        while not l.isattached():
            if do_fsm_log:
                try:
                    f2 = grep("TOP FSM|SEARCH FSM", fsm(do_return=True), do_return=True)
                    if f != f2:
                        f = f2
                        print(time.time(), '\n', f, sep='')
                    #cat_fsm()
                except:
                    # maybe we didnt' upload grep to the board
                    pass
            if do_rssi_log:
                # r2 = at('AT+CSQ', do_return=True).strip()
                # r2 = moni(do_return=True)
                r2 = rsrpq(do_return=True)
                if r != r2:
                    r = r2
                    print(time.time(), r)
                    # rssi()
            time.sleep(sleep_time_s)
            if timeout_s is not None and time.ticks_ms() - t > timeout_ms:
                raise Exception("Could not attach in {} s".format(timeout_s))
        print("isattached", l.isattached(), "turned true after {} s".format(( time.ticks_ms()-t )  / 1000 ))

def sqnsping(num=10, ip='8.8.8.8', interval=0, do_fsm=False, quiet=False):
    lte_init()
    if not l.isattached():
        attach()
    # if l.isconnected():
    #     l.pppsuspend()
    ct = 0
    ct_succ = 0
    ct_fail = 0
    while num < 0 or ct < num:
        succ = False
        try:
            resp = at('AT!="IP::ping ' + ip + '"', do_return=True)
            if not quiet:
                print(resp)
            succ = "from" in resp
        except Exception as e:
            print("Exception during ping", e)
        if succ:
            ct_succ += 1
        else:
            ct_fail += 1
        if do_fsm:
            fsm()
        ct += 1
        if (num < 0 or ct < num):
            # we're still going
            if interval < 0:
                sleep(-interval)
                if succ:
                    interval *= 2
                else:
                    interval /= 2
                    interval = min(-1, interval)
            elif interval:
                sleep(interval)
    print("pings:", num, " failed:", ct_fail, " succeeded:", ct_succ, " -- ", round(ct_succ/num*100.0,1), "%", sep="")
    # sqnsping(3, '18.195.28.152')
    # sqnsping(3, 'pycom.io.mnc028.mcc901.gprs')

def lte_connect():
    if l.isconnected():
        print("already connected")
        return
    if not l.isattached():
        lte_attach()
    print("connect")
    t = time.ticks_ms()
    l.connect()
    print("connect took", (time.ticks_ms() - t ) / 1000 )
    timeout_ms = 60000
    while not l.isconnected():
        time.sleep(0.1)
        if time.ticks_ms() - t > timeout_ms:
            raise Exception("Could not connect in {} s".format((time.ticks_ms() - t )/ 1000 ))
    print("connecting took", (time.ticks_ms() - t ) / 1000 )
    try_fix_dns()

def lte_isconnected():
    return l.isconnected()

def lte_ifconfig(verbose=False):
    for attempt in range(0,3):
        try:
            cgcontrdp = at('AT+CGCONTRDP=1', do_return=True)
            if cgcontrdp.strip() == 'ERROR':
                print('IP not set')
            else:
                if verbose:
                    print(cgcontrdp)
                    # '\r\n+CGCONTRDP: 1,5,"spe.inetd.vodafone.nbiot.mnc028.mcc901.gprs","10.175.213.177.255.255.255.255","","10.105.16.254","10.105.144.254","","",,,1430\r\n\r\nOK\r\n'
                    #                       APN                                           IP                                  dns             dns
                    # l.send_at_cmd('AT+CGDCONT?')
                    # '\r\n+CGDCONT: 1,"IP","spe.inetd.vodafone.nbiot",,,,0,0,0,0,0,0,1,,0\r\n\r\nOK\r\n'
                    at('AT!="ifconfig"')
                else:
                    cgcontrdp_list = cgcontrdp.split(',')
                    ip_mask = cgcontrdp_list[3].split('.')
                    print('APN:', cgcontrdp_list[2])
                    print('IP:', '.'.join(ip_mask[0:4]))
                    print('mask:', '.'.join(ip_mask[4:8]))
            return
        except Exception as ex:
            print("ifconfig Exception:", ex)
    raise Exception("Could not ifconfig")

def lte_ifconfig_suspend():
    l.pppsuspend()
    ifconfig()
    l.pppresume()

def suspendresume():
    l.init(debug=True)
    l.pppsuspend()
    l.pppresume()
    l.init(debug=False)
    if not l.isconnected():
        return False

def dl():
    lte_init()
    if not l.isattached():
        attach()
    if not l.isconnected():
        try:
            print("resume")
            l.pppresume()
            if not l.isconnected():
                print("connect")
                connect()
        except Exception as e:
            print("couldn't resume, try to connect (", e, ")", sep='')
            try:
                connect()
            except Exception as e:
                print("connect failed, try second time (", e, ")")
                sleep(1)
                connect()
    print("download")
    t = time.ticks_ms()
    # r = http_get(kb=kb, timeout_s=5)
    r = http_get('http://mqtt.pybytes.pycom.io/', timeout_s=5, limit_b=100, quiet=True )
    # print(r)
    t = (time.ticks_ms() - t)/1000
    if r[0]:
        print("download succeeded in", t, "seconds (", r[6], " Bps)")
    else:
        print("download failed in", t, "seconds")
    # if not r[0]:
    #     raise Exception("http_get returned false")
    return r[0]

def test_dl(delays = [10, 60, 300], repetitions=3):
    lte_init()
    if not l.isattached():
        attach()
    if not l.isconnected():
        try:
            print("resume")
            l.pppresume()
            if not l.isconnected():
                print('connect')
                connect()
        except Exception as e:
            print("couldn't resume, try to connect (", e, ")", sep='')
            try:
                connect()
            except:
                print("failed, try second time")
                sleep(1)
                connect()
    # repetitions = 3
    # delays = [10, 60, 300 ] # , 600]
    results = []
    for d in delays:
        results_for_delay = []
        for r in range(repetitions):
            success = False
            results_for_delay_rep = (False, 0, 0)
            for a in range(3):
                print("\ntest_dl (delay# after:", d, " repetition:", r, "attempt:", a, ")")
                pretty_gmt()
                try:
                    #dl()
                    r = http_get('http://mqtt.pybytes.pycom.io/', timeout_s=5, limit_b=100)
                    if r[0]:
                        results_for_delay_rep = (True, a, r[6])
                        success=True
                        break
                except Exception as e:
                    print("Exception during download:", e)
            results_for_delay += [results_for_delay_rep]
            # if not success:
            #     raise Exception("test_dl failed (delay after:", d, " repetition:", r, "attempt:", a, ")")
            sleep(d, verbose=True)
        results += [ (d, results_for_delay) ]
    print("test_dl results:")
    for d_reps in results:
        #print('X', d_reps, 'Y')
        print("% 3d     " %(d_reps[0]), end='')
        for rep in d_reps[1]:
            if rep[0]:
                print("succ:", rep[1], "@", round(rep[2],1), sep='', end='   ')
            else:
                print("fail", end='          ')
            #print('x', rep, 'y', end='')
        print()

def long_at():
    if not l.isattached():
        attach()
    # from network import LTE
    # l = LTE(debug=True)
    #
    # attach()

    # set the socket option to expect the TX bytes to be provided in the form of HEX values.
    l.send_at_cmd('AT+SQNSCFGEXT=1,1,0,0,0,1')

    l.send_at_cmd('AT+SQNSD=1,1,5555,"80.101.10.222",0,8888,1')
    sleep(1)

    # short
    l.send_at_cmd('AT+SQNSSENDEXT=1,10')
    l.send_at_cmd('0102030405060708090a')
    sleep(1)

    # Request the transmission of 70 bytes (which will be 140 long HEX string)
    l.send_at_cmd('AT+SQNSSENDEXT=1,70')
    # 140 characters -> 70 bytes. This messages could not be sent with the default implementation.
    l.send_at_cmd('A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A3')
    sleep(1)

    # two chunks + remaining
    l.send_at_cmd('AT+SQNSSENDEXT=1,140')
    l.send_at_cmd('A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A3A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A303A303A303A32303630886368A343164303A3730313A313130303A3')
    sleep(1)

    # corner case two chunks and no remaining
    l.send_at_cmd('AT+SQNSSENDEXT=1,124')
    l.send_at_cmd('0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a0102030405060708090a01020304')
    sleep(1)

    # Shutdown socket
    l.send_at_cmd('AT+SQNSH=1')
    sleep(1)

def lte_reset_everything():
    print('lte reset')
    l.reset()
    time.sleep(0.1)
    print('machine reset')
    time.sleep(0.1)
    machine.reset()

def lte_detach():
    l.detach()

def lte_disconnect():
    l.disconnect()

def lte_deinit(detach=True, reset=False):
    global l
    if l:
        print("lte_deinit(detach=", detach, "reset=", reset, ")")
        l.deinit(detach=detach, reset=reset)
        l = None
        return True
    else:
        print("Can't deinit")

def lte_poweroff_or_what():
    # https://forum.pycom.io/topic/5627/pytrack-deepsleep-wakeup-on-pin-problems?_=1594191399370
    self.lte.disconnect()
    self.lte.detach()
    self.lte.send_at_cmd('AT!="CBE::powerOff"')
    self.lte.deinit()

def diff_log(fct, *args, **kwargs):
    last = None
    while True:
        out = fct(*args, **kwargs)
        if not out == last:
            print(time.time(), out)
            last = out
        time.sleep(1)

def fw_requires_cereg_2(version):
    v = version.split('.')
    def dbg(*m):
        # print(*m)
        pass
    # a.b.c.d
    # 1.20.3.r3
    # 1.18.4.rc7
    a = int(v[0])
    if a > 1:
        dbg(">1")
        return False
    b = int(v[1])
    if b <= 18:
        dbg("<=18")
        return True
    if b > 20:
        dbg(">20")
        return False
    if b == 20:
        dbg("==20")
        c = int(v[2])
        if c < 2:
            dbg("<2")
            return True
        if c > 2:
            dbg(">2")
            return False
        dbg("==2")
        d = v[3]
        if d[0:2] == "rc":
            dbg("rc")
            return True
        if d[0] == "r":
            dbg("r")
            x = int(d[1:])
            dbg(x)
            if x <= 2:
                return True
            else:
                return False
    print("Can't decode", version )
    return None


if __name__ == "__main__":
    print(os.uname().sysname.lower() + '-' + binascii.hexlify(machine.unique_id()).decode("utf-8")[-4:], "lte.py")
    # lte_init_psm_on()
    lte_init_psm_off()
    if False:
        # if current cereg is 1, but we're using an old firmware, then reset to previous cereg=2
        cereg()
        cereg(2)
        assert fw_requires_cereg_2("1.20.2.r3") == False
        assert fw_requires_cereg_2("1.20.2.r2") == True
        assert fw_requires_cereg_2("1.20.2.rc7") == True
        assert fw_requires_cereg_2("1.20.3.xxx") == False
        assert fw_requires_cereg_2("1.20.1.xxx") == True
        assert fw_requires_cereg_2("1.18.y.xxx") == True

    # fix cereg for old FW (ie before 1.20.2.r2)
    # two problems here:
    # a) how to reliably and nicely compare version numbers -> see fw_requires_cereg_2
    # b) for the time being I still have so many locally built versions flying around that break the logic of the version number
    # rel = os.uname().release
    # if rel < '1.20.2.rc99' or rel < '1.20.2.r2':
    #     print('old')
    #     if cereg() != 2:
    #         print('old FW expects cereg=2 ... setting it')
    #         cereg(2)
    # elif rel >= '1.20.2.r2':
    #     print('new')
    # else:
    #     print('dunno')
    try:
        fw = os.uname().release
        if fw_requires_cereg_2(fw):
            print("FW", fw, "requires cereg 2")
            c = cereg()[0]
            if c == 2:
                print("ok", c)
            else:
                print("TODO: UPDATE CEREG SETTING!", c)
                sys.exit()
        else:
            print("FW", fw, "requires cereg 1, and configures this automatically")
            cereg()
            # c = cereg()[0]
            # print("cereg=FW", c)
    except Exception as e:
        print("FW version test Exception:", e)

    if False:
        lte_attach(band=8)
    elif False:
        print("cfun", cfun())
        cereg()
        lte_version()
        lpmc()
        cfg = provider()
        # bands()
        print("attach")
        l.attach(band=8)
        # l.attach(band=cfg[1])
        l.init(debug=False)
        # diff_log(moni, do_return=True)
        lte_waitattached(timeout_s=None, sleep_time_s=5)
        # diff_log(showphy, do_return=True)
    elif False:
        print("attach manual")
        lte_attach_manual(band=20)
    elif True:
        print("cfun", cfun())
        smod()
        bmod()
        lpmc()
        bands()
        lte_version()
        try:
            whoami()
        except:
            pass
        l.imei()
        provider()
        cereg()
        cgatt()
        moni()
        band()
        psm()
        fsm()
        showphy()
        rssi()
        try:
            rsrpq()
        except:
            pass
        if l.isattached():
            if l.isconnected():
                dl()
            else:
                sqnsping()



    if False:
        if socket.dnsserver()[0] == "0.0.0.0":
            print("fix dns")
            if True:
                print("vodafone DNS")
                socket.dnsserver(0, "172.31.16.100")
                socket.dnsserver(1, "172.31.32.100")
            else:
                print("fixme")

    if False:
        l.connect()
        lte_set_callback()
        dns()
        dl()
        # while True:
        #     test_dl(delays = [10])
    if False:
        rsrpq()
        at('AT+CESQ')
        grep("TOP FSM|SEARCH FSM", fsm(do_return=True))
        print(l.isattached())
        lte_post_attach_config()
        l.connect()
        print(l.isconnected())

    #sqnsping(5)
    #lte_ifconfig()
    # lte_connect()
    # while True:
    #     test_dl(delays = [10])
        # test_dl(delays = [10, 60, 300, 1800], repetitions=5)
    # attach(band=20)
    # ntp.sync()
    # test_dl()
    # machine.deepsleep(10000)

    pass
