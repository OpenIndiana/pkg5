#!/usr/bin/python
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
# Copyright 2008 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

import sys
import os
import tempfile
import shutil
import tarfile
import unittest
import pkg.pkgtarfile as pkgtarfile

class TestPkgTarFile(unittest.TestCase):

        def setUp(self):
                self.tpath = tempfile.mkdtemp()

                cpath = tempfile.mkdtemp()
                filepath = os.path.join(cpath, "foo/bar")
                filename = "baz"
                create_path = os.path.join(filepath, filename)
                os.makedirs(filepath)
                rfp = file("/dev/urandom", "rb")
                wfp = file(create_path, "wb")
                buf = rfp.read(8192)
                rfp.close()
                wfp.write(buf)
                wfp.close()

                self.tarfile = os.path.join(self.tpath, "test.tar")

                tarfp = tarfile.open(self.tarfile, 'w')
                tarfp.add(create_path, "foo/bar/baz")
                tarfp.close()
                shutil.rmtree(cpath)
                
        def tearDown(self):
                shutil.rmtree(self.tpath)

        def testerrorlevelIsCorrect(self):
                p = pkgtarfile.PkgTarFile(self.tarfile, 'r')
                extractpath = os.path.join(self.tpath, "foo/bar")
                os.makedirs(extractpath)
                os.chmod(extractpath, 0555)
                self.assertRaises(IOError, p.extract, "foo/bar/baz",
                    extractpath)
                p.close()
                os.chmod(extractpath, 777)


if __name__ == "__main__":
        unittest.main()
