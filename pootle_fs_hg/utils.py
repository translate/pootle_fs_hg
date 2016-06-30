# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from contextlib import contextmanager

import hglib


@contextmanager
def tmp_hg(url):
    from django.conf import settings
    tmp_repo_path = os.path.join(
        settings.POOTLE_FS_PATH, "__tmp_hg_src__")
    if os.path.exists(tmp_repo_path):
        shutil.rmtree(tmp_repo_path)
    hglib.clone(url, tmp_repo_path)
    yield tmp_repo_path, hglib.open(tmp_repo_path)
    shutil.rmtree(tmp_repo_path)
