#
# The Python Imaging Library.
# $Id$
#
# JPEG (JFIF) file handling
#
#
# Copyright (c) 1997-2003 by Secret Labs AB.
# Copyright (c) 1995-1996 by Fredrik Lundh.
#

#
# The Python Imaging Library.
#
# Copyright (c) 1997-2004 by Secret Labs AB
# Copyright (c) 1995-2004 by Fredrik Lundh
#
# See the README file for information on usage and redistribution.
#

###################
#
# JpegImagePlugin.py
#
###################



import format_jpg
import traceback, string, os
import array, struct


MAXBLOCK = 65536

SAFEBLOCK = 1024*1024

ERRORS = {
    -1: "image buffer overrun error",
    -2: "decoding error",
    -3: "unknown error",
    -8: "bad configuration",
    -9: "out of memory error"
}

def raise_ioerror(error):
    try:
        message = jpg.core.getcodecstatus(error)
    except AttributeError:
        message = ERRORS.get(error)
    if not message:
        message = "decoder error %d" % error
    raise IOError(message + " when reading image file")

#
# --------------------------------------------------------------------
# Helpers

def _tilesort(t1, t2):
    # sort on offset
    return cmp(t1[2], t2[2])

##
# Reads large blocks in a safe way.  Unlike fp.read(n), this function
# doesn't trust the user.  If the requested size is larger than
# SAFEBLOCK, the file is read block by block.
#
# @param fp File handle.  Must implement a <b>read</b> method.
# @param size Number of bytes to read.
# @return A string containing up to <i>size</i> bytes of data.

def _safe_read(fp, size):
    if size <= 0:
        return ""
    if size <= SAFEBLOCK:
        return fp.read(size)
    data = []
    while size > 0:
        block = fp.read(min(size, SAFEBLOCK))
        if not block:
            break
        data.append(block)
        size = size - len(block)
    return string.join(data, "")


def i16(c,o=0):
    return ord(c[o+1]) + (ord(c[o])<<8)

def i32(c,o=0):
    return ord(c[o+3]) + (ord(c[o+2])<<8) + (ord(c[o+1])<<16) + (ord(c[o])<<24)

#
# Parser

def Skip(self, marker):
    n = i16(self.fp.read(2))-2
    _safe_read(self.fp, n)

def APP(self, marker):
    #
    # Application marker.  Store these in the APP dictionary.
    # Also look for well-known application markers.

    n = i16(self.fp.read(2))-2
    s = _safe_read(self.fp, n)

    app = "APP%d" % (marker&15)

    self.app[app] = s # compatibility
    self.applist.append((app, s))

    if marker == 0xFFE0 and s[:4] == "JFIF":
        # extract JFIF information
        self.info["jfif"] = version = i16(s, 5) # version
        self.info["jfif_version"] = divmod(version, 256)
        # extract JFIF properties
        try:
            jfif_unit = ord(s[7])
            jfif_density = i16(s, 8), i16(s, 10)
        except:
            pass
        else:
            if jfif_unit == 1:
                self.info["dpi"] = jfif_density
            self.info["jfif_unit"] = jfif_unit
            self.info["jfif_density"] = jfif_density
    elif marker == 0xFFE1 and s[:5] == "Exif\0":
        # extract Exif information (incomplete)
        self.info["exif"] = s # FIXME: value will change
    elif marker == 0xFFE2 and s[:5] == "FPXR\0":
        # extract FlashPix information (incomplete)
        self.info["flashpix"] = s # FIXME: value will change
    elif marker == 0xFFE2 and s[:12] == "ICC_PROFILE\0":
        # Since an ICC profile can be larger than the maximum size of
        # a JPEG marker (64K), we need provisions to split it into
        # multiple markers. The format defined by the ICC specifies
        # one or more APP2 markers containing the following data:
        #   Identifying string      ASCII "ICC_PROFILE\0"  (12 bytes)
        #   Marker sequence number  1, 2, etc (1 byte)
        #   Number of markers       Total of APP2's used (1 byte)
        #   Profile data            (remainder of APP2 data)
        # Decoders should use the marker sequence numbers to
        # reassemble the profile, rather than assuming that the APP2
        # markers appear in the correct sequence.
        self.icclist.append(s)
    elif marker == 0xFFEE and s[:5] == "Adobe":
        self.info["adobe"] = i16(s, 5)
        # extract Adobe custom properties
        try:
            adobe_transform = ord(s[1])
        except:
            pass
        else:
            self.info["adobe_transform"] = adobe_transform
    for k,v in self.info.iteritems():
        print "\t", k,':',v

