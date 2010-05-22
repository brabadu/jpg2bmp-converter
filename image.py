#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
import re
import os
import random
import operator

from utils import InvalidImage, UnknownImageFormat

class Image ():

    def __init__(self):
        self.bitmap = None
        self.height = 0
        self.width = 0
        self.load_modules()

    def open(self, filepath):
        """Returns image object with a class of file type"""
        f = filepath.strip()
        filetype = filepath.split('.')[-1]

        try:
            metadata, self.bitmap = self.modules[filetype].open_file(f)
        except KeyError:
            raise UnknownImageFormat

        self.height = metadata['height']
        self.width = metadata['width']

    def load_modules(self):
        """Dynamic load of modules, that handle image file types"""
        files = os.listdir(os.curdir)
        pattern = re.compile(r'^format_(\w+)\.py')
        format_files = filter(lambda x: x is not None, map(pattern.match, files))
        modules_list = [[f.groups()[0], __import__(f.group()[:-3])] for f in format_files]
        self.modules = dict(modules_list)

    def noiseRGB(self, component, strength=10000):
        """Noise R,G or B component of image"""
        component = str(component).lower()
        all_components = {
            'r' : 0,
            'g' : 1,
            'b' : 2,
        }
        try:
            c = all_components[component]
        except KeyError:
            print 'Component must be r,g or b'

        for line in self.bitmap:
            for pixel in line:
                np = (pixel[c] + strength)
#                print pixel, " : ",
                pixel[c] = max(1, min(65535, np))
#                print pixel

    def noiseHSL(self, strength = 0.1):
        bitmap_hsl = self.convert2HSL()
        for line in bitmap_hsl:
            for pixel in line:
                np = pixel[2] + strength
                pixel[2] = min(1, max(0, np))
        self.bitmap = self.convert2BMP(bitmap_hsl)

    def convert2HSL(self):
        bitmap = []
        for line in self.bitmap:
            bitmap.append([])
            for pixel in line:
                r = (pixel[0] / float(65535))
                g = (pixel[1] / float(65535))
                b = (pixel[2] / float(65535))

                minim = min(r, g, b)
                maxim = max(r, g, b)
                chroma = maxim - minim

                L =  (maxim + minim) / 2

                Hs = None
                if chroma == 0:
                    Hs = None
                elif maxim == r:
                    Hs = ((g - b) / chroma) % 6
                elif maxim == g:
                    Hs = ((b - r) / chroma) + 2
                else:
                    Hs = (r - g) / chroma + 4

                S = 0
                if chroma == 0:
                    S = 0
                elif L <= 0.5:
                    S = chroma / (2 * L)
                else:
                    S = chroma / (2 - 2 * L)
                bitmap[-1].append([Hs, S, L])
        return bitmap

    def convert2BMP(self, bitmap_hsl):
        bitmap = []
        for line in bitmap_hsl:
            bitmap.append([])
            for pixel in line:
                Hs, S, L = pixel

                chroma = 0
                if L <= 0.5:
                    chroma = 2 * L * S
                else:
                    chroma = S * (2 - 2 * L)

                if Hs:
                    X = chroma * (1 - abs(Hs % 2 - 1))
                Rs, Gs, Bs = (0, 0, 0)
                if Hs is None:
                    Rs, Gs, Bs = (0, 0, 0)
                elif 0 <= Hs < 1:
                    Rs, Gs, Bs = (chroma, X, 0)
                elif 1 <= Hs < 2:
                    Rs, Gs, Bs = (X, chroma, 0)
                elif 2 <= Hs < 3:
                    Rs, Gs, Bs = (0, chroma, X)
                elif 3 <= Hs < 4:
                    Rs, Gs, Bs = (0, X, chroma)
                elif 4 <= Hs < 5:
                    Rs, Gs, Bs = (X, 0, chroma)
                elif 5 <= Hs < 6:
                    Rs, Gs, Bs = (chroma, 0, X)

                minim = L - chroma / 2
                R, G, B = (Rs + minim) * 65535, (Gs + minim) * 65535, (Bs + minim) * 65535

                bitmap[-1].append([int(R), int(G), int(B)])
        return bitmap

    def negative(self):
        self.bitmap = [[[65536 - component for component in pixel] for pixel in line] for line in self.bitmap]

    def put_filter(self, f):
        def multiply(x, y):
            return ([x[i]*y for i in xrange(3)])

        self.filter_sum = reduce(operator.add, reduce(operator.add, f))

        import copy
        b = copy.deepcopy(self.bitmap)
        for i,line in enumerate(self.bitmap[1:-1]):
            for j,pixel in enumerate(line[1:-1]):
                multies = (multiply(self.bitmap[i-1][j-1], f[0][0]),
                        multiply(self.bitmap[i-1][j], f[0][1]),
                        multiply(self.bitmap[i-1][j+1], f[0][2]),
                        multiply(self.bitmap[i][j-1], f[1][0]),
                        multiply(self.bitmap[i][j], f[1][1]),
                        multiply(self.bitmap[i][j+1], f[1][2]),
                        multiply(self.bitmap[i+1][j-1], f[2][0]),
                        multiply(self.bitmap[i+1][j], f[2][0]),
                        multiply(self.bitmap[i+1][j+1], f[2][0]))
                center = reduce(lambda x,y: [x[k] + y[k] for k in xrange(3)], multies )
                b[i][j] = [center[k] / self.filter_sum for k in xrange(3)]
        self.bitmap = b

if __name__ == '__main__':
    im = Image()
    im.open('img/test_me24.bmp')
    print im.bitmap[51][51]
    im.noiseHSL()
    print im.bitmap[51][51]

