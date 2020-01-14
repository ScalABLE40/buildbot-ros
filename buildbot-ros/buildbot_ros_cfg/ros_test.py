from buildbot.config import BuilderConfig
from buildbot.changes.gitpoller import GitPoller
from buildbot.plugins import util, schedulers
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate
from buildbot.process import results
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import FileDownload

from buildbot_ros_cfg.helpers import success
from buildbot_ros_cfg.git_pr_poller import GitPRPoller

## @brief Testbuild jobs are used for CI testing of the source repo.
## @param c The Buildmasterconfig
## @param job_name Name for this job (typically the metapackage name)
## @param url URL of the SOURCE repository.
## @param branch Branch to checkout.
## @param distro Ubuntu distro to build for (for instance, 'precise')
## @param arch Architecture to build for (for instance, 'amd64')
## @param rosdistro ROS distro (for instance, 'groovy')
## @param machines List of machines this can build on.
## @param othermirror Cowbuilder othermirror parameter
## @param keys List of keys that cowbuilder will need
def ros_testbuild(c, job_name, url, branch, distro, arch, rosdistro, machines, 
                  othermirror, keys, source=True, locks=[]):

    # Create a Job for Source
    
    if source:
        project_name = '_'.join([job_name, rosdistro, 'source_build'])
        c['change_source'].append(
            GitPoller(
                repourl=url,
                name=url,
                branch=branch,
                category=project_name,
                pollAtLaunch=True,
            )
        )
        c['schedulers'].append(
            schedulers.SingleBranchScheduler(
                name=project_name,
                builderNames=[project_name,],
                change_filter=util.ChangeFilter(category=project_name)
            )
        )
        
        c['schedulers'].append(
            schedulers.Nightly(
                name = project_name+'-nightly-master',
                codebases = {url:{'repository':url,'branch':'master'}},
                builderNames = [project_name,],
                hour=3,
                minute=0,
            )
        )
        
        c['schedulers'].append(
            schedulers.Nightly(
                name = project_name+'-nightly-develop',
                codebases = {url:{'repository':url,'branch':'develop'}},
                builderNames = [project_name,],
                hour=5,
                minute=0,
            )
        )
        
        c['schedulers'].append(
            schedulers.ForceScheduler(
                name=project_name+'-force',
                codebases = [util.CodebaseParameter("", 
                        branch=util.ChoiceStringParameter(
                            name="branch",
                            choices=["master", "devel"],
                            default="master"),
                        repository=util.FixedParameter(name="repository", default=url),
                        )],
                builderNames=[project_name,],
            )
        )
    else:
        r_owner, r_name = (url.split(':')[1])[:-4].split('/')
        project_name = '_'.join([job_name, rosdistro, 'pr_build'])
        c['change_source'].append(
            GitPRPoller(
                owner=r_owner,
                repo=r_name,
                category=project_name,
                branches=[branch],
                pollInterval=10*60,
                pollAtLaunch=True,
                token=util.Secret("OathToken"),
                repository_type='ssh'
            )
        )

        c['schedulers'].append(
            schedulers.SingleBranchScheduler(
                name=project_name,
                builderNames=[project_name,],
                change_filter=util.ChangeFilter(category=project_name)
            )
        )
        
    # Directory which will be bind-mounted
    binddir = '/tmp/'+project_name
    dockerworkdir = '/tmp/test/'


    f = BuildFactory()
    # Remove any old crud in build/src folder
    f.addStep(
        ShellCommand(
            name='rm src',
            command=['rm', '-rf', 'build/src'],
            hideStepIf=success,
            workdir=Interpolate('%(prop:builddir)s')
        )
    )
    # Check out repository (to /build/src)
    f.addStep(
        Git(
            repourl=util.Property('repository', default=url),
            branch=util.Property('branch', default=branch),
            alwaysUseLatest=True,
            mode='full',
            workdir=Interpolate('%(prop:builddir)s/build/src')
        )
    )

    # Download testbuild_docker.py script from master
    f.addStep(
        FileDownload(
            name=job_name+'-grab-script',
            mastersrc='scripts/testbuild_docker.py',
            workerdest=('testbuild_docker.py'),
            hideStepIf=success
        )
    )
    # Download Dockerfile_test script from master
    f.addStep(
        FileDownload(
            name=job_name+'-grab-script',
            mastersrc='docker_components/Dockerfile_test',
            workerdest=('Dockerfile_test'),
            hideStepIf=success
        )
    )
    # Download docker-compose.py script from master
    f.addStep(
        FileDownload(
            name=job_name+'-grab-script',
            mastersrc='docker_components/docker-compose-test.yaml',
            workerdest=('docker-compose-test.yaml'),
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name+'-grab-script',
            mastersrc='docker_components/rosdep_private.yaml',
            workerdest=('rosdep_private.yaml'),
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name+'-grab-script',
            mastersrc='scripts/docker-container.py',
            workerdest=('docker-container.py'),
            hideStepIf=success
        )
    )

    # create docker work environment
    f.addStep(
        ShellCommand(
            command=['python','docker-container.py', job_name],
            hideStepIf=success,
            workdir=Interpolate('%(prop:builddir)s/build/')
        )
    )

    # Make and run tests in a docker container
    f.addStep(
        ShellCommand(
            name=job_name+'-build',
            command=['docker', 'run', 
                    '-v',  'ros-buildbot-docker_deb_repository:/home/package',
                    '--name='+project_name,
                    'scalable-env:'+job_name,
                     'python', '/tmp/build/testbuild_docker.py', binddir,
                    rosdistro],
            descriptionDone=['make and test', job_name]
        )
    )

    f.addStep(
        ShellCommand(
            name=job_name+'-copytestresults',
            command=['docker', 'cp', project_name + ':' +binddir + '/testresults',
                     'testresults'],
            logfiles={'tests': 'testresults'},
            descriptionDone=['testresults', job_name]
        )
    )

    f.addStep(
        ShellCommand(
            name=job_name+'-rm_container',
            command=['docker', 'rm', project_name],
            descriptionDone=['remove docker container', job_name]
        )
    )

    f.addStep(
        ShellCommand(
            name=job_name+'-rm_image',
            command=['docker', 'image', 'rm', 'scalable-env:'+job_name],
            descriptionDone=['remove docker image', job_name]
        )
    )

    c['builders'].append(
        BuilderConfig(
            name=project_name,
            workernames=machines,
            factory=f,
            locks=locks
        )
    )
    # return the name of the job created
    return project_name



## @brief ShellCommand w/overloaded evaluateCommand so that tests can be Warn
class c(ShellCommand):
    warnOnWarnings = True

    def evaluateCommand(self, cmd):
        
        if cmd.didFail():
            # build failed
            return results.FAILURE

        l = self.getLog('tests').readlines()
        if len(l) >= 1:
            if l[0].find('Passed') > -1:
                return results.SUCCESS
            else:
                # some tests failed
                return results.WARNINGS
