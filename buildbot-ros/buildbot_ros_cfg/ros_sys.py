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


def ros_sysbuild(c, job_name, rosdistro, machines,
                source=True, locks=[]):

    # Create a Job for system test job_name = sys_name
    project_name = '_'.join([job_name, rosdistro, 'system_build'])
    c['schedulers'].append(
        schedulers.SingleBranchScheduler(
            name=project_name,
            builderNames=[project_name, ],
            change_filter=util.ChangeFilter(category=project_name)
        )
    )
    c['schedulers'].append(
        schedulers.Nightly(
            name = project_name+'-nightly-master',
            builderNames = [project_name,],
            hour=4,
            minute=0,
        )
    )


    # Directory which will be bind-mounted
    binddir = '/tmp'
    rosinstall_url = "https://raw.githubusercontent.com/ipa-rwu/scalable_system_setup/master/config/" + job_name + ".rosinstall"

    f = BuildFactory()
    # Remove any old crud in /tmp folder
    f.addStep(
        ShellCommand(
            name='rm src',
            command=['rm', '-rf', 'scalable_ws'],
            hideStepIf=success,
            workdir=Interpolate('%(prop:builddir)s/build/')
        )
    )

    # wstool init src .rosinstall
    f.addStep(
        ShellCommand(
            haltOnFailure=True,
            name='wstool_rosintall',
            command=['wstool', 'init', 'src', rosinstall_url],
            hideStepIf=success,
            workdir=Interpolate('%(prop:builddir)s/build/scalable_ws')
        )
    )

    # Download Dockerfile_sys.py script from master
    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='docker_components/Dockerfile_sys',
            workerdest=('Dockerfile_sys'),
            hideStepIf=success
        )
    )
    # Download docker-compose-sys.py script from master
    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='docker_components/docker-compose-sys.yaml',
            workerdest=('docker-compose-sys.yaml'),
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='docker_components/rosdep_private.yaml',
            workerdest=('rosdep_private.yaml'),
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='scripts/docker-container.py',
            workerdest=('docker-container.py'),
            hideStepIf=success
        )
    )


    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='shell/uplode_docker_image.sh',
            workerdest=('upload_docker_image.sh'),
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='scripts/unique_docker_sys.py',
            workerdest=('unique_docker_sys.py'),
            mode=0o755,
            hideStepIf=success
        )
    )

    f.addStep(
        FileDownload(
            name=job_name + '-grab-script',
            mastersrc='shell/test_sys.sh',
            workerdest=('test_sys.sh'),
            mode=0o755,
            hideStepIf=success
        )
    )

    # reedit docker-compose-deb.yaml
    f.addStep(
        ShellCommand(
            haltOnFailure=True,
            name=job_name + '-reedit-docker-compose',
            command=['python','unique_docker_sys.py', 'docker-compose-sys.yaml',
                     Interpolate(job_name)],            
            workdir=Interpolate('%(prop:builddir)s/build/'),
            descriptionDone=['reedit docker-compose', job_name]
        )
    )

    # Build docker image for creating debian
    f.addStep(
        ShellCommand(
            haltOnFailure = True,
            name = job_name + '-create_docker_image',
            command=['docker-compose', '-f','docker-compose-sys.yaml',
                     'build'],
            workdir=Interpolate('%(prop:builddir)s/build/'),
            descriptionDone=['sourcedeb', job_name]
        )
    )

    # Make and run tests in a docker container
    f.addStep(
        ShellCommand(
            name=job_name + '-test_system',
            command=['docker', 'run', '--name=' + project_name,
                     'scalable-sys:' + job_name,
                     'bash','/usr/local/sbin/test_sys.sh'],
            descriptionDone=['make and test', job_name]
        )
    )  
        
    f.addStep(
        ShellCommand(
            name=job_name + '-upload_docker_image',
            command=['bash', 'upload_docker_image.sh', project_name, binddir, job_name],
            descriptionDone=['upload_docker_image', job_name],
            workdir=Interpolate('%(prop:builddir)s/build/')
        )
    )

    f.addStep(
        ShellCommand(
            name=job_name + '-rm_container',
            command=['docker', 'rm', project_name],
            descriptionDone=['remove docker container', job_name]
        )
    )



    f.addStep(
        ShellCommand(
            name=job_name + '-rm_image',
            command=['docker', 'image', 'rm', 'scalable-sys:' + job_name],
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
