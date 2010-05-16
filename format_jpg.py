# palettes/quantizers
WEB = 0
ADAPTIVE = 1

# categories
NORMAL = 0
SEQUENCE = 1
CONTAINER = 2

import _imaging as core

class Image:

    def __init__(self):
        # FIXME: take "new" parameters / other image?
        # FIXME: turn mode and size into delegating properties?
        self.im = None
        self.mode = ""
        self.size = (0, 0)
        self.palette = None
        self.info = {}
        self.category = NORMAL
        self.readonly = 0

    def __repr__(self):
        return "<%s.%s image mode=%s size=%dx%d at 0x%X>" % (
            self.__class__.__module__, self.__class__.__name__,
            self.mode, self.size[0], self.size[1],
            id(self)
            )

    ##
    # Allocates storage for the image and loads the pixel data.  In
    # normal cases, you don't need to call this method, since the
    # Image class automatically loads an opened image when it is
    # accessed for the first time.
    #
    # @return An image access object.

    def load(self):
        "Explicitly load pixel data."
        if self.im and self.palette and self.palette.dirty:
            # realize palette
            apply(self.im.putpalette, self.palette.getdata())
            self.palette.dirty = 0
            self.palette.mode = "RGB"
            self.palette.rawmode = None
            if self.info.has_key("transparency"):
                self.im.putpalettealpha(self.info["transparency"], 0)
                self.palette.mode = "RGBA"
        if self.im:
            return self.im.pixel_access(self.readonly)

    ##
    # Returns a converted copy of this image. For the "P" mode, this
    # method translates pixels through the palette.  If mode is
    # omitted, a mode is chosen so that all information in the image
    # and the palette can be represented without a palette.
    # <p>
    # The current version supports all possible conversions between
    # "L", "RGB" and "CMYK."
    # <p>
    # When translating a colour image to black and white (mode "L"),
    # the library uses the ITU-R 601-2 luma transform:
    # <p>
    # <b>L = R * 299/1000 + G * 587/1000 + B * 114/1000</b>
    # <p>
    # When translating a greyscale image into a bilevel image (mode
    # "1"), all non-zero values are set to 255 (white). To use other
    # thresholds, use the {@link #Image.point} method.
    #
    # @def convert(mode, matrix=None, **options)
    # @param mode The requested mode.
    # @param matrix An optional conversion matrix.  If given, this
    #    should be 4- or 16-tuple containing floating point values.
    # @param options Additional options, given as keyword arguments.
    # @keyparam dither Dithering method, used when converting from
    #    mode "RGB" to "P".
    #    Available methods are NONE or FLOYDSTEINBERG (default).
    # @keyparam palette Palette to use when converting from mode "RGB"
    #    to "P".  Available palettes are WEB or ADAPTIVE.
    # @keyparam colors Number of colors to use for the ADAPTIVE palette.
    #    Defaults to 256.
    # @return An Image object.

    def convert(self, mode=None, data=None, dither=None,
                palette=WEB, colors=256):
        "Convert to other pixel format"

        if not mode:
            # determine default mode
            if self.mode == "P":
                self.load()
                if self.palette:
                    mode = self.palette.mode
                else:
                    mode = "RGB"
            else:
                return self.copy()

        self.load()

        if data:
            # matrix conversion
            if mode not in ("L", "RGB"):
                raise ValueError("illegal conversion")
            im = self.im.convert_matrix(mode, data)
            return self._new(im)

        if mode == "P" and palette == ADAPTIVE:
            im = self.im.quantize(colors)
            return self._new(im)

        # colourspace conversion
        if dither is None:
            dither = FLOYDSTEINBERG

        try:
            im = self.im.convert(mode, dither)
        except ValueError:
            try:
                # normalize source image and try again
                im = self.im.convert(getmodebase(self.mode))
                im = im.convert(mode, dither)
            except KeyError:
                raise ValueError("illegal conversion")

        return self._new(im)

def open(filepath, mode="r"):
    "Open an image file, without loading the raster data"

    if mode != "r":
        raise ValueError("bad mode")

    import JpegImagePlugin
    return JpegImagePlugin.JpegImageFile(filepath)

def open_file(filepath):
    "Open an image file, without loading the raster data"

    im = open(filepath)
    p = im.load()
    bitmap = [[[ elem << 8 for elem in p[x,y]] for x in xrange(im.size[0])]for y in xrange(im.size[1])]
    header = {
        'width' : im.size[0],
        'height' : im.size[1]
    }
    return header, bitmap



def _getdecoder(mode, decoder_name, args, extra=()):

    # tweak arguments
    if args is None:
        args = ()
    elif not type(args).__name__ == 'tuple':
        args = (args,)

    return apply(core.jpeg_decoder, (mode,) + args + extra)

