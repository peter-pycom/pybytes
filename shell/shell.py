import os

# COMMANDS: ls() ll() find() du() df() cat() tee() grep() cp() mv() rm() mkdir() rmdir() cd() pwd()
#
# EXAMPLES:
# ls('/flash/lib')
# ls() # lists the current working directory, see pwd()
# ll('/sd')

# TODO:
# implement wildcards
# fix/implement find(/flash/foo*/bar.*', do_return=True) and cat(find('thingy.txt', do_return=True)) mv(find('*.py'), '/flash/backup/')

def _spin(ct, ms=0):
    if ct == 0:
        print('-', end='')
        return
    x = ct % 3
    if x == 0:
        print('\b\\', end='')
    elif x == 1:
        print('\b/', end='')
    elif x == 2:
        print('\b-', end='')
    time.sleep_ms(ms)

# add a trailing /
def _add_slash(dir):
    if dir[-1] == '/':
        return dir
    else:
        return dir + '/'

# strip the trailing /
def _strip_slash(dir):
    # print('_strip_slash', dir)
    if dir == '/' or dir[-1] != '/':
        return dir
    else:
        return dir[:-1]

def _concat_path(d1, d2):
    return _add_slash(d1) + d2

def _is_dir(obj):
    # print('_is_dir', obj)
    try:
        os.listdir(_strip_slash(obj))
        return True
    except:
        return False

def _is_file(obj):
    return not _is_dir(obj)

def _ll(obj):
    # print("_ll", obj, 'file')
    s = os.stat(obj)
    mode = s[0]
    ## the following values seem to always be 0
    # inode = s[1]
    # device = s[2]
    # num_links = s[3]
    # uid = s[4]
    # gid = s[5]
    ## in bytes
    size = s[6]
    ## times are in seconds since reset (like time.time()), hence the values don't make too much sense. Might be usefull for determining how long ago a file was written IFF it was written since the last reset
    atime = s[7]
    mtime = s[8]
    ctime = s[9]
    if _is_dir(obj):
        obj = _add_slash(obj)
        print("{:<40} ".format(obj), end='')
        if mode != 0x4000:
            print(hex(mode))
    else:
        print("{:<40} ".format(obj), end='')
        if mode != 0x8000:
            # seems to be the only values we ever see are
            # 0x8000 for files and
            # 0x4000 for directories
            print(hex(mode), end='')
        print('{:>9,}'.format(size), 'B', end='')
        if size > 1024:
            print(' = {:>7,.1f}'.format(round(size/1024,2)), ' KiB', sep='', end='')
            if size > 1024 * 1204:
                print(' = {:>2.1f}'.format(round(size / 1024 / 1024,2)), ' MiB', sep='', end='')
    print()

def ll(obj='', show_dir=False):
    if obj == '':
        obj = os.getcwd()
    elif obj[0] != '/':
        obj = _concat_path(os.getcwd(), obj)
    obj = _strip_slash(obj)
    # print(obj, ':', sep='')
    if not show_dir and _is_dir(obj):
        contents = os.listdir(obj)
        # print('_ll', contents)
        for c in contents:
            x = _concat_path(obj,c)
            _ll(x)
    else:
        _ll(obj)

def _wildcard_obj(dir, obj):
    pass

def _wildcard(path):
    # FIXME
    objects = path.split('/')
    dir = '/'
    objects = objects.reverse()
    if objects[-1] != '':
        # path is not an absolute path starting at /
        dir = os.getcwd()
        objects.pop()
    print(dir, objects)

def _find(obj, name=None, type=None, do_return=False):
    import re
    obj = _strip_slash(obj)
    if type is not None and type != 'f' and type != 'd':
        raise Exception("Invalid type:", type)
    do_list = True
    if name and not re.search(name, obj):
        do_list = False
    return_list = []
    #print("obj=", obj, name, type, do_return )

    try:
        # try to treat it as a directory
        contents = os.listdir(obj)
        # jep, it's a directory
        obj = _add_slash(obj)
        if type != 'f' and do_list:
            if do_return:
                return_list += [obj]
            else:
                # print(obj, '\t\t', hex(os.stat(obj)[0]), "[", len(contents), "]" )
                print(_add_slash(obj), '\t\t', "[", len(contents), "]" )

        for c in contents:
            obj2 = _concat_path(obj, c)
            if do_return:
                return_list += _find(obj2, name, type, do_return)
                #print("coming up", obj, obj2, r)
            else:
                _find(obj2, name, type, do_return)
            # print("c=",c, "d=",d, return_list)
    except Exception as e:
        # not a directory, ie a file
        #print("not a dir", e)
        if type != 'd' and do_list:
            if do_return:
                return_list += [obj]
            else:
                _ll(obj)
    if do_return:
        #print("end", obj, return_list)
        return return_list

