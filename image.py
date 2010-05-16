#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
import re
import os

from utils import InvalidImage, UnknownImageFormat

class Image ():
    
    def __init__(self):
        self.load_modules()
    
    def open(self, filepath):
        """Returns image object with a class of file type"""
        f = filepath.strip()
        filetype = filepath.split('.')[-1]
        try:
            return self.modules[filetype].open_file(f)
        except KeyError:
            raise UnknownImageFormat
        
        
    
    def load_modules(self):
        """Dynamic load of modules, that handle image file types"""
        files = os.listdir(os.curdir)
        pattern = re.compile(r'^format_(\w+)\.py')
        format_files = filter(lambda x: x is not None, map(pattern.match, files))
        modules_list = [[f.groups()[0], __import__(f.group()[:-3])] for f in format_files]
        self.modules = dict(modules_list)

    def noise(self, component, strength):
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

