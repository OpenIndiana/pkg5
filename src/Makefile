#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright (c) 2007, 2019, Oracle and/or its affiliates. All rights reserved.
# Copyright 2016, OmniTI Computer Consulting, Inc. All rights reserved.
# Copyright 2020 OmniOS Community Edition (OmniOSce) Association.
#

include Makefile.com

PYTESTS = $(PYTHON_VERSIONS:%=runtest/%)

all := TARGET = all
build := TARGET = build
install := TARGET = install
clean := TARGET = clean
clobber := TARGET = clobber
packages := TARGET = install
test := TARGET = test

JOBS = 8

SUBDIRS=brand zoneproxy util/mkcert

all: $(SUBDIRS) .WAIT build

build: $(PYTHON_VERSIONS)

install: $(SUBDIRS) .WAIT $(PYTHON_VERSIONS)

clean: $(SUBDIRS) $(PYTHON_VERSIONS)
	@cd pkg; pwd; make clean

clobber: $(SUBDIRS) $(PYVERSONS)
	@cd pkg; pwd; make clobber

packages: install
	@cd pkg; pwd; $(MAKE) $(TARGET) check \
		PATH=$$(hg root 2>/dev/null || git rev-parse --show-toplevel)/proto/root_$$(uname -p)/usr/bin:$$PATH \
		PYTHONPATH=$$(hg root 2>/dev/null || git rev-parse --show-toplevel)/proto/root_$$(uname -p)/usr/lib/python3.9/vendor-packages

test: install .WAIT $(PYTESTS)

$(SUBDIRS): FRC
	@cd $@; pwd; $(MAKE) $(TARGET) CC=$(CC)

$(PYTHON_VERSIONS): FRC
	CC=$(CC) python$@ setup.py $(TARGET)

$(PYTESTS): FRC
	-pfexec python$(@F) tests/run.py -j $(JOBS)
	-pfexec cp tests/failures.3 tests/failures.3.$(@F)

FRC:

.NO_PARALLEL: $(PYTHON_VERSIONS) $(PYTESTS)

