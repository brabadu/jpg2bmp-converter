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

        self.image = image.Image()

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
        print "SAVE"
        dialog = gtk.FileChooserDialog("Save",
                               None,
                               gtk.FILE_CHOOSER_ACTION_SAVE,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/bmp")
        filter.add_pattern("*.bmp")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*.*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.image.save(filename)
            self.draw_image()

        dialog.destroy()
        return True

        return True

    def open_file(self, widget):
        print "OPEN"

        dialog = gtk.FileChooserDialog("Open",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/bmp")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.bmp")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*.*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.image.open(filename)
            self.draw_image()

        dialog.destroy()
        return True

    def expose_event(self, area, event):
        self.draw_image()
        return True

    def add_noise_r_cb(self, widget):
        self.image.noise('r')
        self.draw_image()
        return True

    def low_noise_r_cb(self, widget):
        self.image.noise('r', strength=-10000)
        self.draw_image()
        return True

    def add_noise_g_cb(self, widget):
        self.image.noise('g')
        self.draw_image()
        return True

    def low_noise_g_cb(self, widget):
        self.image.noise('g', strength=-10000)
        self.draw_image()
        return True

    def add_noise_b_cb(self, widget):
        self.image.noise('b')
        self.draw_image()
        return True

    def low_noise_b_cb(self, widget):
        self.image.noise('b', strength=-10000)
        self.draw_image()
        return True

    def negative_clicked_cb(self, widget):
        self.image.negative()
        self.draw_image()
        return True

    def put_filter8_clicked_cb(self, widget):
        f = [
            [1, 2, 1],
            [2, 13, 2],
            [2, 2, 1]
        ]
        self.image.put_filter(f)
        self.draw_image()
        return True

    def put_filter11_clicked_cb(self, widget):
        f = [
            [2, 7, 1],
            [2, 7, 2],
            [7, 3, 1]
        ]
        self.image.put_filter(f)
        self.draw_image()
        return True

    def hsl_clicked_cb(self, widget):
        message = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, "H S L !")
        message.add_button(gtk.STOCK_QUIT, gtk.RESPONSE_CLOSE)
        resp = message.run()
        if resp == gtk.RESPONSE_CLOSE:
            message.destroy()
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

