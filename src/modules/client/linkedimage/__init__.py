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
# Copyright (c) 2011, Oracle and/or its affiliates. All rights reserved.
#

"""
Initialize the linked image module.  Consumers of linked image functionality
should never import anything other than pkg".client.linkedimage".  Here we'll
import everything in linkedimage/common.py into our namespace (since that's
where most of our code lives.) We'll also hard code which linked image plugin
modules are supported below.
"""

# standard python classes
import inspect
import os

# import linked image common code
# W0401 Wildcard import
# W0403 Relative import
from common import * # pylint: disable-msg=W0401,W0403

# names of linked image plugins
p_types = [ "zone", "system" ]

# map of plugin names to their associated LinkedImagePlugin derived class
p_classes = {}

# map of plugin names to their associated LinkedImageChildPlugin derived class
p_classes_child = {}

# initialize temporary variables
_modname = _module = _nvlist = _classes = _i = None

# initialize p_classes and p_classes_child
for _modname in p_types:
        _module = __import__("%s.%s" % (__name__, _modname),
            globals(), locals(), [_modname])

        # Find all the classes actually defined in this module.
        _nvlist = inspect.getmembers(_module, inspect.isclass)
        _classes = [
            _i[1]
            for _i in _nvlist
            if _i[1].__module__ == ("%s.%s" % (__name__, _modname))
        ]

        for _i in _classes:
                if LinkedImagePlugin in inspect.getmro(_i):
                        p_classes[_modname] = _i
                elif LinkedImageChildPlugin in inspect.getmro(_i):
                        p_classes_child[_modname] = _i
                else:
                        raise RuntimeError("""
Invalid linked image plugin class '%s' for plugin '%s'""" %
                             (_i.__name__, _modname))

# Clean up temporary variables
del _modname, _module, _nvlist, _classes, _i
