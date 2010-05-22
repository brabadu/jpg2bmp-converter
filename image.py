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

    def noiseHSL(self, strength = 0.3):
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
                delta = maxim - minim

                L =  (maxim + minim) / 2

                if delta == 0: #This is a gray, no chroma...
                    H = 0 #HSL results from 0 to 1
                    S = 0
                else: #Chromatic data...
                    if L < 0.5:
                        S = delta / (maxim + minim)
                    else:
                        S = delta / (2 - maxim - minim)

                    delta_r = (((maxim - r) / 6) + (delta / 2)) / delta
                    delta_g = (((maxim - g) / 6) + (delta / 2)) / delta
                    delta_b = (((maxim - b) / 6) + (delta / 2)) / delta

                    if r == maxim:
                        H = delta_b - delta_g
                    elif g == maxim:
                        H = (1 / 3) + delta_r - delta_b
                    else:
                        H = (2 / 3) + delta_g - delta_r

                    if H < 0:
                        H += 1
                    if H > 1:
                        H -= 1
                bitmap[-1].append([H, S, L])
        return bitmap

    def convert2BMP(self, bitmap_hsl):
        def hue2RGB(v1, v2, vH):
           if vH < 0:
               vH += 1
           if vH > 1:
               vH -= 1
           if (6 * vH) < 1:
               return (v1 + (v2 - v1) * 6 * vH)
           if (2 * vH) < 1:
               return (v2)
           if (3 * vH) < 2:
               return (v1 + (v2 - v1) * ((2 / 3) - vH) * 6)
           return (v1)

        bitmap = []
        for line in bitmap_hsl:
            bitmap.append([])
            for pixel in line:
                H, S, L = pixel
                if S == 0: #HSL from 0 to 1
                   R = L * 65535 #RGB results from 0 to 255
                   G = L * 65535
                   B = L * 65535
                else:
                   if (L < 0.5):
                       var_2 = L * (1 + S)
                   else:
                       var_2 = (L + S) - (S * L)

                   var_1 = 2 * L - var_2

                   R = 255 * hue2RGB(var_1, var_2, H + (1 / 3))
                   G = 255 * hue2RGB(var_1, var_2, H)
                   B = 255 * hue2RGB(var_1, var_2, H - (1 / 3))
                bitmap[-1].append([R, G, B])
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

