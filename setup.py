# -*- coding: utf-8 -*-
"""SetupTools configuration for the Ansible Autodoc package."""

from pathlib import Path
from setuptools import setup
from setuptools import find_packages

def get_long_desc():
    """Return the contents of the readme file."""
    with Path('readme.md').open('r', encoding='utf-8') as r_fh:
        ret_value = r_fh.read()
    return ret_value

def get_requires():
    """Return a list of requirements for setuptools."""
    ret_value = [
        'myst-parser',
        'ruamel.yaml',
        'Sphinx>=5.0',
        'sphinx-autobuild',
        'sphinx-book-theme',
        'setuptools',
    ]
    return ret_value

setup(
    name='sphinxcontrib_ansibleautodoc',
    version='0.0.5',
    url='http://github.com/edwardtheharris/sphinxcontrib-ansibleautodoc',
    download_url='http://pypi.python.org/pypi/sphinxcontrib-ansibleautodoc',
    license='BSD',
    author='WAKAYAMA Shirou, Xander Harris',
    author_email='shirou.faw@gmail.com, xandertheharris@gmail.com',
    description='autodoc for ansible playbook',
    long_description=get_long_desc(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=get_requires(),
    namespace_packages=['sphinxcontrib'],
)
