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
# Copyright (c) 2007, 2010, Oracle and/or its affiliates. All rights reserved.
#

MACH:sh = uname -p

INSTALL = /usr/sbin/install

ROOT = ../../proto/root_${MACH}
ROOTETC = $(ROOT)/etc
ROOTETCZONES = $(ROOT)/etc/zones
ROOTETCBRAND = $(ROOT)/etc/brand/ipkg
ROOTUSRLIB = $(ROOT)/usr/lib
ROOTBRAND = $(ROOTUSRLIB)/brand
ROOTBRANDPKG = $(ROOTBRAND)/ipkg
ROOTBRANDNLIPKG = $(ROOTBRAND)/nlipkg
KVMBRANDPKG = $(ROOTBRAND)/kvm
BHYVEBRANDPKG = $(ROOTBRAND)/bhyve

LINKBRANDPKG = /usr/lib/brand/ipkg

ROOTDIRS = \
	$(ROOT) \
	$(ROOTETC) \
	$(ROOTETCBRAND) \
	$(ROOTETCZONES) \
	$(ROOTUSRLIB) \
	$(ROOTBRAND) \
	$(ROOTBRANDPKG) \
	$(ROOTBRANDNLIPKG) \
	$(KVMBRANDPKG) \
	$(BHYVEBRANDPKG)

ROOTFILES = \
	$(ROOTETCBRAND)/pkgrm.conf \
	$(ROOTETCBRAND)/smf_disable.conf \
	$(ROOTETCZONES)/OInlipkg.xml \
	$(ROOTETCZONES)/SUNWipkg.xml \
	$(ROOTBRANDPKG)/attach \
	$(ROOTBRANDPKG)/clone \
	$(ROOTBRANDPKG)/common.ksh \
	$(ROOTBRANDPKG)/detach \
	$(ROOTBRANDPKG)/fmri_compare \
	$(ROOTBRANDPKG)/image_install \
	$(ROOTBRANDPKG)/p2v \
	$(ROOTBRANDPKG)/pkgcreatezone \
	$(ROOTBRANDPKG)/pkgrm.lst \
	$(ROOTBRANDPKG)/poststate \
	$(ROOTBRANDPKG)/prestate \
	$(ROOTBRANDPKG)/smf_disable.lst \
	$(ROOTBRANDPKG)/support \
	$(ROOTBRANDPKG)/system-unconfigure \
	$(ROOTBRANDPKG)/uninstall \
	$(ROOTBRANDNLIPKG)/config.xml \
	$(KVMBRANDPKG)/config.xml \
	$(KVMBRANDPKG)/platform.xml \
	$(KVMBRANDPKG)/init \
	$(KVMBRANDPKG)/socat \
	$(KVMBRANDPKG)/support \
	$(KVMBRANDPKG)/createzone \
	$(BHYVEBRANDPKG)/createzone \
	$(BHYVEBRANDPKG)/config.xml \
	$(BHYVEBRANDPKG)/platform.xml \
	$(BHYVEBRANDPKG)/init \
	$(BHYVEBRANDPKG)/socat \
	$(BHYVEBRANDPKG)/support \
	$(BHYVEBRANDPKG)/uninstall \
	$(BHYVEBRANDPKG)/firewall.ksh \
	$(BHYVEBRANDPKG)/util.ksh \
	$(BHYVEBRANDPKG)/log.ksh \
	$(BHYVEBRANDPKG)/image.ksh \
	$(BHYVEBRANDPKG)/vars.ksh

BIN = \
	support \
	fmri_compare

support := LDLIBS = -lzonecfg

all := TARGET = all

support: support.c
	$(LINK.c) -o $@ $@.c $(LDLIBS)

fmri_compare: fmri_compare.py
	cp $@.py $@
	chmod 755 $@

all: fmri_compare

clean:
	rm -f $(BIN)

clobber: clean
	rm -f $(ROOTFILES)
	rm -fr $(ROOTBRAND)

install: $(ROOTFILES)


$(ROOT) $(ROOTETC) $(ROOTETCBRAND) $(ROOTETCZONES) $(ROOTUSRLIB) \
	$(ROOTBRAND) $(ROOTBRANDPKG) $(ROOTBRANDNLIPKG) $(KVMBRANDPKG) $(BHYVEBRANDPKG):
	mkdir -p $@

$(ROOTBRANDNLIPKG)/config.xml: $(ROOTBRANDNLIPKG) config.xml
	rm -f $@; $(INSTALL) -f $(ROOTBRANDNLIPKG) -m 0444 config.xml


$(ROOTETCBRAND)/%: $(ROOTETCBRAND) %
	rm -f $@; $(INSTALL) -f $(ROOTETCBRAND) -m 0644 $<

$(ROOTETCZONES)/%: $(ROOTETCZONES) %
	rm -f $@; $(INSTALL) -f $(ROOTETCZONES) -m 0444 $<

$(ROOTBRANDPKG)/%: $(ROOTBRANDPKG) %
	rm -f $@; $(INSTALL) -f $(ROOTBRANDPKG) -m 0444 $<

$(KVMBRANDPKG)/%: $(KVMBRANDPKG) kvm/%
	rm -f $@; $(INSTALL) -f $(KVMBRANDPKG) -m 0444 $<

$(BHYVEBRANDPKG)/%: $(BHYVEBRANDPKG) bhyve/%
	rm -f $@; $(INSTALL) -f $(BHYVEBRANDPKG) -m 0444 $<

$(BHYVEBRANDPKG)/createzone: $(BHYVEBRANDPKG)
	rm -f $@; $(INSTALL) -f $(BHYVEBRANDPKG) -m 0444 kvm/createzone

$(BHYVEBRANDPKG)/socat: $(BHYVEBRANDPKG)
	rm -f $@; $(INSTALL) -f $(BHYVEBRANDPKG) -m 0444 kvm/socat
