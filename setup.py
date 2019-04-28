#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pyrtitions
version = pyrtitions.__version__

try:
    import fastentrypoints
except ImportError:
    from setuptools.command import easy_install
    import pkg_resources
    easy_install.main(['fastentrypoints'])
    pkg_resources.require('fastentrypoints')
    import fastentrypoints

import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
  name = 'pyrtitions',
  py_modules = ['pyrtitions'],
  version = version,
  description = 'A small library to get partition information on Linux',
  author = 'Arsenijs Picugins',
  author_email = 'crimier@yandex.ru',
  url = 'https://github.com/CRImier/pyrtitions',
  download_url = 'https://github.com/CRImier/pyrtitions/archive/{}.tar.gz'.format(version),
  keywords = ['linux', 'partitions'],
  entry_points={"console_scripts": ["pyrtitions = pyrtitions:__main__"]}
)
