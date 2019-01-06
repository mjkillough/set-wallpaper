#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup


setup(
    name='set-wallpaper',
    description='Script to change wallpaper, with optional fade from previous.',
    version='1.1',
    author='Michael Killough',
    author_email='michaeljkillough@gmail.com',
    url='https://github.com/mjkillough/set-wallpaper',
    platforms=['linux'],
    license=['MIT'],
    install_requires=[
        'cairocffi',
        'xcffib'
    ],

    py_modules=['set_wallpaper'],
    entry_points = {
        'console_scripts': [
            'set-wallpaper=set_wallpaper:main',
        ],
    }
)