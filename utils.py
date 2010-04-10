#!/usr/bin/python
# -*- coding:UTF-8 -*-

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