def COM(self, marker):
    #
    # Comment marker.  Store these in the APP dictionary.

    n = i16(self.fp.read(2))-2
    s = _safe_read(self.fp, n)

    self.app["COM"] = s # compatibility
    self.applist.append(("COM", s))

def SOF(self, marker):
    #
    # Start of frame marker.  Defines the size and mode of the
    # image.  JPEG is colour blind, so we use some simple
    # heuristics to map the number of layers to an appropriate
    # mode.  Note that this could be made a bit brighter, by
    # looking for JFIF and Adobe APP markers.

    n = i16(self.fp.read(2))-2
    s = _safe_read(self.fp, n)
    self.size = i16(s[3:]), i16(s[1:])
    print "\t Size:", self.size

    self.bits = ord(s[0])
    if self.bits != 8:
        raise SyntaxError("cannot handle %d-bit layers" % self.bits)

    self.layers = ord(s[5])
    if self.layers == 1:
        self.mode = "L"
    elif self.layers == 3:
        self.mode = "RGB"
    elif self.layers == 4:
        self.mode = "CMYK"
    else:
        raise SyntaxError("cannot handle %d-layer images" % self.layers)
    print "\t Mode:", self.mode

    if marker in [0xFFC2, 0xFFC6, 0xFFCA, 0xFFCE]:
        self.info["progressive"] = self.info["progression"] = 1

    if self.icclist:
        # fixup icc profile
        self.icclist.sort() # sort by sequence number
        if ord(self.icclist[0][13]) == len(self.icclist):
            profile = []
            for p in self.icclist:
                profile.append(p[14:])
            icc_profile = string.join(profile, "")
        else:
            icc_profile = None # wrong number of fragments
        self.info["icc_profile"] = icc_profile
        self.icclist = None

    for i in range(6, len(s), 3):
        t = s[i:i+3]
        # 4-tuples: id, vsamp, hsamp, qtable
        self.layer.append((t[0], ord(t[1])/16, ord(t[1])&15, ord(t[2])))

def DQT(self, marker):
    #
    # Define quantization table.  Support baseline 8-bit tables
    # only.  Note that there might be more than one table in
    # each marker.

    # FIXME: The quantization tables can be used to estimate the
    # compression quality.

    n = i16(self.fp.read(2))-2
    s = _safe_read(self.fp, n)
    while len(s):
        if len(s) < 65:
            raise SyntaxError("bad quantization table marker")
        v = ord(s[0])
        if v/16 == 0:
            self.quantization[v&15] = array.array("b", s[1:65])
            print "\t", self.quantization[v&15]
            s = s[65:]
        else:
            return # FIXME: add code to read 16-bit tables!
            # raise SyntaxError, "bad quantization table element size"


#
# JPEG marker table