def ls(x=''):
    if x == '':
        x = os.getcwd()
    try:
        print(x, ":", os.listdir(x) )
    except:
        try:
            os.stat(x)
            print(x, ":", x)
        except Exception as e:
            print(x, ":", e)

# def ll(dir=''):
#     if dir == '':
#         dir = os.getcwd()
#     _ll(dir)

def find(dir='', name=None, type=None, do_return=False):
    if dir == '':
        dir = os.getcwd()

    msg = ""
    if do_return:
        msg += "return "
        if name:
            msg += "matching '" + name + "' "
    elif name:
        msg += "find matching '" + name + "' "
    else:
        msg += "list all "
    if type == 'f':
        msg += "files "
    elif type == 'd':
        msg += "directories "
    msg += "in " + dir + ":"
    print(msg)
    if do_return:
        return _find(dir, name, type, do_return)
    else:
        _find(dir, name, type, do_return)

def cd(dir="/flash"):
    import os
    pwd() # print old pwd
    if dir[-1] == '*':
        print("wildcard")
        import ls
        hits = ls.find(name=dir, type='d', do_return=True)
        if len(hits) == 1:
            dir=hits[0]
        else:
            raise Exception("Cannot uniquely identify", dir, len(hits))
    if dir != '/' and dir[-1] == '/':
        # strip the trailing /
        dir = dir[:-1]
    try:
        #os.stat(dir)
        os.listdir(dir)
        # NB: seems chdir would throw an exception, but change the internal string anyway
        # hence subsequent calls to os.getcwd() aka pwd() would fail also :-P
    except Exception as e:
        print("Cannot change to", dir, e)
        return
    if len(dir) > 1 and dir[-1] == '/':
        # strip trailing /
        os.chdir(dir[:-1])
    else:
        os.chdir(dir)
    pwd() # print new pwd

def pwd():
    import os
    print(os.getcwd())

def _du(dir):
    total = 0 # sum up the bytes of diskusage
    contents = []
    try:
        contents = os.listdir(dir)
        for c in contents:
            d = dir + "/" + c
            if dir == "/":
                d = dir + c
            # print("c=",c, "d=",d, return_list)
            total += _du(d)
        return total
    except:
        return os.stat(dir)[6]

def du(dir='', do_return=False):
    if dir == '':
        dir = os.getcwd()
    if dir != '/' and dir[-1] == '/':
        # strip the trailing /
        dir = dir[:-1]
    total_b = _du(dir)
    if do_return:
        return total_b
    else:
        print("du", dir, total_b, 'B used', end='')
        if total_b > 1024:
            print(' (', round(total_b / 1024,2), ' KiB', sep='', end='')
            if total_b > 1024 * 1024:
                print(', ', round(total_b / 1024 / 1024,2), ' MiB)', sep='')
            else:
                print(')')
        else:
            print()

def _df(part, verbose):
    free_kib = os.getfree(part)
    free_b = free_kib * 1024
    free_mib = free_kib / 1024
    if verbose:
        used_b = du(part, do_return=True)
        used_kib = used_b / 1024
        total_b = used_b + free_b
        total_kib = total_b / 1024
        error_b = 4 * 1024 * 1024 - total_b
        print(part, ' ', free_b, ' B free (', free_kib, " KiB, ", round(free_kib / 1024,2), " MiB), ", used_b, ' B used (', round(used_kib,2), ' KiB, ', round(used_kib / 1024,2), ' MiB), ', total_b, ' B total (', total_kib, ' KiB, ', round(total_kib / 1024,2), ' MiB) [error_b=', error_b, ']', sep='')
        # /flash 4087808 B free (3992 KiB, 3.9 MiB), 41247 B used (40.28 KiB, 0.04 MiB), 4129055 B total (4032.28 KiB, 3.94 MiB) [error_b=65249]
        # FIXME: why do we have an error of 64K?
        # I would expect something below 1K due to rounding since os.getfree() reports in KiB
        # probably something like inodes, ie managing directories and filenames
    else:
        print(part, kib * 1024, 'B free (', kib, "KiB)", sep='')

