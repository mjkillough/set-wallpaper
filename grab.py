#!/usr/bin/env python
# encoding: utf-8

import xcffib
import xcffib.xproto


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

    @staticmethod
    def copy_drawable_into_persistent_pixmap(drawable):
        """Creates a copy of the drawable as a pixmap that is retained
        after the display its destroyed.

        We do this by making a new connection to the X Display, with a close
        down mode of RetainPermanent. We then create a Pixmap on this new
        connection, which means it gets left behind.
        """
        wrapper = ConnectionWrapper(xcffib.Connection(), persist=True)
        pixmap = wrapper.copy_pixmap(drawable)
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

    def copy_pixmap(self, drawable):
        pixmap = self.create_pixmap()
        gc = self.conn.generate_id()
        self.conn.core.CreateGC(gc, self.root, 0, [])
        self.conn.core.CopyArea(drawable, pixmap, gc, 0, 0, 0, 0, self.width, self.height)
        return pixmap

    def get_current_background(self):
        pass

    def set_background_to_root_window_contents(self):
        """Scrapes the contents of the root window and sets them as the background.

        Plymouth (and perhaps DMs too) leave their framebuffer behind. Grab it
        and properly set it as the background, so that we can have nice transitions.
        """
        pixmap = self.copy_drawable_into_persistent_pixmap(self.root)
        self.set_background(pixmap)

    def set_background(self, pixmap):
        self._set_proprety_to_pixmap('_XROOTPMAP_ID', pixmap)
        self._set_proprety_to_pixmap('ESETROOT_PMAP_ID', pixmap)
        self.conn.core.ChangeWindowAttributes(self.root, xcffib.xproto.CW.BackPixmap, [pixmap])
        self.conn.flush()

# Inspiration:
# https://blogs.gnome.org/halfline/2009/11/28/plymouth-%E2%9F%B6-x-transition/
# Examples:
# https://git.gnome.org/browse/gdm/commit/?h=plymouth-integration&id=e6ed6f48c35a6c736a5cde2dcfb6c10941e07809
# https://github.com/derf/feh/blob/master/src/wallpaper.c
# https://bugzilla.gnome.org/attachment.cgi?id=125864&action=diff

if __name__ == '__main__':
    wrapper = ConnectionWrapper(xcffib.Connection())
    wrapper.set_background_to_root_window_contents()
