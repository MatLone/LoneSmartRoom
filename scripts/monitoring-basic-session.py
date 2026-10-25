"""One explicitly authorized physical session. Never called by the app or agent.

No retry/overwrite: marker is exclusive and must not be removed to repeat a test.
Requires successful mock tests for exact current sources. No IPC/network/providers
other than basic read-only Win32/PDH. Default 80s leaves room for normal cleanup.
"""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if sys.argv[1:] != ['--authorized-single-session']:
        raise SystemExit('Explicit physical-session authorization flag required; nothing collected.')
    from monitoring.basic_validation import source_hashes
    directory = ROOT / '.cache/validation/monitoring-basic-2026-10-25'
    proof = json.loads((directory / 'simulated-tests.json').read_text(encoding='utf-8'))
    if not proof.get('ok') or proof.get('source_hashes') != source_hashes(ROOT):
        raise SystemExit('Current sources have not passed the simulated gate; nothing collected.')
    # Exclusive marker is written BEFORE native construction, including failed attempts.
    with (directory / 'physical-session-started.json').open('x', encoding='utf-8') as handle:
        json.dump({'pid': os.getpid(), 'authorized_max_seconds': 90}, handle)
    attempt = time.monotonic()
    api, result = None, {'reason': 'initialization_failed', 'native_session_attempted': True}
    try:
        from monitoring.windows_native import WindowsReadApi
        from monitoring.basic_session import run_session
        from monitoring.collector import Clock
        api = WindowsReadApi()
        api.require_non_elevated()
        volumes = api.fixed_volumes()
        from monitoring.windows_basic import basic_catalog
        basic_catalog(volumes)  # Fail closed if more than seven fixed volumes.
        if volumes:
            api.open_disk_query(volumes)
        remaining = min(80, 85 - (time.monotonic() - attempt))
        if remaining <= 0:
            raise RuntimeError('initialization_budget_exceeded')
        result = run_session(api, volumes, Clock(), time.sleep, duration=remaining)
        result.update({'volumes': [v[:2] for v in volumes], 'collector_pid': os.getpid(),
                       'non_elevated': True, 'native_session_attempted': True,
                       'network_started': False, 'native_ipc_started': False,
                       'real_sources': ['GetSystemTimes', 'GlobalMemoryStatusEx',
                                        'GetDiskSpaceInformationW', 'PDH LogicalDisk'],
                       'agent_accessed': False, 'gpu_temperature_fan_collection': False})
    except KeyboardInterrupt:
        result['reason'] = 'interrupted'
    except Exception:
        # No native exception/path/token data in logs; preserve failed attempt marker.
        result['reason'] = 'session_failed'
    finally:
        if api is not None:
            try:
                api.close_disk_query()
            except Exception:
                result['native_query_close_failed'] = True
        result['attempt_elapsed_seconds'] = time.monotonic() - attempt
        with (directory / 'physical-session.json').open('x', encoding='utf-8') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'metrics')}, ensure_ascii=False))
    return 0 if (result.get('reason') == 'duration_complete' and result.get('stop', {}).get('clean')
                 and not result.get('monitoring_threads_remaining')
                 and not result.get('native_query_close_failed') and result['attempt_elapsed_seconds'] <= 90) else 1


if __name__ == '__main__':
    raise SystemExit(main())
