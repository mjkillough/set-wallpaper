#!/usr/bin/env python
# encoding: utf-8

import struct
import time

import xcffib
import xcffib.xproto

import cairocffi
import cairocffi.pixbuf
import cairocffi.xcb

class ConnectionWrapper(object):

    def __init__(self, conn, persist=False):
        self.conn = conn
        self.screen = conn.get_setup().roots[0]
        self.root = self.screen.root
        self.width = self.screen.width_in_pixels
        self.height = self.screen.height_in_pixels
        print(self.width, self.height)
        self.depth = 24 # XXX
        if persist:
            self.conn.core.SetCloseDownMode(xcffib.xproto.CloseDown.RetainPermanent)

    def _intern_atom(self, name):
        return self.conn.core.InternAtom(False, len(name), name).reply().atom

    def _set_proprety_to_pixmap(self, name, pixmap):
        self.conn.core.ChangeProperty(
            xcffib.xproto.PropMode.Replace,
            self.root,
            self._intern_atom(name),
            xcffib.xproto.Atom.PIXMAP,
            32, 1, [pixmap]
        )

    def _get_pixmap_property(self, name):
        reply = self.conn.core.GetProperty(
            False, self.root, self._intern_atom(name),
            xcffib.xproto.Atom.PIXMAP, 0, 32
        ).reply()
        if not reply.value_len:
            return None
        return struct.unpack('I', reply.value.buf())[0]

    def _find_root_visual(self):
        for depth in self.screen.allowed_depths:
            for v in depth.visuals:
                if v.visual_id == self.screen.root_visual:
                    return v

    @staticmethod
    def create_persistent_pixmap():
        """Creates a pixmap that persists after the Display's connection is closed.

        We do this by making a new connection to the X Display, with a close
        down mode of RetainPermanent. We then create a Pixmap on this new
        connection, which means it gets left behind.
        """
        wrapper = ConnectionWrapper(xcffib.Connection(), persist=True)
        pixmap = wrapper.create_pixmap()
        wrapper.conn.flush()
        wrapper.conn.disconnect()
        return pixmap

    def create_pixmap(self):
        pixmap = self.conn.generate_id()
        self.conn.core.CreatePixmap(
            self.depth, pixmap,
            self.root, self.width, self.height
        )
        return pixmap

    def copy_pixmap(self, src, dest):
        gc = self.conn.generate_id()
        self.conn.core.CreateGC(gc, self.root, 0, [])
        self.conn.core.CopyArea(src, dest, gc, 0, 0, 0, 0, self.width, self.height)

    def create_surface_for_pixmap(self, pixmap):
        return cairocffi.xcb.XCBSurface(
            self.conn, pixmap, self._find_root_visual(),
            self.width, self.height
        )

    def get_current_background(self):
        """Returns the pixmap for the current background, or None if it is not set."""
        pixmap = self._get_pixmap_property('_XROOTPMAP_ID')
        if pixmap is not None:
            return pixmap
        return self._get_pixmap_property('ESETROOT_PMAP_ID')

    def set_background_to_root_window_contents(self):
        """Scrapes the contents of the root window and sets them as the background.

        Plymouth (and perhaps DMs too) leave their framebuffer behind. Grab it
        and properly set it as the background, so that we can have nice transitions.
        """
        pixmap = self.create_persistent_pixmap()
        self.copy_pixmap(self.root, pixmap)
        self.set_background(pixmap)

    def set_background(self, pixmap):
        self._set_proprety_to_pixmap('_XROOTPMAP_ID', pixmap)
        self._set_proprety_to_pixmap('ESETROOT_PMAP_ID', pixmap)
        self.conn.core.ChangeWindowAttributes(self.root, xcffib.xproto.CW.BackPixmap, [pixmap])
        self.conn.core.ClearArea(0, self.root, 0, 0, self.width, self.height)
        self.conn.flush()


def load_image(path):
    with open(path, 'rb') as f:
        surface, mimetype = cairocffi.pixbuf.decode_to_image_surface(f.read())
        return surface

# Inspiration:
# https://blogs.gnome.org/halfline/2009/11/28/plymouth-%E2%9F%B6-x-transition/
# Examples:
# https://git.gnome.org/browse/gdm/commit/?h=plymouth-integration&id=e6ed6f48c35a6c736a5cde2dcfb6c10941e07809
# https://github.com/derf/feh/blob/master/src/wallpaper.c
# https://bugzilla.gnome.org/attachment.cgi?id=125864&action=diff

if __name__ == '__main__':
    wrapper = ConnectionWrapper(xcffib.Connection())
    image = load_image('/home/mjk/Photos/random-wallpaper.jpg')
    current_pixmap = wrapper.get_current_background()
    pixmap_surface = wrapper.create_surface_for_pixmap(current_pixmap)
    with cairocffi.Context(pixmap_surface) as context:
        context.set_source_surface(image)
        for opacity in range(10, 100, 10):
            context.paint_with_alpha(opacity / 100)
            wrapper.set_background(current_pixmap)
            time.sleep(0.05)