MARKER = {
    0xFFC0: ("SOF0", "Baseline DCT", SOF),
    0xFFC1: ("SOF1", "Extended Sequential DCT", SOF),
    0xFFC2: ("SOF2", "Progressive DCT", SOF),
    0xFFC3: ("SOF3", "Spatial lossless", SOF),
    0xFFC4: ("DHT", "Define Huffman table", Skip),
    0xFFC5: ("SOF5", "Differential sequential DCT", SOF),
    0xFFC6: ("SOF6", "Differential progressive DCT", SOF),
    0xFFC7: ("SOF7", "Differential spatial", SOF),
    0xFFC8: ("JPG", "Extension", None),
    0xFFC9: ("SOF9", "Extended sequential DCT (AC)", SOF),
    0xFFCA: ("SOF10", "Progressive DCT (AC)", SOF),
    0xFFCB: ("SOF11", "Spatial lossless DCT (AC)", SOF),
    0xFFCC: ("DAC", "Define arithmetic coding conditioning", Skip),
    0xFFCD: ("SOF13", "Differential sequential DCT (AC)", SOF),
    0xFFCE: ("SOF14", "Differential progressive DCT (AC)", SOF),
    0xFFCF: ("SOF15", "Differential spatial (AC)", SOF),
    0xFFD0: ("RST0", "Restart 0", None),
    0xFFD1: ("RST1", "Restart 1", None),
    0xFFD2: ("RST2", "Restart 2", None),
    0xFFD3: ("RST3", "Restart 3", None),
    0xFFD4: ("RST4", "Restart 4", None),
    0xFFD5: ("RST5", "Restart 5", None),
    0xFFD6: ("RST6", "Restart 6", None),
    0xFFD7: ("RST7", "Restart 7", None),
    0xFFD8: ("SOI", "Start of image", None),
    0xFFD9: ("EOI", "End of image", None),
    0xFFDA: ("SOS", "Start of scan", Skip),
    0xFFDB: ("DQT", "Define quantization table", DQT),
    0xFFDC: ("DNL", "Define number of lines", Skip),
    0xFFDD: ("DRI", "Define restart interval", Skip),
    0xFFDE: ("DHP", "Define hierarchical progression", SOF),
    0xFFDF: ("EXP", "Expand reference component", Skip),
    0xFFE0: ("APP0", "Application segment 0", APP),
    0xFFE1: ("APP1", "Application segment 1", APP),
    0xFFE2: ("APP2", "Application segment 2", APP),
    0xFFE3: ("APP3", "Application segment 3", APP),
    0xFFE4: ("APP4", "Application segment 4", APP),
    0xFFE5: ("APP5", "Application segment 5", APP),
    0xFFE6: ("APP6", "Application segment 6", APP),
    0xFFE7: ("APP7", "Application segment 7", APP),
    0xFFE8: ("APP8", "Application segment 8", APP),
    0xFFE9: ("APP9", "Application segment 9", APP),
    0xFFEA: ("APP10", "Application segment 10", APP),
    0xFFEB: ("APP11", "Application segment 11", APP),
    0xFFEC: ("APP12", "Application segment 12", APP),
    0xFFED: ("APP13", "Application segment 13", APP),
    0xFFEE: ("APP14", "Application segment 14", APP),
    0xFFEF: ("APP15", "Application segment 15", APP),
    0xFFF0: ("JPG0", "Extension 0", None),
    0xFFF1: ("JPG1", "Extension 1", None),
    0xFFF2: ("JPG2", "Extension 2", None),
    0xFFF3: ("JPG3", "Extension 3", None),
    0xFFF4: ("JPG4", "Extension 4", None),
    0xFFF5: ("JPG5", "Extension 5", None),
    0xFFF6: ("JPG6", "Extension 6", None),
    0xFFF7: ("JPG7", "Extension 7", None),
    0xFFF8: ("JPG8", "Extension 8", None),
    0xFFF9: ("JPG9", "Extension 9", None),
    0xFFFA: ("JPG10", "Extension 10", None),
    0xFFFB: ("JPG11", "Extension 11", None),
    0xFFFC: ("JPG12", "Extension 12", None),
    0xFFFD: ("JPG13", "Extension 13", None),
    0xFFFE: ("COM", "Comment", COM)
}


##
# Image plugin for JPEG and JFIF images.