def df(part='', verbose=True):
    if part == '':
        _df("/flash", verbose)
        try:
            _df('/sd', verbose)
        except:
            pass
    else:
        _df(part, verbose)

def fs():
    print('Filesystem:', pycom.bootmgr()[1])

def mount_sd():
    from machine import SD
    sd = SD()
    # raises "OSError: the requested operation failed" on PyJTAG
    import os
    try:
        os.mount(sd, '/sd')
    except Exception as e:
        if os.stat('/sd'):
            # should be ok, probably previously mounted
            pass
        else:
            print("Exception while trying to mount:", e)
    os.chdir('/sd')
    print('/sd :', os.listdir())

def umount_sd():
    os.umount('/sd')
    ls('/')

def cp(src, dst, force=False, _buf_size=1000):
    import os
    try:
        src_size = os.stat(src)[6]
    except Exception as e:
        raise Exception("src", src, "does not exist:" + str(e))
    dst_exists = False
    if dst != '/' and dst[-1] == '/':
        # strip the trailing /
        dst = dst[:-1]
    print("cp", src, dst)
    try:
        os.listdir(dst)
        # dst is a directory
        src_name = src.split('/')[-1]
        dst = dst + '/' + src_name
    except:
        pass

    try:
        os.stat(dst)
        dst_exists = True
    except:
        pass
    if dst_exists and not force:
        raise Exception("Destination", dst, "exists")

    #raise Exception("hold on!", src, dst)
    s = open(src, 'r')
    d = open(dst, 'w')

    # _buf_size = 100000 # how much to copy at once
    progress_steps = 0.1 # how often to report progress
    if src_size > 1000000:
        progress_steps = 0.01
    progress = progress_steps
    dst_size = 0
    buf = b''
    print('copy', src, '[', src_size, '] to', dst, 'with _buf_size', _buf_size)
    while True:
        buf = s.read(_buf_size)
        if buf:
            d.write(buf)
            dst_size += len(buf)
            # print(dst_size, end=' ')
            if dst_size / src_size >= progress:
                print(int(progress * 100), '%', sep='', end=' ')
                progress += progress_steps
            else:
                #print('.', end='')
                pass
        else:
            break

    print()

    # d.write(s.read())

    d.close()
    s.close()
    dst_size = os.stat(dst)[6]
    if src_size != dst_size:
        raise Exception("Failed to copy. src_size=", src_size, "dst_size=", dst_size)

def mv(src, dst):
    import cp
    import rm
    cp.cp(src, dst)
    rm.rm(src)

def rm(obj, recursive=False):
    if recursive:
        print('rm-rf', obj)
        for o in os.listdir(obj):
            print(o)
            o = _concat_path(obj,o)
            if _is_dir(o):
                rm(o, recursive=True)
            else:
                rm(o)
        print('rmdir')
        rmdir(obj)
    else:
        print("rm", obj)
        os.unlink(obj)

def mkdir(dir):
    import os
    if dir[-1] == '/':
        # strip trailing /
        os.mkdir(dir[:-1])
    else:
        os.mkdir(dir)

def rmdir(dir):
    print('rmdir', dir)
    os.rmdir(dir)

def cat(filename):
    with open(filename, 'r') as f:
        content = f.read()
        print(content)

def tee(content, filename, append=False):
    if append:
        with open(filename, 'a') as f:
            f.write(content)
    else:
        with open(filename, 'w') as f:
            f.write(content)

def grepf(regex, filename, line_numbers=False, do_return=False):
    import re
    ct = 0
    retval = ""
    with open(filename) as file:
        for line in file:
            if re.search(regex, line):
                if do_return:
                    if line_numbers:
                        retval += str(ct)
                    retval += line + '\n'
                else:
                    if line_numbers:
                        print(ct, end=' ')
                    print(line)
            # else:
            #     print(ct, line, "NO")
            ct += 1
        if do_return:
            return retval

