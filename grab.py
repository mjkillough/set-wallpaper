#!/usr/bin/env python
# encoding: utf-8

import struct
import math

import Xlib.display
import Xlib.protocol.request
import Xlib.X
import Xlib.Xatom
import Xlib.xobject.drawable


AllPlanes = 2 ** 32 - 1 # from /usr/include/X11/Xlib.h


class Display(object):
    """Utility wrapper for Xlib.display.Display."""

    def __init__(self, display):
        self.display = display
        self.screen = display.screen()
        self.geometry = self.screen.root.get_geometry()
        self.width = self.geometry.width
        self.height = self.geometry.height
        self.depth = self.geometry.depth
        self.big_endian = struct.unpack('BB', struct.pack('H', 0x0100))[0]

    def scrape_root_window_into_pixmap(self):
        """Scrape the contents of the root window (usually from DM/Plymouth) into pixmap

        This will allow us to do a smooth transition from the login/boot screen to
        the background.
        """
        pixmap = self.screen.root.create_pixmap(self.width, self.height, self.depth)
        gc = self.screen.root.create_gc(
            function=Xlib.X.GXcopy,
            fill_style=Xlib.X.FillSolid,
            subwindow_mode=Xlib.X.IncludeInferiors,
        )
        pixmap.copy_area(gc, self.screen.root, 0, 0, self.width, self.height, 0, 0)
        gc.free()
        return pixmap

    def get_current_background_as_image(self):
        """Returns a PIL.Image containing a copy of the current background."""
        atom = self.display.intern_atom('_XROOTPMAP_ID')
        pixmap_id, = self.screen.root.get_full_property(atom, Xlib.Xatom.PIXMAP).value
        pixmap = Xlib.xobject.drawable.Pixmap(self.display.display, pixmap_id)

        data = pixmap.get_image(
            0, 0, self.width, self.height,
            Xlib.X.ZPixmap, AllPlanes
        ).data
        raw_mode = 'RGBX' if self.big_endian else 'BGRX'
        image = PIL.Image.frombytes('RGB', (self.width, self.height), data, 'raw', raw_mode)
        return image

    def create_solid_pixmap(self, color):
        """Creates a pixmap the size of the screen filled with a solid colour."""
        pixmap = self.screen.root.create_pixmap(self.width, self.height, self.depth)
        gc = pixmap.create_gc(foreground=color)
        pixmap.fill_rectangle(gc, 0, 0, self.width, self.height)
        gc.free()
        return pixmap

    def create_pixmap_from_image(self, image):
        """Creates a pixmap for the PIL image.

        This function is very incomplete and extremely dodgy. :) It's
        a simplified version of python-xlib's Drawable.put_pil_image.

        """
        assert image.mode == 'RGB'
        depth = 24
        stride = 4 * image.width
        raw_mode = 'RGBX' if self.big_endian else 'BGRX'
        data = image.tobytes("raw", raw_mode)

        pixmap = self.screen.root.create_pixmap(image.width, image.height, depth)
        gc = pixmap.create_gc()

        # Unfortunately, we can't send it to X in one go, so we'll need to split it
        # up. We rely on the fact that the BPP is an even number a lot here.
        max_request_length = self.display.display.info.max_request_length << 2
        max_length = max_request_length - Xlib.protocol.request.PutImage._request.static_size
        rows_per_chunk = max_length // stride
        chunks = math.ceil(image.height / rows_per_chunk)
        for chunk_idx in range(chunks):
            y = chunk_idx * rows_per_chunk
            height = y + rows_per_chunk
            chunk_data = data[y*stride:height*stride]
            pixmap.put_image(
                gc, 0, y, image.width, rows_per_chunk,
                Xlib.X.ZPixmap, depth, 0, chunk_data
            )

        gc.free()
        return pixmap

    def set_background_to_pixmap(self, pixmap):
        """Sets the background of the root window to the given pixmap.

        (I think) the pixmap can be freed once it's done.
        """
        for atom_name in ['_XROOTPMAP_ID', 'ESETROOT_PMAP_ID']:
            atom = self.display.intern_atom(atom_name)
            self.screen.root.change_property(atom, Xlib.Xatom.PIXMAP, 32, [pixmap.id])

        geo = self.screen.root.get_geometry()
        self.screen.root.change_attributes(background_pixmap=pixmap)
        self.screen.root.clear_area(width=self.width, height=self.height)
        self.display.flush()



# Inspiration:
# https://blogs.gnome.org/halfline/2009/11/28/plymouth-%E2%9F%B6-x-transition/
# Examples:
# https://git.gnome.org/browse/gdm/commit/?h=plymouth-integration&id=e6ed6f48c35a6c736a5cde2dcfb6c10941e07809
# https://github.com/derf/feh/blob/master/src/wallpaper.c
# https://bugzilla.gnome.org/attachment.cgi?id=125864&action=diff

import PIL.Image

if __name__ == '__main__':
    manager = Display(Xlib.display.Display())
    # pixmap = manager.scrape_root_window_into_pixmap()
    # manager.set_background_to_pixmap(pixmap)

    image = PIL.Image.open('/home/mjk/Photos/wallpaper')
    # pixmap = manager.create_pixmap_from_image(image)
    image = manager.get_current_background_as_image()
    pixmap = manager.create_pixmap_from_image(image)
    manager.set_background_to_pixmap(pixmap)
