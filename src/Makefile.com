#
# This file and its contents are supplied under the terms of the
# Common Development and Distribution License ("CDDL"), version 1.0.
# You may only use this file in accordance with the terms of version
# 1.0 of the CDDL.
#
# A full copy of the text of the CDDL should have accompanied this
# source.  A copy of the CDDL is also available via the Internet at
# http://www.illumos.org/license/CDDL.
#

# Copyright 2022, Richard Lowe.

CC = /usr/gcc/13/bin/gcc
CFLAGS = -m64 -Wall
CPPFLAGS = -D_REENTRANT -D_POSIX_PTHREAD_SEMANTICS

# The version of python used by the scripts, and the 'primary' version in
# packaging, which is transformed into the others
PYTHON_VERSION = 3.9

# The full set of versions for which modules are delivered
PYTHON_VERSIONS = 3.9

PEP8 = /usr/bin/pep8-$(PYTHON_VERSION)
PYTHON = /usr/bin/python$(PYTHON_VERSION)
PYTHON_ROOT= usr/lib/python$(PYTHON_VERSION)
