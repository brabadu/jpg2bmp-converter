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
        self.f = [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1],
        ]
        self.filter_sum = reduce(operator.add, reduce(operator.add, self.f))


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

    def noise(self, component, strength=1000):
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
                pixel[c] = max(0, min(65536, np))
#                print pixel

    def negative(self):
        self.bitmap = [[[65536 - component for component in pixel] for pixel in line] for line in self.bitmap]

    def put_filter(self):
        def multiply(x, y):
            return ([x[i]*y for i in xrange(3)])

        import copy
        b = copy.deepcopy(self.bitmap)
        for i,line in enumerate(self.bitmap[1:-1]):
            for j,pixel in enumerate(line[1:-1]):
                multies = (multiply(self.bitmap[i-1][j-1], self.f[0][0]),
                        multiply(self.bitmap[i-1][j], self.f[0][1]),
                        multiply(self.bitmap[i-1][j+1], self.f[0][2]),
                        multiply(self.bitmap[i][j-1], self.f[1][0]),
                        multiply(self.bitmap[i][j], self.f[1][1]),
                        multiply(self.bitmap[i][j+1], self.f[1][2]),
                        multiply(self.bitmap[i+1][j-1], self.f[2][0]),
                        multiply(self.bitmap[i+1][j], self.f[2][0]),
                        multiply(self.bitmap[i+1][j+1], self.f[2][0]))
                center = reduce(lambda x,y: [x[k] + y[k] for k in xrange(3)], multies )
                b[i][j] = [center[k] / self.filter_sum for k in xrange(3)]
        self.bitmap = b

