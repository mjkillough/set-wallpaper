# set-wallpaper

A script to set the desktop wallpaper on Linux, with an optional fade transition from the wallpaper that was previously set.

If run with `--copy-root-window` it will copy the contents of the root window and set it as the desktop wallpaper. If it is then called again with an image, you can get a smooth transition from your DM to X session. If used with my [notes for a smooth boot experience](https://github.com/mjkillough/notes/blob/master/boot-experience.md) and `X -background none`, then it can enable a smooth transition from the boot splash screen to your desktop wallpaper.

Full usage:

```
usage: set-wallpaper.py [-h] (--copy-root-window | --image IMAGE)
                        [--fade-secs FADE_SECS] [--fade-fps FADE_FPS]

Control desktop wallpaper.

optional arguments:
  -h, --help            show this help message and exit
  --copy-root-window    Set the background to the contents of the root window.
  --image IMAGE         Image to set the brackground to.
  --fade-secs FADE_SECS
                        Number of seconds to fade from current background to
                        new
  --fade-fps FADE_FPS   Number of FPS to aim for during the fade
```


## License

MIT


## Installing

Install non-Python dependencies (see below) and then: `python setup.py install`.

Arch users can use [this PKGBUILD](https://github.com/mjkillough/arch-packages/tree/master/set-wallpaper).


## Dependencies

Developed/run on Python 3. It should be possible to get it to run on Python 2 with some simple tweaks (if it doesn't already).

Depends on Python packages:

- `xcffib`
- `cairocffi`

... these are in `requirements.txt` as usual.

System packages:
- `cairo`
- `gdk-pixbuf`


## Developing

The usual:

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
python setup.py develop
```

and then run `set-wallpaper` to test your changes.

## Tests

None. Sorry, the script works for me and I haven't had a need to tweak it. If I'm bored I'll come back and add some.


## Acknowledgements

Inspired by:
- https://blogs.gnome.org/halfline/2009/11/28/plymouth-%E2%9F%B6-x-transition/

Built whilst looking at examples:
- https://git.gnome.org/browse/gdm/commit/?h=plymouth-integration&id=e6ed6f48c35a6c736a5cde2dcfb6c10941e07809
- https://github.com/derf/feh/blob/master/src/wallpaper.c
- https://bugzilla.gnome.org/attachment.cgi?id=125864&action=diff
