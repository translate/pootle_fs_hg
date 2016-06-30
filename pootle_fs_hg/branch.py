# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager
import logging
import uuid


logger = logging.getLogger(__name__)


class PushError(Exception):
    pass


class HgBranch(object):

    def __init__(self, plugin, name):
        self.plugin = plugin
        self.name = name
        self.master = self.repo.branch()

    @property
    def exists(self):
        return self.name in [h.branch for h in self.repo.heads()]

    @property
    def project(self):
        return self.plugin.project

    @property
    def repo(self):
        return self.plugin.repo

    @property
    def is_active(self):
        return self.branch == self.name

    @property
    def branch(self):
        if not self.exists:
            self.__branch__ = self.create()
        return self.__branch__

    def create(self):
        logger.info(
            "Creating hg branch (%s): %s"
            % (self.project.code, self.name))
        self.repo.bookmark(self.name)
        return self.name

    def checkout(self):
        if not self.is_active:
            self.repo.update(self.name)
            logger.info(
                "Checking out hg branch (%s): %s"
                % (self.project.code, self.name))

    def add(self, paths):
        if paths:
            self.repo.index.add(paths)
            logger.info(
                "Adding paths (%s): %s"
                % (self.project.code, self.name))

    def rm(self, paths):
        if paths:
            self.repo.index.remove(paths)
            logger.info(
                "Removing path (%s): %s"
                % (self.project.code, self.name))

    def commit(self, msg, author=None, committer=None):
        # commit
        result = self.repo.index.commit(
            msg, author=author, committer=committer)
        logger.info(
            "Committing from hg branch (%s): %s"
            % (self.project.code, self.name))
        return result

    def push(self):
        # push to remote/$master
        result = self.repo.remotes.origin.push(
            "%s:%s"
            % (self.name, self.master.name))

        if result[0].flags != 256:
            raise PushError(
                "Commit was unsuccessful: %s"
                % result[0].summary)

        logger.info(
            "Pushing to remote hg branch (%s --> %s): %s"
            % (self.project.code,
               self.repo.remotes.origin.url,
               self.name))
        return result

    def destroy(self):
        self.repo.update(self.master)
        logger.info(
            "Destroying hg branch (%s): %s"
            % (self.project.code, self.name))


@contextmanager
def tmp_branch(plugin):
    branch = HgBranch(plugin, uuid.uuid4().hex)
    branch.checkout()
    try:
        yield branch
    finally:
        branch.destroy()
