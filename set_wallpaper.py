#!/usr/bin/env python
# encoding: utf-8

import argparse
import struct
import time

import xcffib
import xcffib.xproto

import cairocffi
import cairocffi.pixbuf
import cairocffi.xcb


class ConnectionWrapper(object):
    """Convenience wrapper around the bits of xcffib we need."""

    def __init__(self, conn, persist=True):
        self.conn = conn
        self.screen = conn.get_setup().roots[0]
        self.root = self.screen.root
        self.width = self.screen.width_in_pixels
        self.height = self.screen.height_in_pixels
        self.depth = self.screen.root_depth
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
        pixmap = self.create_pixmap()
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


def fade_background_to_image(path, secs, fps):
    # Assume the painting takes 0 seconds for this calculation. In reality
    # this is a crappy assumption, but we're just fading in a wallpaper so
    # who cares.
    steps = max(1, fps * secs)
    step = 1 / steps
    sleep = secs / steps

    image = load_image(path)
    wrapper = ConnectionWrapper(xcffib.Connection())
    pixmap = wrapper.get_current_background()
    surface = wrapper.create_surface_for_pixmap(pixmap)

    with cairocffi.Context(surface) as context:
        context.set_source_surface(image)
        opacity = 0
        for i in range(steps):
            context.paint_with_alpha(i * step)
            wrapper.set_background(pixmap)
            time.sleep(sleep)


def main():
    parser = argparse.ArgumentParser(description='Control desktop wallpaper.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--copy-root-window', dest='copy_root', action='store_true',
                       help='Set the background to the contents of the root window.')
    group.add_argument('--image', dest='image', type=str,
                       help='Image to set the brackground to.')
    parser.add_argument('--fade-secs', dest='fade_secs', type=int, default=0,
                        help='Number of seconds to fade from current background to new')
    parser.add_argument('--fade-fps', dest='fade_fps', type=int, default=20,
                        help='Number of FPS to aim for during the fade')

    args = parser.parse_args()

    if args.copy_root:
        wrapper = ConnectionWrapper(xcffib.Connection())
        wrapper.set_background_to_root_window_contents()
    elif args.image:
        fade_background_to_image(args.image, args.fade_secs, args.fade_fps)
