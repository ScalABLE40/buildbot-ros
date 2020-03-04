#!/usr/bin/env python
'''
Wrapper around git-buildpackage to deal with the change in the way that it
interprets arguments between the version that ships with ubuntu 12.04 and
the version that ships with Ubuntu 14.04.

In older versions of git-buildpackage, the --git-upstream argument could refer
to either a branch or a tag name (bloom uses tags). In recent versions of
git-buildpackage, --git-upstream can only refer to a branch. To get around this,
this script accepts the old style arguments and modifies them to work with the
version of git-buildpackage on this system.

For more information on this issue, see
https://github.com/mikeferguson/buildbot-ros/issues/33
and
https://github.com/ros-infrastructure/bloom/issues/211
'''
import sys
import re
import os
import subprocess

def _get_package_subfolders(basepath, debian_package_name):
    subfolders = []
    for filename in os.listdir(basepath):
        path = os.path.join(basepath, filename)
        if not os.path.isdir(path):
            continue
        if filename.startswith('%s-' % debian_package_name):
            subfolders.append(path)
    return subfolders

rosdistro, package, release_version, workdir = sys.argv[1:5]
gbp_args = sys.argv[5:]

try:
    subfolders = _get_package_subfolders(workdir, package)
    assert len(subfolders) == 1, subfolders
    sources_dir = subfolders[0]
except:
    sources_dir=workdir+'/build'
    print(sources_dir)

cmd = ['gbp', 'buildpackage',
    '--git-ignore-new',
    '--git-ignore-branch',
    # dpkg-buildpackage args
    '-S']
cmd += [
    # dpkg-buildpackage args
    '-us', '-uc']
    # debuild args for lintian
    #'--lintian-opts', '--suppress-tags', 'newer-standards-version']

cmd += ['--git-upstream-tree=TAG',
        '--git-upstream-tag=release/{rosdistro}/{package}/{release_version}'.format(
            rosdistro=rosdistro, package=package, release_version=release_version)] + gbp_args

# workaround different default compression levels
# resulting in different checksums for the tarball
env = dict(os.environ)
env['GZIP'] = '-9'

print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
subprocess.check_call(cmd, cwd=sources_dir, env=env)
