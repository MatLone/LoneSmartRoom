"""Fixed passive desktop evidence; NEVER borrows the Samsung HMAC identity.

Identity/listener/startup metadata use existing readers. HTTPS authentication
stays unknown until an independently authorized receipt is supplied in a later
deployment. No HTTP, DPAPI, command, repair or sensor reader is called here.
"""
from datetime import datetime, timezone
import time
from .passive import report_for


def collect(reader, *, clock=time.monotonic, utc=lambda: datetime.now(timezone.utc)):
    deadline = clock()+12
    try:
        reader.begin(deadline)
        census = reader.census(deadline=deadline)
        if clock() > deadline: raise TimeoutError('observation_deadline')
        report, _ = report_for(census, {}, utc(), clock())
        # Existing restricted Electron model calls validated local observations
        # local_cache. No historical observation is re-timestamped here.
        for row in report['checks']: row['evidence_kind'] = 'local_cache'
        return report
    finally:
        # Existing CIM helpers are read-only but must not outlive this worker.
        # A stuck helper keeps the worker tracked (main reports timeout and
        # refuses successful shutdown); no process is forcibly terminated.
        try:
            scanners = getattr(reader, 'scanners', ())
            if isinstance(scanners, (list,tuple)):
                for child in scanners:
                    while True:
                        try:
                            child.wait()
                            break
                        except OSError: time.sleep(1)
        finally: reader.close()
