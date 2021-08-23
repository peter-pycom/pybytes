import time
boot0_s = time.time()
import machine
cpu_temp0_f = machine.temperature()
import pycom
print('boot.py', boot0_s, time.ticks_ms(), 'pybytes_on_boot=', pycom.pybytes_on_boot())
pycom.heartbeat(False)
pycom.rgbled(0x030300) # yellow
