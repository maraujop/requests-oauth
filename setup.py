#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist
import os
import os.path
import subprocess
import re

version = '0.4.1'

# Required for Python 2.6 backwards compat
def subprocess_check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')

    process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, *popenargs, **kwargs)
    stdout, stderr = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = ' '.join(*popenargs)
        raise Exception("'%s' failed(%d): %s" % (cmd, retcode, stderr))
    return (stdout, stderr, retcode) 

pkg_version = None

try:
    (pkg_version, ignore, ignore) = subprocess_check_output('/usr/bin/git describe | tr - _', shell=True)
    pkg_version = pkg_version.rstrip('\n')
except:
    pass

fatal_error = re.compile('fatal')
if fatal_error.search(pkg_version):
    # If we are not in an active git tree assume we are in a source distribution and get the saved version.txt
    try:
        (pkg_version, ignore, ignore) = subprocess_check_output('cat version.txt', shell=True)
    except:
        print 'WARNING: Cannot get package version from git or in tree - setting to hardcode setup.py version (%s)' % (version)
        pkg_version = version

def modify_specfile():
    cmd = (' sed -e "s/@VERSION@/%s/g" < python-requests-oauth.spec.in ' % pkg_version) + " > python-requests-oauth.spec"
    os.system(cmd)

class sdist(_sdist):
    """ custom sdist command to prepare python-requests-oauth.spec file """
    def run(self):
        modify_specfile()
        _sdist.run(self)

setup(
    name='requests-oauth',
    version=pkg_version,
    description='Hook for adding Open Authentication support to Python-requests HTTP library.',
    long_description=open('README.md').read(),
    author='Miguel Araujo',
    author_email='miguel.araujo.perez@gmail.com',
    url='http://github.com/maraujop/requests-oauth',
    packages=find_packages(),
    install_requires=['requests>=0.12.1', ],
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
    cmdclass = {'sdist': sdist},
)
