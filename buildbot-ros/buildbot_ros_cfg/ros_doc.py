from buildbot.config import BuilderConfig
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Interpolate
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import DirectoryUpload, FileDownload
from buildbot.steps.trigger import Trigger
from buildbot.schedulers import triggerable

from .helpers import success

## @brief Docbuild jobs build the source documentation. This isn't the whold documentation
##        that is on the wiki, like message docs, just the source documentation part.
## @param c The Buildmasterconfig
## @param job_name Name for this job (typically the repository/metapackage name)
## @param url URL of the SOURCE repository.
## @param branch Branch to checkout.
## @param distro Ubuntu distro to build for (for instance, 'precise')
## @param arch Architecture to build for (for instance, 'amd64')
## @param rosdistro ROS distro (for instance, 'groovy')
## @param machines List of machines this can build on.
## @param othermirror Cowbuilder othermirror parameter
## @param keys List of keys that cowbuilder will need
## @param trigger_pkgs List of packages names to trigger after our build is done.
def ros_docbuild(c, job_name, url, branch, rosdistro, machines, trigger_pkgs = None):

    # Directory which will be bind-mounted
    binddir = job_name+'_'+rosdistro+'_docbuild'

    f = BuildFactory()
    # Remove any old crud in /tmp folder
    f.addStep(
        ShellCommand(
            command = ['rm', '-rf', binddir],
            hideStepIf = success
        )
    )
    # Check out repository (to /tmp)
    f.addStep(
        Git(
            repourl = url,
            branch = branch,
            alwaysUseLatest = True,
            mode = 'full'
            #workdir = binddir+'/src/'+job_name+'/'
        )
    )
    # Download  script from master
    f.addStep(
        FileDownload(
            name = job_name+'-grab-script',
            mastersrc = 'scripts/docbuild.py',
            workerdest = Interpolate('%(prop:builddir)s/docbuild.py'),
            hideStepIf = success
        )
    )

    f.addStep(
        FileDownload(
            name = job_name+'-grab-script',
            mastersrc = 'scripts/unique_docker_doc.py',
            workerdest = Interpolate('%(prop:builddir)s/unique_docker_doc.py'),
            hideStepIf = success
        )
    )

    f.addStep(
        FileDownload(
            name = job_name+'-grab-script',
            mastersrc = 'docker_components/Dockerfile_doc',
            workerdest = Interpolate('%(prop:builddir)s/Dockerfile_doc'),
            hideStepIf = success
        )
    )

    f.addStep(
        FileDownload(
            name = job_name+'-grab-script',
            mastersrc = 'docker_components/docker-compose-doc.yaml',
            workerdest = Interpolate('%(prop:builddir)s/docker-compose-doc.yaml'),
            hideStepIf = success
        )
    )
    # reedit docker-compose-doc.yaml
    f.addStep(
        ShellCommand(
            haltOnFailure=True,
            name=job_name + '-reedit-docker-compose',
            command=['python', 'unique_docker_doc.py', Interpolate('%(prop:builddir)s/docker-compose-doc.yaml'),
                     Interpolate(job_name)],
            workdir=Interpolate('%(prop:builddir)s'),
            descriptionDone=['reedit docker-compose', job_name]
        )
    )
    # Build docker image for creating doc
    f.addStep(
        ShellCommand(
            # haltOnFailure = True,
            name=job_name + '-create_docker',
            command=['docker-compose', '-f', Interpolate('%(prop:builddir)s/docker-compose-doc.yaml'),
                     'build'],
            workdir=Interpolate('%(prop:builddir)s'),
            descriptionDone=['create_doc', job_name]
        )
    )

    # creating doc in docker
    f.addStep(
        ShellCommand(
            # haltOnFailure=True,
            name=job_name + '-create_doc',
            command=['docker', 'run',
                    # '-v', 'ros-repository-docker_deb_repository:/home/package',
                     '--name', Interpolate('doc_'+job_name),
                     Interpolate('scalable-doc:' + job_name),
                     'python', '/root/docbuild.py', '/tmp/', rosdistro],
            descriptionDone=['create doc', job_name]
        )
    )

    f.addStep(
        ShellCommand(
            name=job_name+'-copydocs',
            command=['docker', 'cp', Interpolate('doc_'+job_name + ':' + '/tmp/docs'),
                     '/docs'],
            workdir=Interpolate('%(prop:builddir)s'),
            descriptionDone=['copydocs', job_name]
        )
    )

        # rm container
    f.addStep(
        ShellCommand(
            name=job_name + '-rm_container',
            command=['docker', 'rm',  Interpolate('doc_'+job_name)],
            descriptionDone=['remove docker container', job_name]
        )
    )

        # rm image
    f.addStep(
        ShellCommand(
            name=job_name + '-rm_image',
            command=['docker', 'image', 'rm',  Interpolate('scalable-doc:'+job_name)],
            descriptionDone=['remove docker image', job_name]
        )
    )    

    # Trigger if needed
    if trigger_pkgs != None:
        f.addStep(
            Trigger(
                schedulerNames = [t.replace('_','-')+'-'+rosdistro+'-doctrigger' for t in trigger_pkgs],
                waitForFinish = False,
                alwaysRun=True
            )
        )
    # Create trigger
    c['schedulers'].append(
        triggerable.Triggerable(
            name = job_name.replace('_','-')+'-'+rosdistro+'-doctrigger',
            builderNames = [job_name+'_'+rosdistro+'_docbuild',]
        )
    )
    # Add builder config
    c['builders'].append(
        BuilderConfig(
            name = job_name+'_'+rosdistro+'_docbuild',
            workernames = machines,
            factory = f
        )
    )
    # return the name of the job created
    return job_name+'_'+rosdistro+'_docbuild'
