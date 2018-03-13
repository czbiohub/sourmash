from __future__ import print_function
import os
from setuptools import setup, find_packages
import sys


DEBUG_BUILD = os.environ.get("SOURMASH_DEBUG") == '1'

def build_native(spec):
    cmd = ['cargo', 'build']

    target = 'debug'
    if not DEBUG_BUILD:
        cmd.append('--release')
        target = 'release'

    build = spec.add_external_build(
        cmd=cmd,
        path='./rust'
    )

    rtld_flags = ['NOW']
    if sys.platform == 'darwin':
        rtld_flags.append('NODELETE')
    spec.add_cffi_module(
        module_path='sourmash._lowlevel',
        dylib=lambda: build.find_dylib('sourmash', in_path='target/%s' % target),
        header_filename=lambda: build.find_header('sourmash.h', in_path='target'),
        rtld_flags=rtld_flags
    )

# retrieve VERSION from sourmash/VERSION.
thisdir = os.path.dirname(__file__)
version_file = open(os.path.join(thisdir, 'sourmash', 'VERSION'))
VERSION = version_file.read().strip()

CLASSIFIERS = [
    "Environment :: Console",
    "Environment :: MacOS X",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Natural Language :: English",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS :: MacOS X",
    "Programming Language :: Rust",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
]

CLASSIFIERS.append("Development Status :: 5 - Production/Stable")

with open('README.md', 'r') as readme:
    LONG_DESCRIPTION = readme.read()

SETUP_METADATA = \
               {
    "name": "sourmash",
    "version": VERSION,
    "description": "tools for comparing DNA sequences with MinHash sketches",
    "long_description": LONG_DESCRIPTION,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/dib-lab/sourmash",
    "author": "C. Titus Brown",
    "author_email": "titus@idyll.org",
    "license": "BSD 3-clause",
    "packages": find_packages(),
    "zip_safe": False,
    "platforms": "any",
    "entry_points": {'console_scripts': [
        'sourmash = sourmash.__main__:main'
        ]
    },
    "install_requires": ["screed>=0.9", "ijson", "khmer>=2.1", 'milksnake'],
    "setup_requires": ["setuptools>=38.6.0", "milksnake"],
    "extras_require": {
        'test' : ['pytest', 'pytest-cov', 'numpy', 'matplotlib', 'scipy','recommonmark'],
        'demo' : ['jupyter', 'jupyter_client', 'ipython'],
        'doc' : ['sphinx'],
        },
    "include_package_data": True,
    "milksnake_tasks": [build_native],
    "classifiers": CLASSIFIERS
    }

setup(**SETUP_METADATA)

