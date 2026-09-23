#!/usr/bin/env python3
"""Start the :8933 cloakbrowsermcp instance as a detached daemon (double-fork).

Persistent on purpose: survives the calling session, like the :8932 rig server.
Safe to re-run - refuses if the port is already serving.
"""
import os, socket, sys, time

PORT = 8933
PY = os.path.expanduser("~/.local/share/uv/tools/cloakbrowsermcp/bin/python")
LAUNCHER = "/home/ubuntu/x-op/mcp_launcher_8933.py"
LOG = "/home/ubuntu/x-op/logs/mcp-8933.log"


def port_busy():
    s = socket.socket()
    try:
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        return True
    except Exception:
        return False
    finally:
        s.close()


def main():
    if port_busy():
        print("already serving on %d" % PORT)
        return 0
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if os.fork() > 0:
        time.sleep(1.5)
        print("daemonized (parent exits)")
        return 0
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    os.chdir("/home/ubuntu/x-op")
    with open(LOG, "a") as lf:
        os.dup2(lf.fileno(), 1)
        os.dup2(lf.fileno(), 2)
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.execv(PY, [PY, LAUNCHER])
    return 0


if __name__ == "__main__":
    sys.exit(main())
