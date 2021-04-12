def temp_humidity():
    from network import Bluetooth
    import time
    import ubinascii
    import struct
    bt = Bluetooth()
    try:
        bt.start_scan(-1)
    except:
        bt.stop_scan()
        bt.start_scan(-1)

    def twoscmp(value):
        if value > 128:
            value = value - 256
        return value

    def characteristic_callback(char):
        characteristic.callback(trigger=Bluetooth.CHAR_WRITE_EVENT, handler=None, arg=None)

    # last = time.time()
    start = time.ticks_ms()
    while (time.ticks_ms()-start) < 20_000:
        adv = bt.get_adv()
        # if adv and adv.rssi>-60 and ubinascii.hexlify(adv.mac)==b'ffcbb6bbce6c':

        # # ibeacon
        if adv and adv.rssi>-60:# and ubinascii.hexlify(adv.mac)==b'cd9e13c0f24a':
            read_adv = bt.resolve_adv_data(adv.data, Bluetooth.ADV_MANUFACTURER_DATA)
            manuf = ubinascii.hexlify(read_adv)
            manuf_data = ubinascii.hexlify(read_adv[0:4])
            if manuf_data == b'4c000215':
                # uuid = ubinascii.hexlify(read_adv[4:20])
                # major = ubinascii.hexlify(read_adv[20:22])
                # minor = ubinascii.hexlify(read_adv[22:24])
                # tx_power = ubinascii.hexlify(read_adv[24:25])
                # tx_power_real = twoscmp(int(tx_power, 16))
                major_int = int(major, 16) # temp
                minor_int = int(minor,16) # humidity
                return (major_int, minor_int)
                # t = time.time()
                # print(t, t-last, 'temp:', major_int, 'humidity', minor_int)
                # last = t
                # print(read_adv,manuf,manuf_data, uuid, major, minor, tx_power_real, major_int)
            # r_adv = bt.resolve_adv_data(adv.data, Bluetooth.ADV_SERVICE_DATA)
            # print(read_adv, r_adv)
        else:
            time.sleep(0.050)
    return (None,None)

if __name__ == '__main__':
    for attempt in range(10):
        temp,humidity = temp_humidity()
        print(time.time(), ':', temp, 'C', humidity, '%')
