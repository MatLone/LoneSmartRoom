"""Fixed-schema JSONL startup receipts. No arbitrary messages or exception text."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path

EVENTS = frozenset(('attempt', 'paths_ok', 'paths_invalid', 'environment_invalid',
    'spawn_failed', 'child_created', 'child_exit', 'worker_attempt', 'duplicate',
    'legacy_present', 'guard_failed', 'lock_recovered', 'dependency_missing',
    'dependency_failed', 'bootstrap_ready', 'agent_returned', 'agent_failed',
    'invalid_arguments', 'launcher_failed'))
PHASES = frozenset(('supervisor', 'worker', 'paths', 'environment', 'guard', 'agent'))
DEPENDENCIES = frozenset(('cryptography', 'cffi', 'pycparser', 'other'))


class StartupLog:
    MAX_BYTES = 65536
    BACKUPS = 3

    def __init__(self, directory, windows, name):
        self.directory, self.windows, self.name = Path(directory), windows, name
        windows.private_directory(self.directory)

    def emit(self, event, *, phase=None, code=None, dependency=None):
        if event not in EVENTS or phase is not None and phase not in PHASES:
            raise ValueError('unknown_log_tag')
        if dependency is not None and dependency not in DEPENDENCIES:
            raise ValueError('unknown_dependency')
        if code is not None and (type(code) is not int or not -2**31 <= code < 2**32):
            raise ValueError('invalid_code')
        record = {'utc': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                  'pid': os.getpid(), 'event': event}
        record.update({key: value for key, value in
            (('phase', phase), ('code', code), ('dependency', dependency)) if value is not None})
        data = (json.dumps(record, separators=(',', ':')) + '\n').encode('ascii')
        with self.windows.mutex(self.name + '.logs', timeout=3000):
            self.windows.verify_private(self.directory)
            files = [self.directory / ('startup.log' + (f'.{i}' if i else ''))
                     for i in range(self.BACKUPS + 1)]
            for path in files:
                if path.exists() or path.is_symlink():
                    self.windows.private_file(path)  # Reject links, foreign owners/ACLs.
            if files[0].exists() and files[0].stat().st_size + len(data) > self.MAX_BYTES:
                files[-1].unlink(missing_ok=True)
                for i in range(self.BACKUPS - 1, -1, -1):
                    if files[i].exists():
                        files[i].replace(files[i + 1])
            self.windows.private_file(files[0])
            with files[0].open('ab') as output:
                output.write(data)
                output.flush()


def error_code(error):
    """Never serialize repr/str/args, paths or tracebacks."""
    for key in ('winerror', 'errno'):
        value = getattr(error, key, None)
        if type(value) is int and -2**31 <= value < 2**32:
            return value
    return 1
