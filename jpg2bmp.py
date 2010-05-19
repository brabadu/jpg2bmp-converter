#!/usr/bin/python
# -*- coding:UTF-8 -*-

import gtk
import os
import random
import sys

import image

class MainWindow(gtk.Builder):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.add_from_file(os.path.join(os.path.dirname(__file__),'ui/main_window.ui'))
        # подключаем обработчики сигналов, описанные в demo.ui к объекту self
        self.connect_signals(self)
        self.MainWindow.show_all()
        self.x = 100

        self.image = None

        self.drawable = self.drawingarea.window
        self.colormap = self.drawingarea.get_colormap()
        assert self.drawable

        this_color = gtk.gdk.Color(red=0xff, green=0xff, blue=0xff)
        this_foreground = self.colormap.alloc_color(this_color)
        self.gc = self.drawable.new_gc( foreground=this_foreground,
                              background=this_foreground,
                              line_width=2,
                              line_style=gtk.gdk.LINE_SOLID,
                              join_style=gtk.gdk.JOIN_MITER,
                              cap_style=gtk.gdk.CAP_BUTT,
                              fill=gtk.gdk.SOLID,
                              function=gtk.gdk.COPY )


    def __getattr__(self, attr):
        # удобней писать self.window1, чем self.get_object('window1')
        obj = self.get_object(attr)
        if not obj:
            raise AttributeError('object %r has no attribute %r' % (self,attr))
        setattr(self, attr, obj)
        return obj

    def quit(self, widget):
        print "QUIT"
        gtk.main_quit()


    def save_file(self, widget):
        # По поводу кода ниже - рекомендую познакомится со ссылкой:
        # doc.crossplatform.ru/python/pygtk/2.4/ch-DrawingArea.html#sec-GraphicsContext

        drawable = self.drawingarea.window
        colormap = self.drawingarea.get_colormap()
        assert drawable

        this_color = gtk.gdk.Color(red=0x0, green=0x0, blue=0x0)
        this_foreground = colormap.alloc_color(this_color)
        gc = drawable.new_gc( foreground=this_foreground,
                              background=this_foreground,
                              line_width=2,
                              line_style=gtk.gdk.LINE_SOLID,
                              join_style=gtk.gdk.JOIN_MITER,
                              cap_style=gtk.gdk.CAP_BUTT,
                              fill=gtk.gdk.SOLID,
                              function=gtk.gdk.COPY )
#        drawable.set_size(self.x, self.x)
        self.x += 50
        r,g,b = 0,0,0
        x,y = 0,0
        while x < random.randint(100,200):
            drawable.draw_point(gc, x, y)
            x += 2
            y += 1
            r = random.randint(100,65535)
            g = random.randint(100,65535)
            b = random.randint(100,65535)
            color = colormap.alloc_color(r, g, b)
            gc.set_foreground(color)

        return True

    def open_file(self, widget):
        print "OPEN"

        self.image = image.Image()
        filename = ''
        try:
            filename = sys.argv[1]
        except:
            filename = 'img/test_me24.bmp'

        self.image.open(filename)
        self.draw_image()
        return True

    def expose_event(self, area, event):
        self.draw_image()
        return True

    def draw_image(self):
        if self.image is None:
            return

        img = self.image
        for y in xrange(img.height):
            for x in xrange(img.width):
                r, g, b = img.bitmap[y][x]
                col = self.colormap.alloc_color(r, g, b)
                self.gc.set_foreground(col)
                self.drawable.draw_point(self.gc, x, y)


if __name__ == '__main__':
    mainWindow = MainWindow()
    gtk.main()

