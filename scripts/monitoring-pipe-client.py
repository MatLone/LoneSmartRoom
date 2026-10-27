"""Fixed stdio read adapter owned by Electron main; independent collector over native pipe.

No renderer-supplied paths/arguments, no TCP, no agent imports or credentials.
EOF closes only this adapter's worker lifetime pipe. Never kills processes.
"""
import argparse
import ctypes as ct
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from monitoring.ipc import MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, encode
from monitoring.pipe_protocol import pipe_name, request
from monitoring.winpipe import WindowsPipeApi
from monitoring.lifetime import duration_for,end_at
from monitoring.application_context import validate_mode,application_owner
from monitoring.gpu_development import validate_gpu_mode


def main(*, snapshot_sink=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    lifetime=parser.add_mutually_exclusive_group()
    lifetime.add_argument('--duration', type=int, choices=range(1, 76))
    lifetime.add_argument('--application',action='store_true')
    parser.add_argument('--owner-pid',type=int)
    parser.add_argument('--simulated', action='store_true')
    parser.add_argument('--gpu-development', action='store_true')
    args = parser.parse_args()
    duration=duration_for(args.duration,args.application)
    validate_mode(ROOT,args.application,args.simulated)
    validate_gpu_mode(ROOT,args.gpu_development,args.application,args.simulated,duration)
    name = pipe_name(args.session)
    api = WindowsPipeApi(); stop = threading.Event(); started = time.monotonic()
    owner=application_owner(api,ROOT,args.owner_pid) if args.application else None
    worker, handle = None, None
    messages = queue.Queue(maxsize=4); child_lines = queue.Queue(maxsize=4)
    def emit(value): print(encode(value).decode(), flush=True)
    def read_input(stream, target, maximum):
        try:
            while True:
                line = stream.readline(maximum+2)
                if not line: break
                if len(line) > maximum+1 or not line.endswith(b'\n'):
                    stop.set(); break
                try: target.put_nowait(line.rstrip(b'\r\n'))
                except queue.Full: stop.set(); break
        finally:
            try: target.put_nowait(None)
            except queue.Full: stop.set()
    try:
        environment = {k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON', 'NODE_OPTIONS'))}
        command = [sys.executable, '-I', '-B', str(ROOT/'scripts/monitoring-pipe-server.py'),
                   '--session', args.session, '--parent-pid', str(os.getpid())]
        command+=['--application'] if args.application else ['--duration',str(duration)]
        if args.simulated: command.append('--simulated')
        if args.gpu_development: command.append('--gpu-development')
        worker = subprocess.Popen(command, cwd=ROOT, env=environment, shell=False,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  creationflags=0x08000000, bufsize=0)
        handle = api.hold_process(worker.pid); expected = api.identity(handle)
        if any(expected[k] != api.own[k] for k in ('sid', 'session', 'image')) or expected['elevated']:
            raise PermissionError('unexpected_worker')
        threading.Thread(target=read_input, args=(worker.stdout, child_lines, 4096), daemon=True).start()
        ready = json.loads(child_lines.get(timeout=8))
        if ready != {'v':1, 'ready':True, 'pid':worker.pid, 'simulated':args.simulated}:
            raise PermissionError('unexpected_worker_ready')
        emit({'v':1, 'event':'ready', 'bridge_pid':os.getpid(), 'collector_pid':worker.pid,
              'transport':'windows_named_pipe_v1', 'simulated':args.simulated})
        threading.Thread(target=read_input, args=(sys.stdin.buffer, messages, MAX_REQUEST_BYTES), daemon=True).start()
        while (not stop.is_set() and time.monotonic() < end_at(started,duration) and worker.poll() is None
               and (owner is None or api.alive(owner))):
            try: payload = messages.get(timeout=0.1)
            except queue.Empty: continue
            if payload is None: break
            try:
                request(payload)
                deadline = min(end_at(started,duration), time.monotonic()+1.5)
                connection = api.connect(name, handle, expected, deadline, stop)
                try:
                    api.write_frame(connection, payload, MAX_REQUEST_BYTES, deadline, stop)
                    response = api.read_frame(connection, MAX_RESPONSE_BYTES, deadline, stop)
                    api._io(connection, 'write', ct.create_string_buffer(b'\x06'), 1, deadline, stop)
                finally: api.close(connection)
                decoded = json.loads(response)
                if snapshot_sink is not None and decoded.get('ok') and 'snapshot' in decoded:
                    # Optional development fan-out of the SAME protected-pipe read.
                    # No second collector; a rejected projection does not stop local monitoring.
                    try: snapshot_sink(decoded['snapshot'])
                    except (ValueError, TypeError): pass
                emit({'v':1, 'event':'response', 'body':decoded})
            except (OSError, ValueError, TimeoutError):
                emit({'v':1, 'event':'disconnected', 'error':'local_read_unavailable'})
    except Exception as error:
        emit({'v':1, 'event':'error', 'error':type(error).__name__})
    finally:
        stop.set(); stopped = None
        if worker is not None:
            if worker.stdin: worker.stdin.close()
            pending_reported=False;closing_started=time.monotonic()
            while worker.poll() is None:
                try:worker.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    if time.monotonic()-closing_started>5 and not pending_reported:
                        emit({'v':1,'event':'shutdown_pending'});pending_reported=True
            # A pending diagnostic may precede the final sanitized stop record.
            while True:
                try:
                    line=child_lines.get(timeout=1)
                    if line is None:break
                    value=json.loads(line)
                    if value.get('stopped') is True:stopped=value
                except (queue.Empty,ValueError):break
        if handle is not None: api.close(handle)
        if owner is not None:api.close(owner)
        clean = worker is not None and worker.poll() == 0 and bool(stopped and stopped.get('ok'))
        emit({'v':1, 'event':'stopped', 'clean':clean, 'workerExited':worker is None or worker.poll() is not None, 'worker':stopped,
              'elapsed_seconds':time.monotonic()-started})
    return 0 if clean else 1


if __name__ == '__main__': raise SystemExit(main())
