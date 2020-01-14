from buildbot.config import BuilderConfig
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.steps.transfer import FileUpload, FileDownload
from buildbot.steps.trigger import Trigger
from buildbot.steps.master import MasterShellCommand
from buildbot.steps.worker import RemoveDirectory
from buildbot.schedulers import triggerable

from .helpers import success

## @brief Debbuilds are used for building sourcedebs & binaries out of gbps and uploading to an APT repository
## @param c The Buildmasterconfig
## @param job_name Name for this job (typically the metapackage name)
## @param packages List of packages to build.
## @param url URL of the BLOOM repository.
## @param distro Ubuntu distro to build for (for instance, 'precise')
## @param arch Architecture to build for (for instance, 'amd64')
## @param rosdistro ROS distro (for instance, 'groovy')
## @param version Release version to build (for instance, '0.8.1-0')
## @param machines List of machines this can build on.
## @param othermirror Cowbuilder othermirror parameter
## @param keys List of keys that cowbuilder will need
## @param trigger_pkgs List of packages names to trigger after our build is done.
def ros_debbuild(c, job_name, packages, url, distro, arch, rosdistro, version, machines, othermirror, keys, trigger_pkgs = None, locks=[]):
    gbp_args = ['-uc', '-us', '--git-ignore-branch', '--git-ignore-new',
                '--git-verbose', '--git-dist='+distro, '--git-arch='+arch]
    f = BuildFactory()
    # Remove the build directory.
    f.addStep(
        RemoveDirectory(
            name = job_name+'-clean',
            dir = Interpolate('%(prop:builddir)s'),
            hideStepIf = success,
        )
    )

    # Check out the repository master branch, since releases are tagged and not branched
    f.addStep(
        Git(
            repourl = url,
            branch = 'master',
            alwaysUseLatest = True, # this avoids broken builds when schedulers send wrong tag/rev
            mode = 'full' # clean out old versions
         )
    )

    # Need to build each package in order
    for package in packages:
        debian_pkg = 'ros-'+rosdistro+'-'+package.replace('_','-')  # debian package name (ros-groovy-foo)
        branch_name = 'debian/'+debian_pkg+'_%(prop:release_version)s_'+distro  # release branch from bloom debian/ros-groovy-foo_0.0.1_kinetic
        deb_name = debian_pkg+'_%(prop:release_version)s'+distro
        final_name = debian_pkg+'_%(prop:release_version)s'+distro+'_'+arch+'.deb'
#        final_name = debian_pkg+'_%(prop:release_version)s-%(prop:datestamp)s'+distro+'_'+arch+'.deb'
        # Check out the proper tag. Use --force to delete changes from previous deb stamping
        f.addStep(
            ShellCommand(
                haltOnFailure = True,
                name = package+'-checkout',
                command = ['git', 'checkout', Interpolate(branch_name), '--force'],
                hideStepIf = success
            )
        )
        # Download script for building the source deb
        f.addStep(
            FileDownload(
                name = job_name+'-grab-docker-compose-debian',
                mastersrc = 'docker_components/docker-compose-deb.yaml',
                workerdest = Interpolate('%(prop:builddir)s/docker-compose-deb.yaml'),
                mode = 0o755,
                hideStepIf = success
            )
        )

        f.addStep(
            FileDownload(
                name = job_name+'-grab-dockerfile-debian',
                mastersrc = 'docker_components/Dockerfile_deb',
                workerdest = Interpolate('%(prop:builddir)s/Dockerfile_deb'),
                mode = 0o755,
                hideStepIf = success
            )
        )

        f.addStep(
            FileDownload(
                name = job_name+'-grab-build-deb-shell',
                mastersrc = 'shell/builddebian.sh',
                workerdest = Interpolate('%(prop:builddir)s/builddebian.sh'),
                mode = 0o755,
                hideStepIf = success
            )
        )

        f.addStep(
            FileDownload(
                name = job_name+'-grab-rosdep-private',
                mastersrc = 'docker_components/rosdep_private.yaml',
                workerdest = Interpolate('%(prop:builddir)s/rosdep_private.yaml'),
                mode = 0o755,
                hideStepIf = success
            )
        )

        f.addStep(
            FileDownload(
                name = job_name+'-grab-rosdep-private',
                mastersrc = 'scripts/unique_docker_deb.py',
                workerdest = Interpolate('%(prop:builddir)s/unique_docker_deb.py'),
                mode = 0o755,
                hideStepIf = success
            )
        )

        # reedit docker-compose-deb.yaml
        f.addStep(
            ShellCommand(
                haltOnFailure = True,
                name = package+'-reedit-docker-compose',
                command= ['python','unique_docker_deb.py', Interpolate('%(prop:builddir)s/docker-compose-deb.yaml'), Interpolate(package)],
                workdir=Interpolate('%(prop:builddir)s'),
                descriptionDone = ['reedit docker-compose', package]
            )
        )

        # Build docker image for creating debian
        f.addStep(
            ShellCommand(
                #haltOnFailure = True,
                name = package+'-buildsource',
                command= ['docker-compose', '-f', Interpolate('%(prop:builddir)s/docker-compose-deb.yaml'),
                          'build'],
                workdir=Interpolate('%(prop:builddir)s'),
                descriptionDone = ['sourcedeb', package]
            )
        )

        # build debian package
        f.addStep(
            ShellCommand(
                #haltOnFailure=True,
                name=job_name + '-build',
                command=['docker', 'run',
                         '-v',  'ros-buildbot-docker_deb_repository:/home/package',
                         '--name', Interpolate(package),
                         Interpolate('scalable-deb:'+package),
                         'bash','/usr/local/sbin/builddeb.sh'],
                descriptionDone=['build debian package', job_name]
            )
        )

        # update to local repository
        f.addStep(
            ShellCommand(
                name=job_name + '-upload',
                command=['docker', 'exec', '-e',  Interpolate('package='+debian_pkg+'*'), 'local-repository',
                         'bash', '/tmp/debian-upload.sh'],
                descriptionDone=['release package', job_name]
            )
        )

        # rm container
        f.addStep(
            ShellCommand(
                name=job_name + '-rm_container',
                command=['docker', 'rm',  Interpolate(package)],
                descriptionDone=['remove docker container', job_name]
            )
        )

        # rm image
        f.addStep(
            ShellCommand(
                name=job_name + '-rm_image',
                command=['docker', 'image', 'rm',  Interpolate('scalable-deb:'+package)],
                descriptionDone=['remove docker image', job_name]
            )
        )

    # Trigger if needed
    if trigger_pkgs != None:
        f.addStep(
            Trigger(
                schedulerNames = [t.replace('_','-')+'-'+rosdistro+'-'+distro+'-'+arch+'-debtrigger' for t in trigger_pkgs],
                waitForFinish = False,
                alwaysRun=True
            )
        )
    # Create trigger
    c['schedulers'].append(
        triggerable.Triggerable(
            name = job_name.replace('_','-')+'-'+rosdistro+'-'+distro+'-'+arch+'-debtrigger',
            builderNames = [job_name+'_'+rosdistro+'_'+distro+'_'+arch+'_debbuild',]
        )
    )
    # Add to builders
    c['builders'].append(
        BuilderConfig(
            name = job_name+'_'+rosdistro+'_'+distro+'_'+arch+'_debbuild',
            properties = {'release_version' : version},
            workernames = machines,
            factory = f,
            locks=locks
        )
    )
    # return name of builder created
    return job_name+'_'+rosdistro+'_'+distro+'_'+arch+'_debbuild'
