#!/usr/bin/python
# -*- coding:UTF-8 -*-

###################
#
# utils.py
#
###################


class InvalidImage(Exception):
    pass

class UnknownImageFormat(Exception):
    pass

def filehex2dec(lst):
    data = [ord(elem) for elem in lst]
    sum = 0
    for i in xrange(len(data)):
        sum += data[i] * (256**i)
    return sum

def dec2filehex(dec, size):
    def dec2hex(dec, size):
        lst = []
        mod = dec
        while mod > 256:
            div = mod / 256
            if div > 256:
                lst = dec2hex(div, size - 1) + lst
            else:
                lst.insert(0, div)
            mod = mod % 256
        lst.insert(0, mod)
        while len(lst) < size:
            lst.append(0)
        return lst

    return "".join(map(chr, dec2hex(dec, size)))

def testBit(int_type, offset):
    '''testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.'''
    mask = 1 << offset
    return (int_type & mask) and 1 or 0

def setBit(int_type, offset):
    '''setBit() returns an integer with the bit at 'offset' set to 1.'''
    mask = 1 << offset
    return(int_type | mask)

def clearBit(int_type, offset):
    '''clearBit() returns an integer with the bit at 'offset' cleared.'''
    mask = ~(1 << offset)
    return(int_type & mask)

def toggleBit(int_type, offset):
    '''toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.'''
    mask = 1 << offset
    return(int_type ^ mask)

