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
    
    line_size = header['width'] * 3 + header['width'] % 4
    print "Line size = ",line_size
    
    line = f.read(line_size)
    bitmap = []
    while (line):
        bitmap_line = []
        for i in xrange(header['width']):
            bgr = [ord(elem) << 8 for elem in list(line)[i*3:i*3+3]] 
            bgr.reverse()
            bitmap_line.append(bgr)
        bitmap.append(bitmap_line)
        line = f.read(line_size)
    bitmap.reverse()
    return header, bitmap

def save_file(filepath, content):
    print "BMP",filepath
    return True

# Test
if __name__=='__main__':
    open_file('img/test2.bmp')
