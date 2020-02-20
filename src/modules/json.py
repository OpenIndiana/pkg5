#!/usr/bin/python3.5
#
# {{{ CDDL HEADER
#
# This file and its contents are supplied under the terms of the
# Common Development and Distribution License ("CDDL"), version 1.0.
# You may only use this file in accordance with the terms of version
# 1.0 of the CDDL.
#
# A full copy of the text of the CDDL should have accompanied this
# source. A copy of the CDDL is also available via the Internet at
# http://www.illumos.org/license/CDDL.
# }}}

# Copyright 2020 OmniOS Community Edition (OmniOSce) Association.

"""
json module abstraction for the packaging system.
"""

############################################################################
# Standard version

from rapidjson import loads, load, dumps, dump, JSONDecodeError
from jsonschema import validate, ValidationError

############################################################################
# Debug/profiling version

##from pkg.client.debugvalues import DebugValues
##import pkg.misc as misc
##
##import os, time
##import rapidjson as _json
##
##JSONDecodeError = _json.JSONDecodeError
##
##def _start():
##    global rss, start
##    psinfo = misc.ProcFS.psinfo()
##    rss = psinfo.pr_rssize
##    start = time.time()
##
##def _end(func, param, ret):
##    taken = time.time() - start
##    psinfo = misc.ProcFS.psinfo()
##    mem = (psinfo.pr_rssize - rss) / 1024.0
##    print("JSON Mem +{:.2f} MiB - Time {:.2f}s - {}({}) = {}"
##        .format(mem, taken, func, param, ret))
##
##def _file(stream):
##        try:
##            name = stream.name
##            size = os.path.getsize(name) / (1024.0 * 1024.0)
##            return "{:.2f} MiB {}".format(size, name)
##        except:
##            return str(stream)
##
##def load(stream, **kw):
##    if "json" in DebugValues:
##        _start()
##        ret = _json.load(stream, **kw)
##        _end('load', _file(stream), '')
##        return ret
##    else:
##        return _json.load(stream, **kw)
##
##def loads(str, **kw):
##    if "json" in DebugValues:
##        _start()
##        ret = _json.loads(str, **kw)
##        _end('loads', len(str), '')
##        return ret
##    else:
##        return _json.loads(str, **kw)
##
##def dump(obj, stream, **kw):
##    if "json" in DebugValues:
##        _start()
##        ret = _json.dump(obj, stream, **kw)
##        _end('dump', _file(stream), ret)
##        return ret
##    else:
##        return _json.dump(obj, stream, **kw)
##
##def dumps(obj, **kw):
##    if "json" in DebugValues:
##        _start()
##        ret = _json.dumps(obj, **kw)
##        _end('dumps', '', len(ret))
##        return ret
##    else:
##        return _json.dumps(obj, **kw)

# Vim hints
# vim:ts=4:sw=4:et:fdm=marker
