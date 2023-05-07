#!/usr/bin/python3 -B
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import argparse
import json
import os
import shutil
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Debian package creator script",
    )
    parser.add_argument(
        '-i',
        '--install',
        action='store_true',
        dest='install',
        help="Install the package after creating it",
    )
    parser.add_argument(
        '--plat-flags',
        dest='plat_flags',
        default=None,
        help='Use non-default PLAT_FLAGS to compile',
    )
    return parser.parse_args()

args = parse_args()
if args.install:
    # Warm up sudo
    assert not os.system('sudo echo')

if args.plat_flags is None:
    BUILD_CMD = 'make'
else:
    BUILD_CMD = f"PLAT_FLAGS='{args.plat_flags}' make"

PYTHON_VERSION = "".join(str(x) for x in sys.version_info[:2])

orig_wd = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)

os.chdir(orig_wd)
os.system("scripts/src.sh")

with open("src/meta.json") as f:
    j = json.load(f)
    MAJOR_VERSION = j['version']['major']
    MINOR_VERSION = j['version']['minor']

global_version_fedora = MINOR_VERSION.replace("-", ".")
PACKAGE_NAME = "{}-{}".format(
    MAJOR_VERSION, global_version_fedora)

global_home = os.path.expanduser("~")
rpm_build_path = os.path.join(
    global_home,
    'rpmbuild',
    "BUILD",
    MAJOR_VERSION,
)
os.system(f'rm -rf {rpm_build_path}*')

if not os.path.isdir("{}/rpmbuild".format(global_home)):
    if shutil.which("rpmdev-setuptree"):
        os.system("rpmdev-setuptree")
    else:
        for dirname in (
            'BUILD',
            'BUILDROOT',
            'RPM',
            'SOURCES',
            'SPECS',
        ):
            path = os.path.join(global_home, 'rpmbuild', dirname)
            os.makedirs(path)

SPEC_DIR = "{}/rpmbuild/SPECS/".format(global_home)
SOURCE_DIR = "{}/rpmbuild/SOURCES/".format(global_home)

TARBALL_NAME = "{}.tar.gz".format(PACKAGE_NAME)
TARBALL_URL = ("https://github.com/stargateaudio/stargate/archive"
    "/{}".format(TARBALL_NAME))

os.system('cp "{}" "{}"'.format(TARBALL_NAME, SOURCE_DIR))

global_spec_file = "{}.spec".format(MAJOR_VERSION,)

f_spec_template = \
"""
%global debug_package %{{nil}}

Name:           {0}
Version:        {1}

Release:        1%{{?dist}}
Summary:        Digital audio workstations, instrument and effect plugins

License:        GPLv3
URL:            http://github.com/stargateaudio/stargate/
Source0:        {2}


# Commented out to allow compiling from an old Debian VM, these
# dependencies are still required

#BuildRequires: \
#    alsa-lib-devel \
#    fftw-devel \
#    gcc \
#    gcc-c++ \
#    libsndfile-devel \
#    portaudio-devel \
#    portmidi-devel \
#    python3-devel \

Requires: \
    (alsa-lib or alsa) \
    (fftw3 or libfftw3-3) \
    libsndfile \
    (portaudio or libportaudio2) \
    (portmidi or libportmidi0) \
    python3 \
    (python3-jinja2 or python3-Jinja2) \
    python3-numpy \
    python3-psutil \
    (python3-pyyaml or python3-PyYAML) \
    (python3-pyqt6 or python3-qt6 or python3-qt5 or python3-pyqt5) \
    (rubberband or rubberband-cli) \
    vorbis-tools \

Recommends: \
    ffmpeg \
    lame \
    python3-mutagen \

%global __python %{{__python3}}

%description
Stargate is digital audio workstations (DAWs), instrument and effect plugins

%prep
%setup -q

%build
{3}

%install
rm -rf $RPM_BUILD_ROOT
DESTDIR="$RPM_BUILD_ROOT" make install


%post

update-mime-database %{{_usr}}/share/mime/  || true
xdg-mime default {0}.desktop text/{0}.project || true

%files

%defattr(644, root, root)

%attr(755, root, root) /opt/{0}
%attr(755, root, root) %{{_usr}}/bin/{0}
%{{_usr}}/share/applications/{0}.desktop
%{{_usr}}/share/doc/{0}
%{{_usr}}/share/mime/packages/{0}.xml
%{{_usr}}/share/pixmaps/{0}.ico
%{{_usr}}/share/pixmaps/{0}.png

%doc

""".format(
    MAJOR_VERSION,
    global_version_fedora,
    TARBALL_URL,
    BUILD_CMD,
    PYTHON_VERSION,
)

f_spec_file = open(global_spec_file, "w")
f_spec_file.write(f_spec_template)
f_spec_file.close()

os.system('cp "{}" "{}"'.format(global_spec_file, SPEC_DIR))

if args.install:
    os.system('rm -f {}-*'.format(MAJOR_VERSION))

os.chdir(SPEC_DIR)
f_rpm_result = os.system("rpmbuild -ba {}".format(global_spec_file))

if f_rpm_result:
    print("Error:  rpmbuild returned {}".format(f_rpm_result))
    exit(f_rpm_result)
else:
    pkg_name = "{}-*{}*rpm".format(
        MAJOR_VERSION, MINOR_VERSION)

    cp_cmd = "cp ~/rpmbuild/RPMS/*/{} '{}'".format(pkg_name, orig_wd)
    print(cp_cmd)
    os.system(cp_cmd)

    if args.install:
        os.system("sudo dnf remove -y {0} '{0}-*'".format(MAJOR_VERSION))
        #os.system("sudo rpm -e {0}".format(MAJOR_VERSION))
        #os.system("sudo rpm -e {0}-debuginfo".format(MAJOR_VERSION))
        os.system("sudo dnf install -y {}/{}".format(orig_wd, pkg_name))

