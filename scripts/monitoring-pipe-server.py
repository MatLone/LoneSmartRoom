"""Development collector worker. Only launched by the fixed local bridge script."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from monitoring.collector import Collector
from monitoring.ipc import encode
from monitoring.pipe_server import PipeServer
from monitoring.winpipe import WindowsPipeApi
from monitoring.windows_basic import CpuProvider, MemoryProvider, VolumeProvider, DiskIoProvider, basic_catalog
from monitoring.lifetime import duration_for,finish_collector
from monitoring.application_context import validate_mode
from monitoring.gpu_development import validate_gpu_mode,claim_gpu_owner,finish_gpu,ReadActivity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--parent-pid', required=True, type=int)
    lifetime=parser.add_mutually_exclusive_group()
    lifetime.add_argument('--duration', type=int, choices=range(1, 76))
    lifetime.add_argument('--application',action='store_true')
    parser.add_argument('--simulated', action='store_true')
    parser.add_argument('--gpu-development', action='store_true')
    args = parser.parse_args()
    duration=duration_for(args.duration,args.application)
    validate_mode(ROOT,args.application,args.simulated)
    validate_gpu_mode(ROOT,args.gpu_development,args.application,args.simulated,duration)
    api, collector, server, parent = None, None, None, None
    gpu_adapter,gpu_owner=None,None
    stop = threading.Event(); started = time.monotonic(); result = {'ok': False}
    try:
        api = WindowsPipeApi()
        if args.application and api.own['image']!=os.path.normcase(os.path.realpath(ROOT.parent/'runtime/python.exe')):
            raise PermissionError('unexpected_bundle_interpreter')
        if os.getppid() != args.parent_pid: raise PermissionError('unexpected_parent')
        parent = api.hold_process(args.parent_pid)
        expected = api.identity(parent)
        if any(expected[k] != api.own[k] for k in ('sid', 'session', 'image')) or expected['elevated']:
            raise PermissionError('unexpected_parent')
        if args.simulated:
            # Explicit fixture, visibly marked by the contract; no native sensor object constructed.
            sys.path.insert(0, str(ROOT/'tests/monitoring'))
            from pipe_fixture import FixtureProvider
            specs = basic_catalog(('C:\\', 'D:\\'))
            collector = Collector(specs, [FixtureProvider(specs)])
        else:
            from monitoring.windows_native import WindowsReadApi
            from monitoring.development_collector import create_basic_collector
            sensors = WindowsReadApi(); sensors.require_non_elevated()
            if args.gpu_development:
                gpu_owner=claim_gpu_owner(api)  # Refuse duplicates before constructing/loading ADLX.
                from monitoring.adlx_bridge import real_adapter
                gpu_adapter=real_adapter(owner_handle=gpu_owner)  # Only the owned lease handle is inherited; diagnostics OFF.
            collector = create_basic_collector(sensors,gpu_adapter=gpu_adapter)
        activity=ReadActivity(collector,time.monotonic) if args.gpu_development else None
        server = PipeServer(api, collector, args.session, parent, expected, stop, duration=duration, simulated=args.simulated,activity=activity)
        server.open()  # If name/ACL setup fails, no real sampling has started.
        def eof_stop():
            sys.stdin.buffer.read(1)  # Only lifetime EOF/closure, no command parser or remote shutdown endpoint.
            stop.set()
        threading.Thread(target=eof_stop, name='LonePipeLifetime', daemon=True).start()
        collector.start()
        print(json.dumps({'v': 1, 'ready': True, 'pid': os.getpid(), 'simulated': args.simulated}), flush=True)
        server.serve()
        result = {'ok': True, 'connections': server.counts,
                  'cache_samples': collector.cache.sample_count, 'diagnostics': collector.diagnostics()}
    except Exception as error:
        result = {'ok': False, 'error': type(error).__name__}  # no paths, payloads, tokens or exception text.
    finally:
        stop.set()
        if server is not None: server.close()
        if collector is not None:
            stopped = finish_collector(collector,lambda:print(encode({'v':1,'pending_stop':True}).decode(),flush=True))
            result['stop'] = {'clean': stopped.clean, 'stopped': stopped.stopped, 'timed_out': stopped.timed_out}
            result['ok'] = result['ok'] and stopped.clean
        if gpu_adapter is not None:
            clean=finish_gpu(gpu_adapter,lambda:print(encode({'v':1,'pending_stop':True}).decode(),flush=True))
            process=gpu_adapter.transport.process
            result['gpu']={'clean':clean,'exited':process is None or process.poll() is not None,
                           'pid':process.pid if process else None}
            result['ok']=result['ok'] and clean
        if api is not None and gpu_owner is not None:api.close(gpu_owner)
        if api is not None and parent is not None: api.close(parent)
        result.update(v=1, stopped=True, pid=os.getpid(), elapsed_seconds=time.monotonic()-started,
                      ended_at=datetime.now(timezone.utc).isoformat())
        print(encode(result).decode(), flush=True)
    return 0 if result['ok'] else 1


if __name__ == '__main__': raise SystemExit(main())
