import os
import binascii
import machine
import time

logfile = "/flash/log_" + os.uname().sysname + "_" + binascii.hexlify(machine.unique_id()).decode() + ".log"

def log(*messages):
    # messages = ('eh', 'yo', 666, 'whazzzup!?')
    f = open(logfile, 'a')
    t = "[" + str(time.time()) + "]"
    f.write(t)
    f.write(' ')
    for m in messages:
        # print(m)
        f.write(str(m))
        f.write(' ')
    f.write('\n')
    f.close()
    print(t, *messages)

def catlog():
    f = open(logfile, 'r')
    print(f.read())
    f.close()

def rmlog():
    try:
        print("remove", logfile )
        os.remove(logfile)
        print("done")
    except Exception as e:
        print("couldn't remove {}: {}".format(logfile,e))
        pass

if __name__ == "__main__":
    # log('eh', 'yo', 666, 'whazzzup!?')
    # print('---')
    catlog()
    if False:
        rmlog()
