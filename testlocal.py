#!/usr/bin/env python3

"""Allow for testing searches on local log data

The log data is expected to be in ./moddata/log/ in the same structure as it is
on the server
"""

import sys

try:
    import znc
except ImportError:
    pass

if __name__ == "__main__" and "znc" not in sys.modules:

    print("WARNING: Testing znc-logsearch locally")
    print("WARNING: Results may differ when running as a ZNC module")
    print("--------------------------------------------------------")
    print()

    from argparse import Namespace

    # Mock the ZNC module with enough functionality for testing
    sys.modules["znc"] = Namespace(
        Module = object,
        CModInfo = Namespace(UserModule=None, GlobalModule=None),
        CZNC = Namespace(Get=lambda: Namespace(GetZNCPath=lambda: "."))
    )

    import logsearch

    mock = Namespace(
        GetUserName=lambda: "*",
        GetUserPath=lambda: "/dev/null",
        GetName=lambda: "*",
        GetNetworkPath=lambda: "/dev/null",
    )

    l = logsearch.logsearch()
    l.GetUser = lambda: mock
    l.GetNetwork = lambda: mock
    l.PutModule = print
    l.show_help = lambda: print("Syntax: <window> <query>")

    l.OnModCommand(" ".join(sys.argv[1:]))
