from buildbot_ros_cfg.ros_sys import ros_sysbuild
import sys


## @brief Create debbuilders from release file
## @param c The Buildmasterconfig
## @param oracle The rosdistro oracle
## @param distro The distro to configure for ('groovy', 'hydro', etc)
## @param builders list of builders that this job can run on
## @returns A list of debbuilder names created
def sysbuilders_from_rosinatll(c, systemindex, distro, builders, locks):
    #systemindex = get_rosinstall_index('git@github.com:ipa-rwu/scalable_system_setup.git')
    system = systemindex.scalable_system[distro]
    system_pack_https = systemindex.scalable_system[distro]['https'].keys()
    jobs_source = list()
    for name in system_pack_https:
        jobs_source.append(ros_sysbuild(c,
                                    name,
                                    distro,
                                    builders,
                                    True, locks))
    return jobs_source
    #return jobs_source. job_debian

