#!/usr/bin/python
# -*- coding:UTF-8 -*-

###################
#
# format_bmp.py
#
###################
import operator

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
        bitmap_line.reverse()
    elif bpp == 8:
        line = map(ord, line)
        for i in xrange(width):
            pixel = palette[line[i]]
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
            bitmap_line.append(abgr[1:])
    else:
        Exception("Wrong bbp")
    return bitmap_line

def save_file(filepath, content, bpp):
    print "Saving \"%s\" as BMP" % filepath
    f = open(filepath, 'wb')
    f.write('BM')

    #skiping fields file_size and bitmap_adress, because don't know them now. Will write later
    f.seek(14)

    #header length
    write = lambda data, size: f.write(utils.dec2filehex(data,size))

    write(40, 4)

    #image height and width
    width = len(content[0])
    height = len(content)
    write(width, 4)
    write(height, 4)

    #color_plane
    write(1, 2)

    #bbp
    write(int(bpp), 2)

    #compression
    write(0, 4)

    #skiping bitmap length, will write later
    f.seek(38)

    # horizontal and vertical resolution
    write(2835, 4)
    write(2835, 4)

    # color_number and base_color_number
    write(0, 4)
    write(0, 4)

    #palette
    palette = []
    if bpp == 1:
        palette = [[0, 0, 0], [65280, 65280, 65280]]
    elif bpp == 8:
        import palette256
        palette = palette256.palette
        for p in palette:
            p.reverse()
    else:
        pass

    for p in palette:
        output_p = [component >> 8 for component in p]
        output_p.reverse()
        output_p = map(chr, output_p)
        f.write("".join(output_p) + '\x00')

    # bitmap
    bitmap_adress = f.tell()
    content.reverse()

    line_size = get_bitmap_line_byte_size(width, bpp)
    if bpp == 24:
        for line in content:
            bitmap_line = []
            for pixel in line:
                pixel.reverse()
                bitmap_line += [chr(min(c >> 8, 255)) for c in pixel]
                pixel.reverse()
            while len(bitmap_line) < line_size:
                bitmap_line.append('\x00')
            f.write("".join(bitmap_line))
    elif bpp == 1:
        for line in content:
            binary_line = ""
            for pixel in line:
                binary_line += str(get_palette_pos(palette, pixel))
            while len(binary_line) < line_size*8:
                binary_line += '0'

            bitmap_line = [binary_line[i*8:(i+1)*8] for i in xrange(line_size)]
            bitmap_line = [int(byte, 2)  for byte in bitmap_line if byte]
            bitmap_line = map(chr, bitmap_line)
            f.write("".join(bitmap_line))
    elif bpp == 8:
        for line in content:
            bitmap_line = []
            for pixel in line:
                i = 0
                while (i < 256) and \
                ((abs(pixel[0] - palette[i][0]) >= 8192) or \
                (abs(pixel[1] - palette[i][1]) >= 8192) or \
                (abs(pixel[2] - palette[i][2]) >= 8192)):
                    i +=1
                if i < 256:
                    bitmap_line.append(chr(i))
                else:
                    bitmap_line.append(chr(get_palette_pos(palette, pixel)))
            f.write("".join(bitmap_line))
    else:
        f.close()
        raise Exception("Reading of %d bbp images wasn't implemented" % bpp)

    file_size = f.tell()
    bitmap_length = file_size - bitmap_adress

    # file size
    f.seek(2)
    write(file_size, 4)

    # bitmap adress (where it starts)
    f.seek(10)
    write(bitmap_adress, 4)

    # bitmap length
    f.seek(34)
    write(bitmap_length, 4)

    f.close()
    content.reverse()
    return True

def get_palette_pos(palette, pixel):
    eps = []
    for p in palette:
        eps.append(reduce(operator.add, [abs(p[i]-pixel[0]) for i in xrange(3)]))
    return eps.index(min(eps))


# Test
if __name__=='__main__':
    h, b = open_file('img/test_me24.bmp')
    save_file('img/result.bmp', b, 8)

