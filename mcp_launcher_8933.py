#!/usr/bin/env python3
"""Serve cloakbrowsermcp over streamable HTTP on 127.0.0.1:8933 - SECOND instance.

Purpose: post-side / research browser, isolated from the reply rig on :8932.
Its browser is launched separately (cloak_launch) with its own profile copy
(/home/ubuntu/.cloakbrowser/profiles/operator2), so it never shares pages,
locks, or tab state with the worker's browser.
"""
import sys


def main():
    from cloakbrowsermcp.server import create_server
    server = create_server(caps={"vision"})
    server.settings.host = "127.0.0.1"
    server.settings.port = 8933
    server.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    sys.exit(main())