def greps(regex, str, line_numbers=False, do_return=False):
    import re
    lines = str.split('\n')
    ct = 0
    retval = ""
    for line in lines:
        if re.search(regex, line):
            if do_return:
                if line_numbers:
                    retval += str(ct)
                retval += line + '\n'
            else:
                if line_numbers:
                    print(ct, end=' ')
                print(line)
        # else:
        #     print(ct, line, "NO")
        ct += 1
    if do_return:
        return retval

def grep(regex, str='', file='', line_numbers=False, do_return=False):
    if len(str):
        return greps(regex, str, line_numbers, do_return)
    elif len(file):
        return grepf(regex, file, line_numbers, do_return)
    else:
        raise Exception("Specify either a string 'str', or a filename 'file'")

def _test():
    ll()
    ls('/flash')
    ll('/flash')
    cd('/flash')
    ll('main.py')
    cat('main.py')
    find('/flash') # FIXME doesn't recurse :(
    pwd()
    df()
    grep('import', file='main.py')
    # mkdir('/flash/stuff') and mkdir('/flash/stuff')
    # rm('/flash/main.py')

def _stress():
    s = "All work and no play makes Jack a dull boy" * 10
    d = '/flash/stress'
    try:
        mkdir(d)
    except:
        pass
    if False:
        print(os.listdir('/flash/stress'))
    ct = 0
    while True:
        f = d + '/jack{:05}.txt'.format(ct)
        print(ct)
        for x in range(1):
            tee(s, f, True)
            _spin(x)
        print('\b', end='')
        print(ct, os.getfree('/flash'), len(os.listdir(d)))
        ct += 1

if __name__ == "__main__":
    ls()
    ll()
    if False:
        tee('import pycom\npycom.heartbeat(False)\npycom.rgbled(0x070700)', '/flash/boot.py')
        tee('''
        import pycom
        import time
        pycom.heartbeat(False)
        pycom.rgbled(0x110011)
        time.sleep(1)
        pycom.heartbeat(True)
        ''', '/flash/boot.py')
        cat('boot.py')
        cat('main.py')
        rm('boot.py')
        rm('main.py')
        import machine
        machine.reset()
        # tee(lte.at('AT+SQNBANDSEL?', do_return=True),'/flash/bandsel.log')
        # cat('/flash/bandsel.log')
        print('''
        asdf
        jkl''')
    if False:
        _stress()
    try:
        mount_sd()
        find('/sd')
        import sqnsupgrade
    except:
        pass
    if False:
        ls('/sd/CATM1-41065')
        ls('/sd/NB1-41019')
        import sqnsupgrade
        sqnsupgrade.info()
        # published
        sqnsupgrade.run('/sd/CATM1-41065/CATM1-41065.dup', debug=True)
        sqnsupgrade.run('/sd/CATM1-41065/CATM1-41065.dup', '/sd/CATM1-41065/updater.elf', debug=True)
        sqnsupgrade.run('/sd/NB1-41019/NB1-41019.dup', debug=True)
        # delta
        # tbd
        # CAT-M1
        sqnsupgrade.run('/sd/LR5.2.1.0-48829/LR5.2.1.0-48829-1.dup', load_fff=False, debug=True)
        sqnsupgrade.run('/sd/LR5.2.1.0-48829/LR5.2.1.0-48829-2.dup', debug=True)
        # NB-IoT
        sqnsupgrade.run('/sd/NB1-46262/NB1-46262.dup', debug=True)
        sqnsupgrade.run('/sd/NB1-46262/FIPY_LR6.1.2.0-46262_SMDD.dup', debug=True)
        sqnsupgrade.run('/sd/FIPY_LR6.1.2.0-46262_SMDD.dup', debug=True)
        sqnsupgrade.run('/sd/NB1-48939/NB1-48939.dup', debug=True)
        machine.reset()
        #_wildcard('/sd/CAT*/mtool*')
        # find('/sd/CATM1-41065', 'updater')

        #find('/', 'updater')
        #find(name='update')
        # ll("/flash/up41065.elf")
        # print(find(name='.*33080.*', type='f', do_return=True))
        #print(find(name='.*NB1.*', type='d', do_return=True))
        # print(find(name='.*41065.*', type=None, do_return=True))
    pass
