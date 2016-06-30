# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from pytest_pootle.factories import ProjectDBFactory
# from pytest_pootle.fs.suite import (
#    run_add_test, run_fetch_test, run_rm_test, run_merge_test,
#    check_files_match)

from pootle_fs.utils import FSPlugin

from pootle_fs_hg.plugin import DEFAULT_COMMIT_MSG
from pootle_fs_hg.utils import tmp_hg


def _check_hg_fs(plugin, response):
    # with tmp_hg(plugin.fs_url) as (tmp_repo_path, tmp_repo):
    #   check_files_match(tmp_repo_path, response)
    pass


@pytest.mark.django_db
def test_plugin_instance(english):
    project = ProjectDBFactory(source_language=english)
    project.config["pootle_fs.fs_type"] = "hg"
    project.config["pootle_fs.fs_url"] = "bar"
    project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    hg_plugin = FSPlugin(project)
    assert hg_plugin.project == hg_plugin.plugin.project == project
    assert hg_plugin.is_cloned is False
    # assert hg_plugin.stores.exists() is False
    # assert hg_plugin.translations.exists() is False


@pytest.mark.django_db
def test_plugin_instance_bad_args(hg_project):
    hg_plugin = FSPlugin(hg_project)

    with pytest.raises(TypeError):
        hg_plugin.plugin.__class__()

    with pytest.raises(TypeError):
        hg_plugin.plugin.__class__("FOO")


@pytest.mark.django_db
def __test_plugin_pull(hg_project_1):
    hg_plugin = FSPlugin(hg_project_1)
    assert hg_plugin.is_cloned is False
    hg_plugin.pull()
    assert hg_plugin.is_cloned is True


@pytest.mark.django_db
def __test_plugin_commit_message(hg_project):
    hg_plugin = FSPlugin(hg_project)
    NEW_COMMIT_MSG = "New commit message"
    hg_plugin.pull()
    assert not hg_plugin.config.get("pootle_fs.commit_message")

    # make some updates
    hg_plugin.push_translations()

    # check that commit message uses default when not set in config
    with tmp_hg(hg_plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.hg.log('-1', '--pretty=%s')
        assert last_commit == DEFAULT_COMMIT_MSG

    # update the config
    hg_plugin.config["pootle_fs.commit_message"] = NEW_COMMIT_MSG

    # make further updates
    hg_plugin.add_translations()
    hg_plugin.sync_translations()

    # test that sync_translations committed with new commit message
    with tmp_hg(hg_plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_commit = tmp_repo.hg.log('-1', '--pretty=%s')
        assert last_commit == NEW_COMMIT_MSG


@pytest.mark.django_db
def __test_plugin_commit_author(hg_project):
    plugin = FSPlugin(hg_project)

    NEW_AUTHOR_NAME = "New Author"
    NEW_AUTHOR_EMAIL = "new@email.address"
    plugin.pull()
    assert not plugin.config.get("pootle_fs.author_name")
    assert not plugin.config.get("pootle_fs.author_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_hg(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.hg.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.hg.log('-1', '--pretty=%ae')
        hg_config = tmp_repo.config_reader()
        default_user = os.environ["USER"]
        default_email = (
            "%s@%s"
            % (default_user, os.environ.get("HOSTNAME", "")))
        assert (
            last_author_name
            == hg_config.get_value("user", "name", default_user))
        assert (
            last_author_email
            == hg_config.get_value("user", "email", default_email))

    # update the author name/email in config
    plugin.config["pootle_fs.author_name"] = NEW_AUTHOR_NAME
    plugin.config["pootle_fs.author_email"] = NEW_AUTHOR_EMAIL

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit author
    with tmp_hg(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_author_name = tmp_repo.hg.log('-1', '--pretty=%an')
        last_author_email = tmp_repo.hg.log('-1', '--pretty=%ae')
        assert last_author_name == NEW_AUTHOR_NAME
        assert last_author_email == NEW_AUTHOR_EMAIL


@pytest.mark.django_db
def __test_plugin_commit_committer(hg_project):
    plugin = FSPlugin(hg_project)

    NEW_COMMITTER_NAME = "New Committer"
    NEW_COMMITTER_EMAIL = "new@email.address"

    plugin.pull()
    assert not plugin.config.get("pootle_fs.committer_name")
    assert not plugin.config.get("pootle_fs.committer_email")

    # make some updates
    plugin.push_translations()

    # check that commit message uses system default when not set in config
    with tmp_hg(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.hg.log('-1', '--pretty=%an')
        last_committer_email = tmp_repo.hg.log('-1', '--pretty=%ae')
        hg_config = tmp_repo.config_reader()
        default_user = os.environ["USER"]
        default_email = (
            "%s@%s"
            % (default_user, os.environ.get("HOSTNAME", "")))
        assert (
            last_committer_name
            == hg_config.get_value("user", "name", default_user))
        assert (
            last_committer_email
            == hg_config.get_value("user", "email", default_email))

    # update the committer name/email in config
    plugin.config["pootle_fs.committer_name"] = NEW_COMMITTER_NAME
    plugin.config["pootle_fs.committer_email"] = NEW_COMMITTER_EMAIL

    # make further updates
    plugin.add_translations()
    plugin.sync_translations()

    # test that sync_translations committed with new commit committer
    with tmp_hg(plugin.fs_url) as (tmp_repo_path, tmp_repo):
        last_committer_name = tmp_repo.hg.log('-1', '--pretty=%cn')
        last_committer_email = tmp_repo.hg.log('-1', '--pretty=%ce')
        assert last_committer_name == NEW_COMMITTER_NAME
        assert last_committer_email == NEW_COMMITTER_EMAIL


# Parametrized FETCH
@pytest.mark.django_db
def __test_plugin_fetch_translations(hg_project, fetch_translations):
    # run_fetch_test(
    #    plugin=FSPlugin(hg_project),
    #    check_fs=_check_hg_fs,
    #    **fetch_translations)
    pass


# Parametrized ADD
@pytest.mark.django_db
def __test_plugin_add_translations(hg_project, add_translations):
    # run_add_test(
    #    plugin=FSPlugin(hg_project),
    #    check_fs=_check_hg_fs,
    #    **add_translations)
    pass


# Parametrized RM
@pytest.mark.django_db
def __test_plugin_rm_translations(hg_project, rm_translations):
    # run_rm_test(
    #    plugin=FSPlugin(hg_project),
    #    check_fs=_check_hg_fs,
    #    **rm_translations)
    pass


# Parametrized MERGE
@pytest.mark.django_db
def __test_plugin_merge_fs(hg_project, merge_translations):
    # run_merge_test(
    #    plugin=FSPlugin(hg_project),
    #    check_fs=_check_hg_fs,
    #    **merge_translations)
    pass


# Parametrized MERGE
@pytest.mark.django_db
def __test_plugin_merge_pootle(hg_project, merge_translations):
    # run_merge_test(
    #    plugin=FSPlugin(hg_project),
    #    check_fs=_check_hg_fs,
    #    pootle_wins=True,
    #    **merge_translations)
    pass