class JpegImageFile(format_jpg.Image):

    def __init__(self, filepath):
        format_jpg.Image.__init__(self)

        self.tile = None
        self.readonly = 1 # until we know better

        self.decoderconfig = ()
        self.decodermaxblock = MAXBLOCK

        if filepath:
            # filename
            self.fp = open(filepath, "rb")
            self.filename = filepath

        try:
            self._open()
        except IndexError, v: # end of data
            traceback.print_exc()
            raise SyntaxError, v
        except TypeError, v: # end of data (ord)
            traceback.print_exc()
            raise SyntaxError, v
        except KeyError, v: # unsupported mode
            traceback.print_exc()
            raise SyntaxError, v
        except EOFError, v: # got header but not the first frame
            traceback.print_exc()
            raise SyntaxError, v

        if not self.mode or self.size[0] <= 0:
            raise SyntaxError, "not identified by this driver"

    def _open(self):

        s = self.fp.read(1)

        if ord(s[0]) != 255:
            raise SyntaxError("not a JPEG file")

        # Create attributes
        self.bits = self.layers = 0

        # JPEG specifics (internal)
        self.layer = []
        self.huffman_dc = {}
        self.huffman_ac = {}
        self.quantization = {}
        self.app = {} # compatibility
        self.applist = []
        self.icclist = []

        while 1:

            s = s + self.fp.read(1)

            i = i16(s)

            if MARKER.has_key(i):
                name, description, handler = MARKER[i]
                print hex(i), name, description
                if handler is not None:
                    handler(self, i)
                if i == 0xFFDA: # start of scan
                    rawmode = self.mode
                    if self.mode == "CMYK":
                        rawmode = "CMYK;I" # assume adobe conventions
                    self.tile = [("jpeg", (0,0) + self.size, 0, (rawmode, ""))]
                    # self.__offset = self.fp.tell()
                    break
                s = self.fp.read(1)
            elif i == 0 or i == 65535:
                # padded marker or junk; move on
                s = "\xff"
            else:
                raise SyntaxError("no marker found")

    def load(self):
        "Load image data based on tile list"

        pixel = format_jpg.Image.load(self)

        if self.tile is None:
            raise IOError("cannot load this image")
        if not self.tile:
            return pixel

        self.map = None

        readonly = 0

        if self.filename and len(self.tile) == 1:
            # try memory mapping
            d, e, o, a = self.tile[0]
            if d == "raw" and a[0] == self.mode and a[0] in jpg._MAPMODES:
                try:
                    if hasattr(jpg.core, "map"):
                        # use built-in mapper
                        self.map = jpg.core.map(self.filename)
                        self.map.seek(o)
                        self.im = self.map.readimage(
                            self.mode, self.size, a[1], a[2]
                            )
                    else:
                        # use mmap, if possible
                        import mmap
                        file = open(self.filename, "r+")
                        size = os.path.getsize(self.filename)
                        # FIXME: on Unix, use PROT_READ etc
                        self.map = mmap.mmap(file.fileno(), size)
                        self.im = jpg.core.map_buffer(
                            self.map, self.size, d, e, o, a
                            )
                    readonly = 1
                except (AttributeError, EnvironmentError, ImportError):
                    self.map = None

        self.load_prepare()

        read = self.fp.read
        seek = self.fp.seek

        if not self.map:

            # sort tiles in file order
            self.tile.sort(_tilesort)

            try:
                # FIXME: This is a hack to handle TIFF's JpegTables tag.
                prefix = self.tile_prefix
            except AttributeError:
                prefix = ""

            for d, e, o, a in self.tile:
                d = format_jpg._getdecoder(self.mode, d, a, self.decoderconfig)
                seek(o)
                try:
                    d.setimage(self.im, e)
                except ValueError:
                    continue
                b = prefix
                t = len(b)
                while 1:
                    s = read(self.decodermaxblock)
                    if not s:
                        self.tile = []
                        raise IOError("image file is truncated (%d bytes not processed)" % len(b))
                    b = b + s
                    n, e = d.decode(b)
                    if n < 0:
                        break
                    b = b[n:]
                    t = t + n

        self.tile = []
        self.readonly = readonly

        self.fp = None # might be shared

        if not self.map and e < 0:
            raise_ioerror(e)

        # post processing
        if hasattr(self, "tile_post_rotate"):
            # FIXME: This is a hack to handle rotated PCD's
            self.im = self.im.rotate(self.tile_post_rotate)
            self.size = self.im.size

        return format_jpg.Image.load(self)

    def load_prepare(self):
        # create image memory if necessary
        if not self.im or\
           self.im.mode != self.mode or self.im.size != self.size:
            print self.mode, self.size
            self.im = format_jpg.core.new(self.mode, self.size)
        # create palette (optional)
        if self.mode == "P":
            jpg.Image.load(self)

