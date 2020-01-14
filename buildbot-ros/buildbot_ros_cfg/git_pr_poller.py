#!/usr/bin/env python

# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

# This is the gitpoller adapted for use with pull requests.
# Extraneous code has been removed (e.g. commit-related methods).
# A modification has been added using name to allow for multiple instances.

import re
import ast

from twisted.internet import defer
from twisted.python import log

from buildbot.changes import base
from buildbot.changes import github as github_c
from buildbot.util import bytes2unicode
from buildbot.util import httpclientservice
from buildbot.reporters import github as github_r
from buildbot.process.properties import Properties
from buildbot.process.results import CANCELLED
from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import RETRY
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
#from buildbot.util import unicode2NativeString
from buildbot.util.giturlparse import giturlparse


class GitPRPoller(github_c.GitHubPullrequestPoller):
    """This source will poll a remote git repo for pull requests
    and submit changes for the PR's branches to the change master."""
    secrets = ("sshPrivateKey", "sshHostKey", "OathToken")

    @defer.inlineCallbacks
    def reconfigService(self,
                        owner,
                        repo,
                        branches=None,
                        pollInterval=10 * 60,
                        category=None,
                        baseURL=None,
                        pullrequest_filter=True,
                        token=None,
                        pollAtLaunch=False,
                        magic_link=False,
                        repository_type="https",
                        github_property_whitelist=None,
                        **kwargs):
        yield base.ReconfigurablePollingChangeSource.reconfigService(
            self, name=self.name, **kwargs)

        if baseURL is None:
            baseURL = github_c.HOSTED_BASE_URL
        if baseURL.endswith('/'):
            baseURL = baseURL[:-1]

        http_headers = {'User-Agent': 'Buildbot'}
        self.token = None
        if token is not None:
            self.token = yield self.renderSecrets(token)
            http_headers.update({'Authorization': 'token ' + self.token})

        self._http = yield httpclientservice.HTTPClientService.getService(
            self.master, baseURL, headers=http_headers)

        self.owner = owner
        self.repo = repo
        self.branches = branches
        self.github_property_whitelist = github_property_whitelist
        self.pollInterval = pollInterval
        self.pollAtLaunch = pollAtLaunch
        self.repository_type = github_c.link_urls[repository_type]
        self.magic_link = magic_link

        if github_property_whitelist is None:
            self.github_property_whitelist = []

        if callable(pullrequest_filter):
            self.pullrequest_filter = pullrequest_filter
        else:
            self.pullrequest_filter = (lambda _: pullrequest_filter)

        self.category = category if callable(category) else bytes2unicode(
        category)

class GitHubStatusPushV2(github_r.GitHubStatusPush):


    def getSha(self,repo_user, repo_name, branch):
        return self._http.get(
            '/'.join(['/repos', repo_user, repo_name, 'git', 'refs','heads', branch ]))

    @defer.inlineCallbacks
    def send(self, build):
        props = Properties.fromDict(build['properties'])
        props.master = self.master

        if build['complete']:
            state = {
                SUCCESS: 'success',
                WARNINGS: 'success',
                FAILURE: 'failure',
                SKIPPED: 'success',
                EXCEPTION: 'error',
                RETRY: 'pending',
                CANCELLED: 'error'
            }.get(build['results'], 'error')
            description = yield props.render(self.endDescription)
        elif self.startDescription:
            state = 'pending'
            description = yield props.render(self.startDescription)
        else:
            return

        context = yield props.render(self.context)

        sourcestamps = build['buildset'].get('sourcestamps')

        if not sourcestamps or not sourcestamps[0]:
            return

        project = sourcestamps[0]['project']

        branch = props['branch']
        m = re.search(r"refs/pull/([0-9]*)/merge", branch)
        if m:
            issue = m.group(1)
        else:
            issue = None

        if "/" in project:
            repoOwner, repoName = project.split('/')
        else:
            giturl = giturlparse(sourcestamps[0]['repository'])
            repoOwner = giturl.owner
            repoName = giturl.repo

        if self.verbose:
            log.msg("Updating github status: repoOwner={repoOwner}, repoName={repoName}".format(
                repoOwner=repoOwner, repoName=repoName))

        for sourcestamp in sourcestamps:
            if sourcestamp['revision'] != '':
                sha = sourcestamp['revision']
            else:
                try:
                    repo_user = repoOwner
                    repo_name = repoName
                    branch = sourcestamp['branch']
                    response = yield self.getSha(
                        repo_user=repo_user,
                        repo_name=repo_name,
                        branch=branch
                    )
                    content = yield response.content()
                    info = ast.literal_eval(content)
                    sha = info["object"]["sha"]
                except Exception as e:
                    sha = ''
                    log.err(
                        e,
                        'Failed to get sha for {repoOwner}/{repoName} '
                        'branch "{branch}"'
                        'http {code}, {content}'.format(
                            repoOwner=repoOwner, repoName=repoName,
                            branch=branch, code=response.code, content=content))
            try:
                repo_user = repoOwner
                repo_name = repoName
                sha = sha
                state = state
                target_url = build['url']
                context = context
                issue = issue
                description = description
                response = yield self.createStatus(
                    repo_user=repo_user,
                    repo_name=repo_name,
                    sha=sha,
                    state=state,
                    target_url=target_url,
                    context=context,
                    issue=issue,
                    description=description
                )

                if not self.isStatus2XX(response.code):
                    raise Exception()

                if self.verbose:
                    log.msg(
                        'Updated status with "{state}" for {repoOwner}/{repoName} '
                        'at {sha}, context "{context}", issue {issue}.'.format(
                            state=state, repoOwner=repoOwner, repoName=repoName,
                            sha=sha, issue=issue, context=context))
            except Exception as e:
                content = yield response.content()
                log.err(
                    e,
                    'Failed to update "{state}" for {repoOwner}/{repoName} '
                    'at {sha}, context "{context}", issue {issue}. '
                    'http {code}, {content}'.format(
                        state=state, repoOwner=repoOwner, repoName=repoName,
                        sha=sha, issue=issue, context=context,
                        code=response.code, content=content))