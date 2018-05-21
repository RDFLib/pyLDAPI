#!/usr/bin/env python
from setuptools import setup
import io

with io.open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='pyldapi',
    packages=['pyldapi'],
    version='1.0.0',
    description='A very small module to add Linked Data API functionality to a Python Flask installation',
    author='Nicholas Car',
    author_email='nicholas.car@csiro.au',
    url='https://github.com/CSIRO-enviro-informatics/pyldapi',
    download_url='https://github.com/CSIRO-enviro-informatics/pyldapi/archive/v1.0.0.tar.gz',
    license='LICENSE.txt',
    keywords=['Linked Data', 'Semantic Web', 'Flask', 'Python', 'API', 'RDF'],
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/CSIRO-enviro-informatics/pyldapi/issues',
        'Source': 'https://github.com/CSIRO-enviro-informatics/pyldapi/',
    },
    install_requires=[
        'flask',
        'requests',
        'rdflib',
        'rdflib-jsonld'
    ],
)

 # use http://peterdowns.com/posts/first-time-with-pypi.html