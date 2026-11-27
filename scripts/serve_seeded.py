"""Start a fresh, seeded Ephios server from THIS source tree and keep it running until the process is stopped.

Used for the audits that need a running application (axe-core, Lighthouse, ZAP, k6): prints `READY <base url>` once
the login page answers. Environment: E2E_BIND / E2E_PUBLIC_HOST (see tests/team/api/support.py).
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.team.api.support import Server


def main():
    server = Server(tempfile.mkdtemp(prefix="ephios_audit_"))
    server.start()
    print("READY", server.base, flush=True)
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
