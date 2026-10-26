"""Explicit, one-shot diagnostic harness. Never imported by operational workers.

Rejected validation frames remain rejected. Only this observation harness may keep
reading the SAME initialized bridge after a well-identified frame validation error.
Transport/permission/bootstrap failures stop the session; no restart or force kill.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from monitoring.adlx_bridge import BridgeError
from monitoring.adlx_diagnostics import RULES
from monitoring.adlx_provider import AdlxProvider, GPU_SPECS, WarmingUp
from monitoring.basic_session import resource_sample, stats, summarize
from monitoring.collector import Collector, Schedule
from monitoring.contracts import ContractError

OUT = ROOT / '.cache/validation/recovery-adlx-instrumented-2026-10-25'


class ObservedAdapter:
    def __init__(self, inner):
        self.inner = inner
        self.data_kind = inner.data_kind
        self.attempts = 0
        self.outcome = None
        self.rule = None
        self.fatal = False

    def open(self): return self.inner.open()
    def devices(self): return self.inner.devices()
    def capabilities(self, key): return self.inner.capabilities(key)
    def total_vram(self, key): return self.inner.total_vram(key)
    def close(self): return self.inner.close()

    def latest(self, key):
        self.attempts += 1
        self.outcome, self.rule = 'accepted', None
        try:
            return self.inner.latest(key)
        except WarmingUp:
            self.outcome = 'warming_up'
            raise
        except BridgeError as error:
            if error.code in ('invalid_frame', 'invalid_reading') and error.rule in RULES:
                self.outcome, self.rule = 'rejected', error.rule
            else:
                self.outcome, self.fatal = 'fatal', True
            raise
        except Exception:
            self.outcome, self.fatal = 'fatal', True
            raise

    def note_provider(self, rule, *, metric=None):
        if rule in RULES:
            self.outcome, self.rule = 'rejected', rule
        callback = getattr(self.inner, 'note_provider', None)
        if callback:
            callback(rule, metric=metric)


def run_instrumented(adapter, resources, clock, wait, *, duration=70, on_row=None):
    if type(duration) not in (int, float) or not 0 < duration <= 70:
        raise ContractError('invalid_session_duration')
    processors = resources.logical_processors()
    if type(processors) is not int or not 1 <= processors <= 4096:
        raise ContractError('invalid_processor_count')
    start, started = clock.monotonic(), clock.utcnow()
    base = resources.collector()
    observed = ObservedAdapter(adapter)
    collector = None
    rows, counts, rules = [], Counter(), Counter()
    previous, previous_time = {}, {}
    first, clean, final_cpu, resource_failure = None, False, None, False
    reason = 'duration_complete'
    try:
        observed.open()
        devices = observed.devices()
        if len(devices) != 1:
            raise ContractError('invalid_device_count')
        provider = AdlxProvider(observed, devices[0].key)  # unchanged 1.5 s freshness
        collector = Collector(GPU_SPECS, [provider], clock=clock,
                              schedule=Schedule(fast=2, thermal=2, capacity=60, read_budget=1))
        while clock.monotonic() - start < duration:
            cycle, before = clock.monotonic(), observed.attempts
            collector.step()
            snapshot = collector.snapshot()
            dynamic = [m for m in snapshot['metrics'] if m['id'] != 'gpu.adlx.vram_total_mb']
            attempted = observed.attempts != before
            outcome = observed.outcome if attempted else 'not_sampled'
            if attempted:
                if outcome == 'accepted':
                    outcome = 'valid' if any(m['valid'] for m in dynamic) else 'unavailable'
                first = outcome if first is None else first
                counts[outcome] += 1
                if observed.rule:
                    rules[observed.rule] += 1
            samples = {}
            for name, read in (('collector', resources.collector), ('bridge', resources.bridge)):
                value, at = read(), clock.monotonic()
                samples[name] = resource_sample(value, previous.get(name), at - previous_time.get(name, at), processors)
                previous[name], previous_time[name] = value, at
            row = {'elapsed_seconds': clock.monotonic() - start, 'snapshot': snapshot,
                   'frame_outcome': outcome, 'rule': observed.rule if attempted else None,
                   'resources': samples, 'cycle_seconds': clock.monotonic() - cycle,
                   'cache_samples': collector.cache.sample_count}
            rows.append(row)
            if on_row: on_row(row)
            if observed.fatal or any(m['state'] == 'permission_denied' for m in dynamic):
                reason = 'fatal_read_error'
                break
            if not attempted and any(m['state'] == 'error' for m in dynamic):
                reason = 'unclassified_read_error'
                break
            if any(v['working_set_bytes'] > 512 * 1024**2 for v in samples.values()):
                reason = 'memory_budget_exceeded'
                break
            if len(rows) >= 36:
                reason = 'row_limit'
                break
            remaining = duration - (clock.monotonic() - start)
            if remaining > 0:
                wait(min(remaining, max(0, 2 - (clock.monotonic() - cycle))))
    except Exception:
        reason = 'session_failed'  # Never log free-form exceptions or payloads.
    finally:
        if collector:
            stopped = collector.stop(timeout=6)
            clean = stopped.stopped and stopped.clean
        else:
            try:
                adapter.close()
                clean = adapter.clean is True
            except Exception:
                clean = False
        try:
            final_cpu = {'collector': resources.collector()['cpu_seconds'], 'bridge': resources.bridge_cpu()}
        except Exception:
            resource_failure = True
    elapsed = clock.monotonic() - start
    summary = {}
    for name in ('collector', 'bridge'):
        samples = [row['resources'][name] for row in rows]
        cpu = final_cpu[name] - (base['cpu_seconds'] if name == 'collector' else 0) if final_cpu else None
        summary[name] = {'cpu_percent_total_normalized': cpu * 100 / elapsed / processors if cpu is not None and elapsed > 0 else None,
                         'rss_bytes': stats(s['working_set_bytes'] for s in samples),
                         'private_commit_bytes': stats(s['private_commit_bytes'] for s in samples)}
    diagnostics = adapter.diagnostics()
    return {'startedUtc': started.isoformat(), 'elapsedSeconds': elapsed, 'reason': reason,
            'shutdownClean': clean, 'resourceReadFailed': resource_failure, 'logicalProcessors': processors,
            'rows': rows, 'metrics': summarize(rows), 'resourceSummary': summary,
            'combinedResidentBytes': stats(sum(v['working_set_bytes'] for v in row['resources'].values()) for row in rows),
            'frameCounts': dict(counts), 'ruleCounts': dict(rules), 'firstFrameOutcome': first,
            'readAttempts': observed.attempts, 'adapterDiagnostics': diagnostics,
            'restarted': False, 'forcedTermination': False}


def diagnostic_bytes(diagnostics):
    """Single bounded export; keep the first rejection and only recent records."""
    data = dict(diagnostics.get('frame_diagnostics', {}))
    data['records'] = list(data.get('records', []))
    while True:
        encoded = json.dumps(data, allow_nan=False, separators=(',', ':')).encode('utf-8')
        if len(encoded) <= 32768 and len(data['records']) <= 16:
            return encoded
        if len(data['records']) <= 1:
            raise ContractError('diagnostic_export_limit')
        data['records'].pop(1)
        data['dropped'] = data.get('dropped', 0) + 1


def main():
    if sys.argv[1:] != ['--execute-once']:
        raise SystemExit('Explicit one-session authorization flag required')
    gate = json.loads((OUT/'gpu-preflight.json').read_text())
    assert gate['ok'] and gate['samsungConfirmed'] and gate['previousSuitesMatch']
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(gate['checkedUtc'])).total_seconds()
    assert 0 <= age < 60
    from monitoring.adlx_bridge import real_adapter
    from monitoring.collector import Clock
    from monitoring.windows_native import WindowsReadApi
    import importlib.util
    import os
    import threading
    spec = importlib.util.spec_from_file_location('gpu_resources', ROOT/'scripts/adlx-native-session.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    api = WindowsReadApi()
    api.require_non_elevated()
    adapter = real_adapter(diagnostics=True)
    resources = module.Resources(api, adapter)
    with (OUT/'gpu-session-attempt.json').open('x', encoding='utf-8') as stream:
        json.dump({'startedUtc': datetime.now(timezone.utc).isoformat(), 'maximumSeconds': 90,
                   'plannedCollectionSeconds': 70, 'retryAllowed': False, 'diagnosticsOptIn': True}, stream)
    print('Single instrumented GPU session started.', flush=True)
    with (OUT/'gpu-session-metrics.jsonl').open('x', encoding='utf-8') as stream:
        def save(row):
            stream.write(json.dumps(row, allow_nan=False, separators=(',', ':'))+'\n')
            stream.flush()
        result = run_instrumented(adapter, resources, Clock(), threading.Event().wait, on_row=save)
    diagnostic = result['adapterDiagnostics'].pop('frame_diagnostics', {})
    exported = diagnostic_bytes({'frame_diagnostics': diagnostic})
    with (OUT/'gpu-diagnostics.json').open('xb') as stream: stream.write(exported)
    process = adapter.transport.process
    result.update(bridgePid=process.pid if process else None, collectorPid=os.getpid(),
                  bridgeReturnCode=process.poll() if process else None,
                  bridgeResidual=bool(process and process.poll() is None), ready=adapter.ready,
                  diagnosticRecords=len(diagnostic.get('records', [])), diagnosticFileBytes=len(exported),
                  diagnosticEnabledOnlyInExitedSession=adapter.clean is True,
                  realGpuSession=True, profileUsed=False, networkInterfaceCreated=False,
                  sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'gpu-session-result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: result[k] for k in ('reason','elapsedSeconds','shutdownClean','bridgeResidual','frameCounts','ruleCounts','readAttempts')}), flush=True)
    return 0 if result['shutdownClean'] and not result['bridgeResidual'] and result['reason']=='duration_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
