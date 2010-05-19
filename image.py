#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
import re
import os

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

    def save(self, filepath):
        f = filepath.strip()

        if not f.endswith('.bmp'):
            f += '.bmp'
        self.modules['bmp'].save_file(f, self.bitmap, self.height, self.width)

    def load_modules(self):
        """Dynamic load of modules, that handle image file types"""
        files = os.listdir(os.curdir)
        pattern = re.compile(r'^format_(\w+)\.py')
        format_files = filter(lambda x: x is not None, map(pattern.match, files))
        modules_list = [[f.groups()[0], __import__(f.group()[:-3])] for f in format_files]
        self.modules = dict(modules_list)

