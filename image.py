#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
import re
import os
import random

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
                print pixel[c]
                pixel[c] = abs(pixel[c] + random.randint(-strength, strength)) % 65536

    def negative(self):
        self.bitmap = [[[65536 - component for component in pixel] for pixel in line] for line in self.bitmap]

