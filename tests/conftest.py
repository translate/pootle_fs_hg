#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from pkgutil import iter_modules

from django import setup
from django.conf import settings

from . import fixtures


def pytest_configure():
    os.environ["HGUSER"] = "hg@pootle.test"

    if not settings.configured:
        from pootle import syspath_override  # Needed for monkey-patching
        syspath_override
        os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
        WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['POOTLE_SETTINGS'] = os.path.join(
            WORKING_DIR, 'settings.py')
        setup()  # Required until pytest-dev/pytest-django#146 is fixed


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name

pytest_plugins = tuple(
    ['pytest_pootle']
    + [p for p in _load_fixtures(fixtures, )])
