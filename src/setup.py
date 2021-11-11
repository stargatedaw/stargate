#!/usr/bin/env python3
"""

"""

import json
import os
import platform
import setuptools
import subprocess
import sys

from distutils.core import Extension
from setuptools.command.test import test as TestCommand


NAME = "stargate"
URL = 'https://github.com/stargateaudio/stargate'
DESCRIPTION = (
    "Holistic audio production solution"
)

DIRNAME = os.path.dirname(__file__)

ENV = os.environ
MACHINE = platform.machine()

if 'PLAT_FLAGS' in ENV:
    PLAT_FLAGS = ENV['PLAT_FLAGS'].split()
elif MACHINE == 'x86_64':
    PLAT_FLAGS = [
        '-mfpmath=sse',
        '-mssse3',
        '-mtune=generic',
        '-mstackrealign',
    ]
else:
    PLAT_FLAGS = [
        '-march=native',
        '-mtune=native',
    ]
OPT_FLAGS = ENV['OPT_FLAGS'].split() if 'OPT_FLAGS' in ENV else [
	'-ffast-math',
	'-finline-functions',
#	'-floop-optimize',
	'-flto',
	'-fno-stack-protector',
	'-fprefetch-loop-arrays',
	'-fsingle-precision-constant',
	'-fstrength-reduce',
	'-fno-strict-aliasing',
    #'-funroll-loops',
]
OPT_LVL = ENV['OPT_LVL'].split() if 'OPT_LVL' in ENV else [
    '-O2',
    '-g',
    '-ggdb3',
]
EXTRA_COMPILE_ARGS = OPT_LVL + OPT_FLAGS + PLAT_FLAGS

try:
    CACHE_LINE_SIZE = subprocess.check_output([
        'getconf',
        'LEVEL1_DCACHE_LINESIZE',
    ]).strip(),
except Exception as ex:
    print(ex)
    CACHE_LINE_SIZE = "64"

def create_c_ext():
    def _walk(dirname, ext):
        return [
            os.path.join(path, f)
            for path, dirs, files in os.walk(dirname)
            for f in files
            if f.endswith(ext)
        ]

    include_dirs = [
        "engine/include",
        "vendor/libcds/include",
    ]
    libraries = [
        'fftw3',
        'fftw3f',
        'm',
        'portaudio',
        'portmidi',
        'pthread',
        'sndfile',
    ]
    if platform.uname().system == 'Linux':
        libraries.append('asound')

    define_macros = [
        ("CACHE_LINE_SIZE", CACHE_LINE_SIZE),
        ("SG_DLL", None),
        ("SG_THREAD_LOCAL", "__thread"),
        ("_GNU_SOURCE", None,),
        ("__USE_GNU", None),
    ]
    sources = _walk('engine/src', '.c') + _walk('vendor/libcds/src', '.c')

    return Extension(
        name='stargateengine',
        sources=sources,
        include_dirs=include_dirs,
        libraries=libraries,
        define_macros=define_macros,
        language='c',
        extra_compile_args=EXTRA_COMPILE_ARGS,
    )

C_EXT = create_c_ext()

with open(
    os.path.join(DIRNAME, 'requirements.txt'),
) as f:
    DEPS = [
        x.strip() for x in f.read().split('\n')
        if x.strip() and not x.strip().startswith('#')
    ]


def _version():
    if 'test' in sys.argv:
        # avoid triggering a pytest coverage report bug
        return 'test'
    dirname = os.path.dirname(__file__)
    abspath = os.path.abspath(dirname)
    path = os.path.join(
        abspath,
        'meta.json',
    )
    with open(path) as f:
        return json.load(f)['version']['minor']

VERSION = _version()


def _github_download_url(
    url=URL,
    version=VERSION,
):
    return "{url}/archive/{version}.tar.gz".format(
        url=url,
        version=version
    )


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def run_tests(self):
        #import here, because outside the eggs aren't loaded
        import pytest
        errno = pytest.main()
        sys.exit(errno)


setuptools.setup(
    name=NAME,
    version=VERSION,
    author="stargateaudio",
    author_email="stargateaudio@noreply.github.com",
    license="GPLv3",
    description=DESCRIPTION,
    # Only build the C extension if C_EXT=1 was defined in the env. vars.
    ext_modules=[C_EXT] if ENV.get('C_EXT') == '1' else [],
    long_description=DESCRIPTION,
    url=URL,
    packages=setuptools.find_packages(
        exclude=(
            "scripts",
            "test",
            "test.*",
            "*.test",
            "*.test.*",
        ),
    ),
    include_package_data=True,
    install_requires=DEPS,
    tests_require=[
        'pytest',
        'pytest-cov',
    ],
    extras_require={},
    cmdclass={
        'test': PyTest,
    },
    setup_requires=[
        'pytest-runner',
    ],
    scripts=[
        'scripts/stargate',
    ],
    # PyPI
    download_url=_github_download_url(),
    keywords=[],
)
