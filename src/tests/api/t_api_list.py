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
# Copyright (c) 2009, 2011, Oracle and/or its affiliates. All rights reserved.
#

import testutils
if __name__ == "__main__":
        testutils.setup_environment("../../../proto")
import pkg5unittest

import calendar
import difflib
import os
import pprint
import re
import shutil
import unittest

import pkg.client.api as api
import pkg.client.api_errors as api_errors
import pkg.client.progress as progress
import pkg.fmri as fmri
import pkg.misc as misc
import pkg.version as version

CLIENT_API_VERSION = 52
PKG_CLIENT_NAME = "pkg"

class TestApiList(pkg5unittest.ManyDepotTestCase):
        # Only start/stop the depot once (instead of for every test)
        persistent_setup = True

        packages = [
            "apple@1,5.11-0",
            "apple@1.0,5.11-0",
            "apple@1.1,5.11-0",
            "apple@1.2.0,5.11-0",
            "apple@1.2.1,5.11-0",
            "apple@1.2.1,5.11-0",
            "apple@1.2.1,5.11-1",
            "bat/bar@1.2,5.11-0",
            "baz@1.0",
            "baz@1.0.1",
            "baz@1.3",
            "corge@0.9",
            "corge@1.0",
            "entire@1.0",
            "grault@1.0",
            "obsolete@1.0",
            "quux@1.0",
            "qux@0.9",
            "qux@1.0",
            "zoo@1.0",
            "zoo@2.0",
        ]

        @staticmethod
        def __tuple_order(a, b):
                apub, astem, aver = a
                bpub, bstem, bver = b
                rval = cmp(astem, bstem)
                if rval != 0:
                        return rval
                rval = cmp(apub, bpub)
                if rval != 0:
                        return rval
                aver = version.Version(aver, "5.11")
                bver = version.Version(bver, "5.11")
                return cmp(aver, bver) * -1

        def __get_pkg_variant(self, stem, ver):
                var = "true"
                opvar = "false"
                if stem == "apple":
                        return [var]
                elif stem in ("entire", "bat/bar", "obsolete"):
                        return
                elif stem in ("corge", "grault", "qux", "quux"):
                        return [var, opvar]
                elif stem == "zoo" and ver.startswith("1.0"):
                        return [var]
                return [opvar]

        @staticmethod
        def __get_pkg_cats(stem, ver):
                if stem == "apple":
                        return [
                            "fruit",
                            "org.opensolaris.category.2008:"
                            "Applications/Sound and Video"
                        ]
                elif stem == "bat/bar":
                        return [
                            "food",
                            "org.opensolaris.category.2008:"
                            "Development/Python"
                        ]
                return []

        @staticmethod
        def __get_pkg_summ_desc(stem, ver):
                summ = "Summ. is %s %s" % (stem, ver)
                desc = "Desc. is %s %s" % (stem, ver)
                return summ, desc

        def __get_pkg_states(self, pub, stem, ver, installed=False):
                states = [api.PackageInfo.KNOWN]
                if installed:
                        states.append(api.PackageInfo.INSTALLED)
                if stem == "apple":
                        # Compare with newest version entry for this stem.
                        if ver != str(self.dlist1[6].version):
                                states.append(api.PackageInfo.UPGRADABLE)
                elif stem == "baz":
                        # Compare with newest version entry for this stem.
                        if ver != str(self.dlist1[10].version):
                                states.append(api.PackageInfo.UPGRADABLE)
                elif stem == "corge":
                        # Compare with newest version entry for this stem.
                        nver = str(self.dlist1[12].version)
                        if ver != nver:
                                states.append(api.PackageInfo.UPGRADABLE)
                        if ver == nver:
                                states.append(api.PackageInfo.RENAMED)
                elif stem == "obsolete":
                        states.append(api.PackageInfo.OBSOLETE)
                elif stem == "qux":
                        # Compare with newest version entry for this stem.
                        nver = str(self.dlist1[18].version)
                        if ver != nver:
                                states.append(api.PackageInfo.UPGRADABLE)
                        if ver == nver:
                                states.append(api.PackageInfo.RENAMED)
                elif stem == "zoo":
                        # Compare with newest version entry for this stem.
                        nver = str(self.dlist1[20].version)
                        if ver != nver:
                                states.append(api.PackageInfo.UPGRADABLE)

                return frozenset(states)

        def __get_pub_entry(self, pub, idx, name, ver):
                if pub == "test1":
                        l = self.dlist1
                else:
                        l = self.dlist2

                f = l[idx]
                self.assertEqual(f.pkg_name, name)
                v = str(f.version)
                try:
                        self.assertTrue(v.startswith(ver + ":"))
                except AssertionError:
                        self.debug("\n%s does not start with %s:" % (v, ver))
                        raise
                return f, v

        def __get_exp_pub_entry(self, pub, idx, name, ver, installed=False):
                f, v = self.__get_pub_entry(pub, idx, name, ver)
                return self.__get_expected_entry(pub, name, v,
                    installed=installed)

        def setUp(self):
                pkg5unittest.ManyDepotTestCase.setUp(self, ["test1", "test2",
                    "test3"])

                pkg_data = ""
                for p in self.packages:
                        pkg_data += p
                        stem, ver = p.split("@")

                        # XXX version should not require 5.11
                        sver = version.Version(ver, "5.11")
                        sver = str(sver).split(":", 1)[0]

                        summ, desc = self.__get_pkg_summ_desc(stem, sver)
                        pkg_data += """
open %(stem)s@%(ver)s
add set name=pkg.summary value="%(summ)s"
add set name=pkg.description value="%(desc)s"
""" % { "stem": stem, "ver": ver, "summ": summ, "desc": desc }

                        cats = self.__get_pkg_cats(stem, sver)
                        if cats:
                                pkg_data += "add set name=info.classification"
                                for cat in cats:
                                        pkg_data += ' value="%s"' % cat
                                pkg_data += "\n"

                        var = self.__get_pkg_variant(stem, sver)
                        if var:
                                adata = "value="
                                adata += " value=".join(var)
                                pkg_data += "add set name=variant.mumble " \
                                    "%s\n" % adata

                        if stem == "corge" and sver.startswith("1.0"):
                                pkg_data += "add set name=pkg.renamed " \
                                    "value=true\n"
                                pkg_data += "add depend type=require " \
                                    "fmri=grault\n"
                        elif stem == "entire":
                                pkg_data += "add depend type=incorporate " \
                                    "fmri=apple@1.2-0\n"
                                pkg_data += "add depend type=incorporate " \
                                    "fmri=qux@1.0\n"
                                pkg_data += "add depend type=incorporate " \
                                    "fmri=quux@1.0\n"
                        elif stem == "obsolete":
                                pkg_data += "add set name=pkg.obsolete " \
                                    "value=true\n"
                        elif stem == "qux" and sver.startswith("1.0"):
                                pkg_data += "add set name=pkg.renamed " \
                                    "value=true\n"
                                pkg_data += "add depend type=require " \
                                    "fmri=quux\n"

                        pkg_data += "close\n"

                rurl1 = self.dcs[1].get_repo_url()
                plist = self.pkgsend_bulk(rurl1, pkg_data)

                # Ensure that the second repo's packages have exactly the same
                # timestamps as those in the first ... by copying the repo over.
                d1dir = self.dcs[1].get_repodir()
                d2dir = self.dcs[2].get_repodir()
                self.copy_repository(d1dir, d2dir, { "test1": "test2" })

                self.dlist1 = []
                self.dlist2 = []
                for e in plist:
                        # Unique FMRI object is needed for each list.
                        f = fmri.PkgFmri(str(e))
                        self.dlist1.append(f)

                        f = fmri.PkgFmri(str(e))
                        f.set_publisher("test2")
                        self.dlist2.append(f)

                self.dlist1.sort()
                self.dlist2.sort()

                # The new repository won't have a catalog, so rebuild it.
                self.dcs[2].get_repo(auto_create=True).rebuild()

                # The third repository should remain empty and not be
                # published to.

                # Next, create the image and configure publishers.
                self.image_create(rurl1, prefix="test1",
                    variants={ "variant.mumble": "true" })
                rurl2 = self.dcs[2].get_repo_url()
                self.pkg("set-publisher -g " + rurl2 + " test2")

        def assertPrettyEqual(self, actual, expected):
                if actual == expected:
                        return

                actual = pprint.pformat(actual, indent=2)
                expected = pprint.pformat(expected, indent=2)

                self.assertEqual(expected, actual,
                    "Actual output differed from expected output.\n" +
                    "\n".join(difflib.unified_diff(
                        expected.splitlines(), actual.splitlines(),
                        "Expected output", "Actual output", lineterm="")))
                raise AssertionError(output)

        def __get_expected_entry(self, pub, stem, ver, installed=False):
                states = self.__get_pkg_states(pub, stem, ver,
                    installed=installed)

                sver = ver.split(":", 1)[0]
                raw_cats = self.__get_pkg_cats(stem, sver)
                summ, desc = self.__get_pkg_summ_desc(stem, sver)

                scheme = None
                cat = None
                pcats = []
                for e in raw_cats:
                        if e and ":" in e:
                                scheme, cat = e.split(":", 1)
                        else:
                                scheme = ""
                                cat = e
                        pcats.append((scheme, cat))
                return ((pub, stem, ver), summ, pcats, states)

        def __get_expected(self, pkg_list, cats=None, pubs=misc.EmptyI,
            variants=False):
                nlist = {}
                newest = pkg_list == api.ImageInterface.LIST_NEWEST
                if newest:
                        # Get the newest FMRI for each unique package stem on
                        # a per-publisher basis.
                        for plist in (self.dlist1, self.dlist2):
                                for f in plist:
                                        pstem = f.get_pkg_stem()
                                        pub, stem, ver = f.tuple()
                                        ver = str(f.version)
                                        sver = ver.split(":", 1)[0]

                                        var = self.__get_pkg_variant(stem, sver)
                                        if pstem not in nlist:
                                                nlist[pstem] = f
                                        elif not variants and var and \
                                            "true" not in var:
                                                continue
                                        elif f.version > nlist[pstem]:
                                                nlist[pstem] = f
                nlist = sorted(nlist.values())

                expected = []
                for plist in (self.dlist1, self.dlist2):
                        for f in plist:
                                pub, stem, ver = f.tuple()
                                ver = str(f.version)
                                if pubs and pub not in pubs:
                                        continue

                                sver = ver.split(":", 1)[0]
                                var = self.__get_pkg_variant(stem, sver)
                                if not variants and var and "true" not in var:
                                        continue

                                if newest and f not in nlist:
                                        continue

                                t, summ, pcats, states = \
                                    self.__get_expected_entry(pub, stem, ver)
                                if cats is not None:
                                        if not cats:
                                                if pcats:
                                                        # Want packages with no
                                                        # category.
                                                        continue
                                        elif not \
                                            [sc for sc in cats if sc in pcats]:
                                                # Doesn't match specified
                                                # categories.
                                                continue

                                expected.append((t, summ, pcats, states))

                def pkg_list_order(a, b):
                        at = a[0]
                        bt = b[0]
                        return self.__tuple_order(at, bt)
                expected.sort(cmp=pkg_list_order)
                return expected

        def __get_returned(self, pkg_list, api_obj=None, cats=None,
            num_expected=None, patterns=misc.EmptyI,
            pubs=misc.EmptyI, variants=False):

                if not api_obj:
                        progresstracker = progress.NullProgressTracker()
                        api_obj = api.ImageInterface(self.get_img_path(),
                            CLIENT_API_VERSION, progresstracker, lambda x: False,
                            PKG_CLIENT_NAME)

                # Set of states exposed by the API.
                exp_states = set([api.PackageInfo.FROZEN,
                    api.PackageInfo.INCORPORATED, api.PackageInfo.EXCLUDES,
                    api.PackageInfo.KNOWN, api.PackageInfo.INSTALLED,
                    api.PackageInfo.UPGRADABLE, api.PackageInfo.OBSOLETE,
                    api.PackageInfo.RENAMED])

                # Get ordered list of all packages.
                returned = []
                for entry in api_obj.get_pkg_list(pkg_list, cats=cats,
                    patterns=patterns, pubs=pubs, variants=variants):
                        (pub, stem, ver), summ, pcats, raw_states = entry

                        sver = ver.split(":", 1)[0]

                        # Eliminate states not exposed by the api.
                        states = raw_states.intersection(exp_states)
                        returned.append(((pub, stem, ver), summ, pcats, states))
                return returned

        def __test_list(self, pkg_list, api_obj=None,
            cats=None, num_expected=None, pubs=misc.EmptyI,
            variants=False):

                # Get package list.
                returned = self.__get_returned(pkg_list, api_obj=api_obj,
                    cats=cats, pubs=pubs, variants=variants)

                # Now generate expected list.
                expected = self.__get_expected(pkg_list, cats=cats,
                    pubs=pubs, variants=variants)

                # Compare returned and expected.
                self.assertPrettyEqual(returned, expected)

                if num_expected is not None:
                        self.assertEqual(len(returned), num_expected)

        def test_list_01_full(self):
                """Verify the sort order and content of a full list and
                combinations thereof."""

                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(), CLIENT_API_VERSION,
                    progresstracker, lambda x: False, PKG_CLIENT_NAME)

                # First check all variants case.
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test1", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 4, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0"),
                    self.__get_exp_pub_entry("test1", 2, "apple", "1.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test1", 0, "apple", "1,5.11-0"),
                    self.__get_exp_pub_entry("test2", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test2", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test2", 4, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test2", 3, "apple",
                        "1.2.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 2, "apple", "1.1,5.11-0"),
                    self.__get_exp_pub_entry("test2", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 0, "apple", "1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test1", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test1", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test2", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test2", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 11, "corge", "0.9,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 11, "corge", "0.9,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11"),
                    self.__get_exp_pub_entry("test2", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 17, "qux", "0.9,5.11"),
                    self.__get_exp_pub_entry("test1", 20, "zoo", "2.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 20, "zoo", "2.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 42)

                # Next, check no variants case (which has to be done
                # programatically).
                self.__test_list(api.ImageInterface.LIST_ALL, api_obj=api_obj,
                    num_expected=34, variants=False)

        def test_list_02_newest(self):
                """Verify the sort order and content of a list excluding
                packages not for the current image variant, and all but
                the newest versions of each package for each publisher."""

                self.__test_list(api.ImageInterface.LIST_NEWEST,
                    num_expected=18, variants=False)

                # Verify that LIST_NEWEST will allow version-specific
                # patterns such that the newest version allowed by the
                # pattern is what is listed.
                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(),
                    CLIENT_API_VERSION, progresstracker, lambda x: False,
                    PKG_CLIENT_NAME)

                returned = self.__get_returned(api_obj.LIST_NEWEST,
                    api_obj=api_obj, patterns=["baz@1.0", "bat/bar",
                        "corge@1.0"], variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test2", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 6)

        def test_list_03_cats(self):
                """Verify the sort order and content of a list excluding
                packages not for the current image variant, and packages
                that don't match the specified scheme, category
                combinations."""

                combos = [
                    ([
                        ("", "fruit"),
                        ("org.opensolaris.category.2008",
                        "Applications/Sound and Video"),
                        ("", "food"),
                        ("org.opensolaris.category.2008",
                        "Development/Python")
                    ], 16),
                    ([
                        ("org.opensolaris.category.2008",
                        "Development/Python")
                    ], 2),
                    ([
                        ("org.opensolaris.category.2008",
                        "Applications/Sound and Video"),
                        ("", "food")
                    ], 16),
                    ([
                        ("", "fruit")
                    ], 14),
                    ([
                        ("", "food")
                    ], 2),
                    ([], 18) # Only packages with no category assigned.
                ]

                for combo, expected in combos:
                        self.__test_list(api.ImageInterface.LIST_ALL,
                            cats=combo, num_expected=expected, variants=False)

        def test_list_04_pubs(self):
                """Verify the sort order and content of list filtered using
                various publisher and variant combinations."""

                combos = [
                    (["test1", "test2"], 34, False),
                    (["test1", "test2"], 42, True),
                    (["test2"], 17, False),
                    (["test2"], 21, True),
                    (["test1"], 17, False),
                    (["test1"], 21, True),
                    (["test3"], 0, False),
                    (["test3"], 0, True),
                    ([], 34, False),
                    ([], 42, True)
                ]

                for combo, expected, variants in combos:
                        self.__test_list(api.ImageInterface.LIST_ALL,
                            num_expected=expected, pubs=combo,
                            variants=variants)

        def test_list_05_installed(self):
                """Verify the sort order and content of a list containing
                only installed packages and combinations thereof."""

                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(), CLIENT_API_VERSION,
                    progresstracker, lambda x: False, PKG_CLIENT_NAME)

                # Verify no installed packages case.
                returned = self.__get_returned(api_obj.LIST_INSTALLED,
                    api_obj=api_obj)
                self.assertEqual(len(returned), 0)

                # Test results after installing packages and only listing the
                # installed packages.  Note that the 'obsolete' and renamed packages
                # won't be installed.
                af = self.__get_pub_entry("test1", 3, "apple",
                    "1.2.0,5.11-0")[0]
                api_obj.plan_install(["entire", af.get_fmri(), "corge",
                    "obsolete", "qux"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                # Verify the results for LIST_INSTALLED.
                returned = self.__get_returned(api_obj.LIST_INSTALLED,
                    api_obj=api_obj)
                self.assertEqual(len(returned), 4)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11",
                        installed=True)
                ]
                self.assertPrettyEqual(returned, expected)

                # Verify the results for LIST_INSTALLED_NEWEST.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11",
                        installed=False),
                ]

                self.assertEqual(len(returned), 12)
                self.assertPrettyEqual(returned, expected)

                # Re-test, including variants.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test2", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 20, "zoo", "2.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 20, "zoo", "2.0,5.11",
                        installed=False),
                ]
                self.assertPrettyEqual(returned, expected)

                # Verify results of LIST_INSTALLED_NEWEST when not including
                # the publisher of installed packages.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, pubs=["test2"])

                expected = [
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 12, "corge",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo",
                        "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 19, "zoo",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo",
                        "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Verify the results for LIST_INSTALLED_NEWEST after
                # uninstalling 'quux' and 'qux'.
                api_obj.plan_uninstall(["quux"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11",
                        installed=False),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Verify the results for LIST_INSTALLED_NEWEST after
                # all packages have been uninstalled.
                api_obj.plan_uninstall(["*"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test2", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, including variants.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test2", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test2", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 18, "qux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 20, "zoo", "2.0,5.11"),
                    self.__get_exp_pub_entry("test2", 20, "zoo", "2.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, including only a specific package version, which
                # should show the requested versions even though newer
                # versions are available.  'baz' should be omitted because
                # it doesn't apply to the current image variants; so should
                # zoo@2.0.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, patterns=["apple@1.0,5.11.0", "baz",
                        "qux@0.9", "zoo@2.0"])

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11"),
                    self.__get_exp_pub_entry("test2", 17, "qux", "0.9,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, including only a specific package version, which
                # should show the requested versions even though newer
                # versions are available, and all variants.  'baz' should be
                # included this time; as should zoo@2.0.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, patterns=["apple@1.0,5.11.0", "baz",
                        "qux@0.9", "zoo@2.0"], variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 1, "apple", "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test1", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test2", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11"),
                    self.__get_exp_pub_entry("test2", 17, "qux", "0.9,5.11"),
                    self.__get_exp_pub_entry("test1", 20, "zoo", "2.0,5.11"),
                    self.__get_exp_pub_entry("test2", 20, "zoo", "2.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Test results after installing packages and only listing the
                # installed packages.
                af = self.__get_pub_entry("test1", 1, "apple", "1.0,5.11-0")[0]
                api_obj.plan_install([af.get_fmri(), "qux@0.9", "corge@0.9"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                # Verify the results for LIST_INSTALLED and
                # LIST_INSTALLED_NEWEST when future versions
                # are renamed and current versions are not
                # incorporated.
                returned = self.__get_returned(api_obj.LIST_INSTALLED,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 11, "corge", "0.9,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11",
                        installed=True),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 3)

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 11, "corge", "0.9,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test last but specify patterns for versions newer than
                # what is installed; nothing should be returned as
                # LIST_INSTALLED_NEWEST is supposed to omit versions newer
                # than what is installed, allowed by installed incorporations,
                # or doesn't apply to image variants.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, patterns=["apple@1.2.1,5.11-1",
                        "corge@1.0", "qux@1.0"])
                expected = []
                self.assertPrettyEqual(returned, expected)

                # Remove corge, install grault, retest for
                # LIST_INSTALLED_NEWEST.  corge, grault, qux, and
                # quux should be listed since none of them are
                # listed in an installed incorporation.
                api_obj.plan_uninstall(["corge"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                af = self.__get_pub_entry("test1", 1, "apple", "1.0,5.11-0")[0]
                api_obj.plan_install(["pkg://test2/grault"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple", "1.0,5.11-0",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 13, "entire", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Now verify that publisher search order determines the entries
                # that are listed when those entries are part of an installed
                # incorporation.
                api_obj.plan_uninstall(["*"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                api_obj.plan_install(["entire"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                # In this case, any packages present in an installed
                # incorporation and that are not installed should be
                # listed using the highest ranked publisher (test1).
                # Only apple and quux are incorporated, and build
                # 0 of apple should be listed here instead of build 1
                # since the installed incorporation doesn't allow the
                # build 1 version.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test1", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, specifying versions older than the newest, with
                # some older than that allowed by the incorporation (should
                # be omitted) and with versions allowed by the incorporation
                # (should be returned).
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, patterns=["apple@1.2.0,5.11-0", "qux@0.9"])

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, specifying versions newer than that allowed by the
                # incorporation.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, patterns=["apple@1.2.1,5.11-1"])
                self.assertEqual(len(returned), 0)

                # Re-test, only including test1's packages.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, pubs=["test1"])

                expected = [
                    self.__get_exp_pub_entry("test1", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Re-test, only including test2's packages.  Since none of
                # the other packages are installed for test1, and they meet
                # the requirements of the installed incorporations, this is
                # the expected result.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj, pubs=["test2"])

                expected = [
                    self.__get_exp_pub_entry("test2", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Change test2 to be ranked higher than test1.
                api_obj.set_pub_search_before("test2", "test1")

                # Re-test; test2 should now have its entries listed in place
                # of test1's for the non-filtered case.
                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test2", 5, "apple",
                        "1.2.1,5.11-0"),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Now install one of the incorporated packages and check
                # that test2 is still listed for the remaining package
                # for the non-filtered case.
                api_obj.plan_install(["apple"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test2", 5, "apple",
                        "1.2.1,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Reset publisher search order and re-test.
                api_obj.set_pub_search_before("test1", "test2")

                returned = self.__get_returned(api_obj.LIST_INSTALLED_NEWEST,
                    api_obj=api_obj)

                expected = [
                    self.__get_exp_pub_entry("test2", 5, "apple",
                        "1.2.1,5.11-0", installed=True),
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 12, "corge", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 13, "entire", "1.0,5.11",
                        installed=True),
                    self.__get_exp_pub_entry("test1", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 14, "grault", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 16, "quux", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 19, "zoo", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 19, "zoo", "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)

                # Reset image state for following tests.
                api_obj.plan_uninstall(["*"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

        def test_list_06_upgradable(self):
                """Verify the sort order and content of a list containing
                only upgradable packages and combinations thereof."""

                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(), CLIENT_API_VERSION,
                    progresstracker, lambda x: False, PKG_CLIENT_NAME)

                # Verify no installed packages case.
                returned = self.__get_returned(api_obj.LIST_UPGRADABLE,
                    api_obj=api_obj)
                self.assertEqual(len(returned), 0)

                # Test results after installing packages and only listing the
                # installed, upgradable packages.
                af = self.__get_pub_entry("test1", 3, "apple",
                    "1.2.0,5.11-0")[0]
                api_obj.plan_install([af.get_fmri(), "bat/bar", "qux"])
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

                # Verify the results for LIST_UPGRADABLE.
                returned = self.__get_returned(api_obj.LIST_UPGRADABLE,
                    api_obj=api_obj)
                self.assertEqual(len(returned), 1)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0", installed=True),
                ]
                self.assertPrettyEqual(returned, expected)

                # Reset image state for following tests.
                api_obj.plan_uninstall(["*"], False)
                api_obj.prepare()
                api_obj.execute_plan()
                api_obj.reset()

        def test_list_07_get_pkg_categories(self):
                """Verify that get_pkg_categories returns expected results."""

                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(), CLIENT_API_VERSION,
                    progresstracker, lambda x: False, PKG_CLIENT_NAME)

                # Verify no installed packages case.
                returned = api_obj.get_pkg_categories(installed=True)
                self.assertEqual(len(returned), 0)

                def get_pkg_cats(p):
                        stem, ver = p.split("@")

                        # XXX version should not require 5.11
                        sver = version.Version(ver, "5.11")
                        sver = str(sver).split(":", 1)[0]
                        raw_cats = self.__get_pkg_cats(stem, sver)

                        pcats = []
                        for e in raw_cats:
                                if e and ":" in e:
                                        scheme, cat = e.split(":", 1)
                                else:
                                        scheme = ""
                                        cat = e
                                pcats.append((scheme, cat))
                        return pcats

                # Verify all case.
                returned = api_obj.get_pkg_categories()
                all_pkgs = self.packages
                all_cats = sorted(set(
                    sc
                    for p in all_pkgs
                    for sc in get_pkg_cats(p)
                ))
                self.assertPrettyEqual(returned, all_cats)

                # Verify all case with a few different pub combos.
                combos = [
                    (["test1", "test2"], all_cats),
                    (["test1"], all_cats),
                    (["test2"], all_cats),
                    (["test3"], []),
                    ([], all_cats),
                ]

                for combo, expected in combos:
                        returned = api_obj.get_pkg_categories(pubs=combo)
                        self.assertPrettyEqual(returned, expected)

                # Now install different sets of packages and ensure the
                # results match what is expected.
                combos = [
                    [
                        self.dlist1[6], # "apple@1.2.1,5.11-1"
                        self.dlist1[7], # "bar@1.2,5.11-0"
                    ],
                    [
                        self.dlist1[12], # "corge@1.0"
                        self.dlist1[14], # "grault@1.0"
                    ],
                    [
                        self.dlist1[16], # "quux@1.0"
                    ],
                ]

                for combo in combos:
                        pkgs = [
                            f.get_fmri(anarchy=True, include_scheme=False)
                            for f in combo
                        ]
                        api_obj.plan_install(pkgs)
                        api_obj.prepare()
                        api_obj.execute_plan()
                        api_obj.reset()

                        returned = api_obj.get_pkg_categories(installed=True)
                        expected = sorted(set(
                            sc
                            for p in pkgs
                            for sc in get_pkg_cats(p)
                        ))
                        self.assertPrettyEqual(returned, expected)

                        # Prepare for next test.
                        # skip corge since it's renamed
                        api_obj.plan_uninstall([
                                                p
                                                for p in pkgs
                                                if not p.startswith("corge@1.0")
                                                ], False)
                        api_obj.prepare()
                        api_obj.execute_plan()
                        api_obj.reset()

        def test_list_08_patterns(self):
                """Verify that pattern filtering works as expected."""

                progresstracker = progress.NullProgressTracker()
                api_obj = api.ImageInterface(self.get_img_path(), CLIENT_API_VERSION,
                    progresstracker, lambda x: False, PKG_CLIENT_NAME)

                # First, check all variants, but with multiple patterns for the
                # partial, exact, and wildcard match cases.
                patterns = ["bar", "pkg:/baz", "*obs*"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test1", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test1", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test1", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 10, "baz", "1.3,5.11"),
                    self.__get_exp_pub_entry("test2", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test2", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 10)

                # Next, check all variants, but with exact and partial match.
                patterns = ["pkg:/bar", "obsolete"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 15, "obsolete",
                        "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 15, "obsolete",
                        "1.0,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 2)

                # Next, check all variants, but for publisher and exact
                # match case only.
                patterns = ["pkg://test2/bat/bar"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 1)

                # Should return no matches.
                patterns = ["pkg://test2/bar"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)
                expected = []
                self.assertPrettyEqual(returned, expected)

                # Next, check all variants, but for exact match case only.
                patterns = ["pkg:/bat/bar"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 7, "bat/bar",
                        "1.2,5.11-0"),
                    self.__get_exp_pub_entry("test2", 7, "bat/bar",
                        "1.2,5.11-0"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 2)

                # Next, check version matching for a single pattern.
                patterns = ["apple@1.2.0"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 3, "apple",
                        "1.2.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 3, "apple",
                        "1.2.0,5.11-0"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 2)

                patterns = ["apple@1.0"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 1, "apple",
                        "1.0,5.11-0"),
                    self.__get_exp_pub_entry("test2", 1, "apple",
                        "1.0,5.11-0"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 2)

                patterns = ["apple@*,*-1"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 6, "apple",
                        "1.2.1,5.11-1"),
                    self.__get_exp_pub_entry("test2", 6, "apple",
                        "1.2.1,5.11-1"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 2)

                # Next, check version matching for multiple patterns.
                patterns = ["baz@1.0", "pkg:/obsolete@1.1",
                    "pkg://test1/qux@0.9"]
                returned = self.__get_returned(api_obj.LIST_ALL,
                    api_obj=api_obj, patterns=patterns, variants=True)

                expected = [
                    self.__get_exp_pub_entry("test1", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test1", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test2", 9, "baz", "1.0.1,5.11"),
                    self.__get_exp_pub_entry("test2", 8, "baz", "1.0,5.11"),
                    self.__get_exp_pub_entry("test1", 17, "qux", "0.9,5.11"),
                ]
                self.assertPrettyEqual(returned, expected)
                self.assertEqual(len(returned), 5)

                # Finally, verify that specifying an illegal pattern will
                # raise an InventoryException.
                patterns = ["baz@1.*.a"]
                expected = [
                    version.IllegalVersion(
                        "Bad Version: %s" % p.split("@", 1)[-1])
                    for p in patterns
                ]
                try:
                        returned = self.__get_returned(api_obj.LIST_ALL,
                            api_obj=api_obj, patterns=patterns, variants=True)
                except api_errors.InventoryException, e:
                        self.assertEqualDiff(expected, e.illegal)
                else:
                        raise RuntimeError("InventoryException not raised!")


if __name__ == "__main__":
        unittest.main()
