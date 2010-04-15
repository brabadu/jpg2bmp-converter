#!/usr/bin/python
# -*- coding:UTF-8 -*-

import utils

def open_file(filepath):
    print "Opening \"%s\" as BMP" % filepath
    f = open(filepath, 'rb')
    # Checking header
    header = f.read(2)
    if header != 'BM':
        raise InvalidImage()
        
    metadata = {}
    field_name = [['file_size', 4], 
                    ['reserved', 4], 
                    ['bitmap_adress', 4], 
                    ['header_length', 4],
                    ['width', 4], 
                    ['height', 4],
                    ['color_plane', 2],
                    ['bit_on_pixel', 2],
                    ['compression', 4],
                    ['bitmap_length', 4],
                    ['hres', 4],
                    ['vres', 4],
                    ['color_number', 4],
                    ['base_color_number', 4],
                    ]
    for field in field_name:
        metadata[field[0]] = utils.filehex2dec(f.read(field[1]))
        
    for k,v in metadata.iteritems():
        print k, ':', v
    # Here reading of palette must be...
    
    # Reading bitmap
    f.seek(metadata['bitmap_adress'])
    
    line_size = metadata['width'] * 3 + metadata['width'] % 4
    print "Line size = ",line_size
    
    line = f.read(line_size)
    bitmap = []
    while (line):
        bitmap_line = []
        for i in xrange(metadata['width']):
            bitmap_line.append( [ord(elem) for elem in list(line)[i*3:i*3+3]] )
        bitmap.append(bitmap_line)
#        print [ord(elem) for elem in list(line)]
#        print bitmap_line
        line = f.read(line_size)
    
    return metadata, bitmap

def save_file(filepath, content):
    print "BMP",filepath
    return True
    
