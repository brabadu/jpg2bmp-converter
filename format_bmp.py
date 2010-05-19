#!/usr/bin/python
# -*- coding:UTF-8 -*-

import utils

header_fields = [['file_size', 4],
                ['reserved', 4],
                ['bitmap_adress', 4],
                ['header_length', 4],
                ['width', 4],
                ['height', 4],
                ['color_plane', 2],
                ['bits_on_pixel', 2],
                ['compression', 4],
                ['bitmap_length', 4],
                ['hres', 4],
                ['vres', 4],
                ['color_number', 4],
                ['base_color_number', 4],
                ]

def open_file(filepath):
    print "Opening \"%s\" as BMP" % filepath
    f = open(filepath, 'rb')
    # Checking header
    signature = f.read(2)
    if signature != 'BM':
        raise InvalidImage()

    # Header
    header = {}
    for field in header_fields:
        header[field[0]] = utils.filehex2dec(f.read(field[1]))
    for k,v in header.iteritems():
        print k, ':', v
    print

    # Palette
    has_palette = header['bits_on_pixel'] <= 8 and True or False
    print "File has palette:", has_palette
    palette = []
    if has_palette:
        for i in xrange(2**header['bits_on_pixel']):
            bgra = f.read(4)
            b, g, r = [ord(elem) << 8 for elem in list(bgra)[:-1]]
            palette.append([r, g, b])
        print "\n".join(["%7d %7d %7d" % tuple(color) for color in palette])


    # Bitmap
    f.seek(header['bitmap_adress'])

    line_size = get_bitmap_line_byte_size(header['width'], header['bits_on_pixel'])
    print "Line size = ",line_size

    line = f.read(line_size)
    bitmap = []
    while (line):
        bitmap_line = get_bitmap_line(line, header['width'], header['bits_on_pixel'], palette)
        bitmap.append(bitmap_line)
        line = f.read(line_size)
    bitmap.reverse()
    return header, bitmap

def get_bitmap_line_byte_size(width, bpp):
    useful_bits = width * bpp
    mod = useful_bits % 32
    if mod:
        useful_bits += 32 - mod
    return useful_bits / 8

def get_bitmap_line(line, width, bpp, palette):
    bitmap_line = []
    if bpp == 1:
        line = list(line)
        line.reverse()
        integer = utils.filehex2dec(line)
        integer >>= get_bitmap_line_byte_size(width, bpp)*8 - width * bpp
        for i in xrange(width):
            pixel = palette[utils.testBit(integer, i)]
            bitmap_line.append(pixel)
    elif bpp == 24:
        for i in xrange(width):
            bgr = [ord(elem) << 8 for elem in list(line)[i*3:i*3+3]]
            bgr.reverse()
            bitmap_line.append(bgr)
    elif bpp == 32:
        for i in xrange(width):
            abgr = [ord(elem) << 8 for elem in list(line)[i*4:i*4+4]]
            abgr.reverse()
            bitmap_line.append(abgr[:-1])
    else:
        Exception("Wrong bbp")
    return bitmap_line

def save_file(filepath, content):
    print "BMP",filepath
    return True

# Test
if __name__=='__main__':
    h, b = open_file('img/test2.bmp')
    print b

