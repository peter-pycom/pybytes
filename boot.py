import time
boot0_t = time.time()
import machine
cpu_temp_f = machine.temperature()
import pycom
print('boot.py', boot0_t, time.ticks_ms(), 'pybytes_on_boot=', pycom.pybytes_on_boot())
pycom.heartbeat(False)
pycom.rgbled(0x030300) # yellow
