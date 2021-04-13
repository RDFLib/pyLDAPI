#!/usr/bin/env python
# -*- coding: latin-1 -*-
import codecs
import re
import os
import sys
import pathlib
from setuptools import setup
from setuptools.command.install import install
import pkg_resources
import setuptools

# Default value
if sys.argv[1] != 'install':
    packages = None
    install_requires = None
    version = '3.12'


class InstallCommand(install):
    user_options = install.user_options + [
        ('framework=', None, 'Available frameworks: flask or fastapi'),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.framework = None

    def finalize_options(self):
        framework = self.framework
        assert self.framework in ('flask', 'fastapi'), 'Framework not found'
        install.finalize_options(self)

    def run(self):
        install.run(self)


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return codecs.open(path, mode, encoding)


with open_local(['README.rst']) as readme:
    long_description = readme.read()

with open('requirements_flask.txt') as f:
    install_requires = f.read().splitlines()

if sys.argv[1] != 'install':
    for i, arg in enumerate(sys.argv):
        print("heeeeee")
        print("arg", arg)
        if "--framework" in arg:
            package_framework = sys.argv[i].split('=')[-1]
            if package_framework == 'flask':
                packages = ['pyldapi_flask']

                # with pathlib.Path('requirements_flask.txt').open() as requirements_txt:
                #     install_requires = [
                #         str(requirement)
                #         for requirement
                #         in pkg_resources.parse_requirements(requirements_txt)
                #     ]
                with open('requirements_flask.txt') as f:
                    install_requires = f.read().splitlines()
                print("UNSTA", install_requires)
            elif package_framework == 'fastapi':
                packages = ['pyldapi_fastapi']

                with open('requirements_fastapi.txt') as f:
                    install_requires = f.read().splitlines()
                # with open_local(['requirements_fastapi.txt']) as req:
                #     install_requires = req.read().split("\n")
                # with pathlib.Path('requirements_fastapi.txt').open() as requirements_txt:
                #     install_requires = [
                #         str(requirement)
                #         for requirement
                #         in pkg_resources.parse_requirements(requirements_txt)
                #     ]
            else:
                raise ValueError('Framework not found - Frameworks available: flask - fastapi')

            with open_local([packages[0], '__init__.py'], encoding='latin1') as fp:
                try:
                    version = re.findall(r"^__version__ = '([^']+)'\r?$",
                                         fp.read(), re.M)[0]
                except IndexError:
                    raise RuntimeError('Unable to determine version.')
            break

# print("PCK", packages)
setup(
    name='pyldapi',
    packages=packages,
    version=version,
    cmdclass={'install': InstallCommand},
    description='A very small module to add Linked Data API functionality to '
                'a Python Flask installation',
    author='Nicholas Car',
    author_email='nicholas.car@surroundaustralia.com',
    url='https://github.com/RDFLib/pyLDAPI',
    download_url='https://github.com/RDFLib/pyLDAPI'
                 '/archive/v{:s}.tar.gz'.format(version),
    license='LICENSE.txt',
    keywords=['Linked Data', 'Semantic Web', 'Flask', 'Python', 'API', 'RDF'],
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'License :: OSI Approved :: '
            'GNU General Public License v3 or later (GPLv3+)',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/RDFLib/pyLDAPI/issues',
        'Source': 'https://github.com/RDFLib/pyLDAPI/',
    },
    install_requires=install_requires,
)
