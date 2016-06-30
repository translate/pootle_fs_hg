# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager
from datetime import datetime
import os

import pytest

import hglib

# from pytest_pootle.fs.utils import create_test_suite

from pootle_fs_hg.utils import tmp_hg


@contextmanager
def get_dir_util():
    from distutils import dir_util
    yield dir_util
    # bug in distutils cache
    dir_util._path_created = {}


@pytest.fixture(scope="session", autouse=True)
def hg_env(post_db_setup, _django_cursor_wrapper):
    from django.conf import settings

    import pytest_pootle

    from pytest_pootle.factories import (
        ProjectDBFactory, TranslationProjectFactory)

    from pootle_fs.utils import FSPlugin
    from pootle_language.models import Language

    import tempfile

    with _django_cursor_wrapper:
        project0 = ProjectDBFactory(
            source_language=Language.objects.get(code="en"),
            code="hg_project_0")

        language0 = Language.objects.get(code="language0")
        TranslationProjectFactory(project=project0, language=language0)

        initial_src_path = os.path.abspath(
            os.path.join(
                os.path.dirname(pytest_pootle.__file__),
                "data/fs/example_fs"))
        fs_dir = tempfile.mkdtemp()
        settings.POOTLE_FS_PATH = fs_dir

        repo_path = os.path.join(fs_dir, "__hg_src_project_0__")
        os.mkdir(repo_path)
        hglib.init(repo_path)

        with tmp_hg(repo_path) as (tmp_repo_path, tmp_repo):
            with get_dir_util() as dir_util:
                dir_util.copy_tree(initial_src_path, tmp_repo_path)
            tmp_repo.add()
            tmp_repo.commit("Initial commit")
            tmp_repo.push()

        project0.config["pootle_fs.fs_type"] = "hg"
        project0.config["pootle_fs.fs_url"] = repo_path
        project0.config["pootle_fs.translation_paths"] = {
            "default": "/<language_code>/<dir_path>/<filename>.<ext>"}

        plugin = FSPlugin(project0)
        plugin.add()
        plugin.fetch()
        plugin.sync()

        # create_test_suite(plugin)

        project1 = ProjectDBFactory(
            source_language=Language.objects.get(code="en"),
            code="hg_project_1")

        TranslationProjectFactory(project=project1, language=language0)

        repo_path = os.path.join(fs_dir, "__hg_src_project_1__")
        hglib.init(repo_path)

        with tmp_hg(repo_path) as (tmp_repo_path, tmp_repo):
            with get_dir_util() as dir_util:
                dir_util.copy_tree(initial_src_path, tmp_repo_path)
            tmp_repo.add()
            tmp_repo.commit("Initial commit")
            tmp_repo.push()

        project1.config["pootle_fs.fs_type"] = "hg"
        project1.config["pootle_fs.fs_url"] = repo_path
        project1.config["pootle_fs.translation_paths"] = {
            "default": "/<language_code>/<dir_path>/<filename>.<ext>"}


@pytest.fixture
def hg_plugin_base(tmpdir, settings):
    # from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    with get_dir_util() as dir_util:
        dir_util.copy_tree(
            settings.POOTLE_FS_PATH,
            str(tmpdir))
    settings.POOTLE_FS_PATH = str(tmpdir)
    for project_code in ["project_0", "project_1"]:
        project = Project.objects.get(
            code="hg_%s" % project_code)
        repo_path = os.path.join(
            settings.POOTLE_FS_PATH,
            "__hg_src_%s__" % project_code)

        project.config["pootle_fs.fs_type"] = "hg"
        project.config["pootle_fs.fs_url"] = repo_path
        project.config["pootle_fs.translation_paths"] = {
            "default": "/<language_code>/<dir_path>/<filename>.<ext>"}

        # plugin = FSPlugin(project)
        # if os.path.exists(project.local_fs_path):
        #    origin = plugin.repo.remotes.origin
        #    cw = origin.config_writer
        #    cw.set("url", plugin.fs_url)
        #    cw.release()


@pytest.fixture
def hg_project(hg_plugin_base):
    from pootle_project.models import Project

    return Project.objects.get(code="hg_project_0")


@pytest.fixture
def hg_project_1(hg_plugin_base):
    from pootle_project.models import Project

    return Project.objects.get(code="hg_project_1")


def _hg_edit(plugin, filepath, content=None, message=None):
    with tmp_hg(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        dir_name = os.path.dirname(po_file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if content is None:
            content = str(datetime.now())
        if message is None:
            message = "Editing %s" % filepath
        with open(po_file, "w") as f:
            f.write(content)
        tmp_repo.index.add([filepath.strip("/")])
        tmp_repo.index.commit(message)
        tmp_repo.remotes.origin.push()


def _hg_remove(plugin, filepath):
    with tmp_hg(plugin.fs.url) as (tmp_repo_path, tmp_repo):
        po_file = os.path.join(
            tmp_repo_path, filepath.strip("/"))
        os.unlink(po_file)
        tmp_repo.index.commit("Removing %s" % filepath)
        tmp_repo.remotes.origin.push()


@pytest.fixture
def hg_plugin_suite(hg_plugin):
    # return create_test_suite(
    #    hg_plugin, edit_file=_hg_edit, remove_file=_hg_remove)
    pass
