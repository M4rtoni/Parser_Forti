#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import parser_forti

setup(
    name='Parser_Forti',
    version=parser_forti.__version__,
    #packages=find_packages(),
    author='Florian MAUFRAIS',
    author_email='florian.maufrais@nxosecurity.com',
    description='This programme is tool to convert a Fortinet configuration file in JSON, XSLS files',
    long_description=open('README.md').read(),
    include_package_data=True,
    url='https://github.com/M4rtoni/Parser_Forti',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
    ],
    license='BSD 3-clause "New" or "Revised" License'
    )