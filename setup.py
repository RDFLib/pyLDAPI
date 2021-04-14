#!/usr/bin/env python
# -*- coding: latin-1 -*-
import codecs
import os
from setuptools import setup
from pyldapi.config import __version__


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )
    return codecs.open(path, mode, encoding)


with open_local(['README.rst']) as readme:
    long_description = readme.read()

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()


setup(
    name='pyldapi',
    packages=['pyldapi',
              'pyldapi.fastapi_framework',
              'pyldapi.flask_framework'],
    version=__version__,
    description='A very small module to add Linked Data API functionality to '
                'a Python Flask installation',
    author='Nicholas Car',
    author_email='nicholas.car@surroundaustralia.com',
    url='https://github.com/RDFLib/pyLDAPI',
    download_url='https://github.com/RDFLib/pyLDAPI'
                 '/archive/v{:s}.tar.gz'.format(__version__),
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
