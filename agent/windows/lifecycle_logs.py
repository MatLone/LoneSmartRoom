"""Successor log schema for opt-in lifecycle; original operational logger unchanged."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from launcher_logs import EVENTS, PHASES, DEPENDENCIES, error_code

LIFECYCLE_EVENTS = EVENTS | frozenset(('shutdown_requested', 'listener_closed',
    'shutdown_deadline_exceeded', 'shutdown_complete', 'shutdown_failed',
    'mutex_released', 'stop_completed', 'stop_timed_out', 'stop_not_running'))


class LifecycleLog:
    MAX_BYTES, BACKUPS = 65536, 3

    def __init__(self, directory, windows, name):
        self.directory, self.windows, self.name = Path(directory), windows, name
        windows.private_directory(self.directory)

    def emit(self, event, *, phase=None, code=None, dependency=None):
        if event not in LIFECYCLE_EVENTS or phase is not None and phase not in PHASES:
            raise ValueError('unknown_log_tag')
        if dependency is not None and dependency not in DEPENDENCIES:
            raise ValueError('unknown_dependency')
        if code is not None and (type(code) is not int or not -2**31 <= code < 2**32):
            raise ValueError('invalid_code')
        record = {'utc':datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                  'pid':os.getpid(), 'event':event}
        record.update({key:value for key,value in
            (('phase',phase),('code',code),('dependency',dependency)) if value is not None})
        data = (json.dumps(record, separators=(',',':'))+'\n').encode('ascii')
        with self.windows.mutex(self.name+'.logs', timeout=3000):
            self.windows.verify_private(self.directory)
            files = [self.directory/('startup.log'+(f'.{i}' if i else ''))
                     for i in range(self.BACKUPS+1)]
            for path in files:
                if path.exists() or path.is_symlink():
                    self.windows.private_file(path)
            if files[0].exists() and files[0].stat().st_size+len(data)>self.MAX_BYTES:
                files[-1].unlink(missing_ok=True)
                for i in range(self.BACKUPS-1,-1,-1):
                    if files[i].exists():files[i].replace(files[i+1])
            self.windows.private_file(files[0])
            with files[0].open('ab') as output:
                output.write(data); output.flush()
