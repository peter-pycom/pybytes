import binascii
def hexdump(file=None, buf=None, print_ascii=True, print_bin=False, head=None):
    if file is not None:
        f = open(filename, 'r')
        buf = f.read()
        f.close()
    ct = 0
    ascii_buffer = ""
    for b in buf:
        if isinstance(b, int):
            o = b
            c = chr(b)
        elif isinstance(b, str):
            o = ord(b)
            c = b
        else:
            raise Exception("don't know what to do with", type(b))
        # pretty print one byte
        if print_bin:
            print("{:08b} ".format(o), end="")
        else:
            print("{:02x} ".format(o), end="")
        if (0 <= o and o <= 0x1f) or o in [0x23, 0x7f, 0x81, 0x8d, 0x8f, 0x90, 0x9d, 0xa0, 0xad]: # c == '\n' or c == '\r' or (): #o in [0, 1, 2, 3, 4, 0x7f]:
            # non-printable characters
            # there are probably many more ... you find one, you fix it
            ascii_buffer += '.'
        elif o == 0x5c:
            ascii_buffer += '\\'
        elif o == 0x20:
            ascii_buffer += ' '
        else:
            ascii_buffer += c # str(c)
        ct += 1
        if ct % 8 == 0:
            print(" ", end="")
        if ct % 16 == 0:
            # wrap the line after 16 bytes
            if print_ascii:
                print(" |{:s}|".format(ascii_buffer))
            else:
                print()
            ascii_buffer = ""
        if head is not None and ct >= head:
            break
    if ascii_buffer:
        l = ct % 16
        for x in range(0, 16-l):
            # leave space as much as we have left in this line
            print('   ', end='')
        if l < 8:
            # print one space for ending off both blocks of 8
            print('  ', end='')
        else:
            # print one space for ending off the second block of 8
            print(' ', end='')
        # last partially filled ascii_buffer
        if print_ascii:
            print(" |{:s}|".format(ascii_buffer))
        else:
            print()

if __name__ == "__main__":
    # hexdump("/flash/test/test.bin.up")
    # hexdump("/flash/test/http_get.recv")
    # hexdump("/flash/up41065.elf", head=2000)
    # hexdump(buf='ever\r\n')
    # hexdump(buf=b'1234ff')
    hexdump(buf=buf,print_bin=True, print_ascii=False)
