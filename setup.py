#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.3.0'

setup(
    name='requests-oauth',
    version=version,
    description='Hook for adding Open Authentication support to Python-requests HTTP library.',
    long_description=open('README.md').read(),
    author='Miguel Araujo',
    author_email='miguel.araujo.perez@gmail.com',
    url='http://github.com/maraujop/requests-oauth',
    packages=find_packages(),
    install_requires=['requests', ],
    license='BSD',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
    keywords=['requests', 'python-requests', 'OAuth', 'open authentication'],
    zip_safe=False,
)
