"""Bounded basic session orchestration, injected API/clock. No native construction."""
from collections import Counter
import math
import statistics
import threading

from .collector import Collector
from .contracts import Availability as A, ContractError, finite, utc_text
from .windows_basic import CpuProvider, DiskIoProvider, MemoryProvider, VolumeProvider, basic_catalog


def stats(values):
    values = list(values)
    return {'count': len(values), 'min': min(values), 'mean': statistics.fmean(values),
            'max': max(values)} if values else {'count': 0, 'min': None, 'mean': None, 'max': None}


def resource_sample(current, previous, elapsed, processors):
    if type(processors) is not int or not 1 <= processors <= 4096 or not 0 <= finite(elapsed):
        raise ContractError('invalid_resource_interval')
    cpu = current['cpu_seconds']
    if type(cpu) not in (int, float) or not math.isfinite(cpu) or cpu < 0:
        raise ContractError('invalid_process_cpu')
    for key in ('working_set_bytes', 'private_commit_bytes'):
        if type(current[key]) is not int or current[key] < 0:
            raise ContractError('invalid_process_memory')
    percent = None
    if previous is not None and elapsed > 0 and cpu >= previous['cpu_seconds']:
        percent = (cpu - previous['cpu_seconds']) * 100 / elapsed / processors
    return {**current, 'cpu_percent_total_normalized': percent}


def summarize(rows):
    unique, states, sample_times = {}, {}, {}
    for row in rows:
        for metric in row['snapshot']['metrics']:
            key = metric['id']
            stamp = metric['collected_at']
            identity = (key, stamp)
            if identity in unique:
                continue  # Capacity samples repeated in snapshots are not new readings.
            unique[identity] = metric
            states.setdefault(key, Counter())[metric['state']] += 1
            sample_times.setdefault(key, []).append((stamp, row['elapsed_seconds'] - (metric['age_seconds'] or 0)))
    result = {}
    for key, counts in states.items():
        metrics = [v for (mid, _stamp), v in unique.items() if mid == key]
        valid = [v['value'] for v in metrics if v['valid']]
        times = [t for stamp, t in sample_times[key] if stamp is not None]
        result[key] = {'unit': metrics[0]['unit'], 'source': metrics[0]['source'],
                       'values': stats(valid), 'states': dict(counts),
                       'interval_seconds': stats(b - a for a, b in zip(times, times[1:])),
                       'first_collected_at': metrics[0]['collected_at'],
                       'last_collected_at': metrics[-1]['collected_at']}
    return result


def run_session(api, volumes, clock, wait, *, duration=80):
    if not 0 < finite(duration) <= 85:
        raise ContractError('invalid_session_duration')
    specs = basic_catalog(volumes)
    cpu, memory = CpuProvider(api), MemoryProvider(api)
    providers = [cpu, memory] + [VolumeProvider(api, root) for root in volumes]
    if volumes:
        providers.append(DiskIoProvider(api, volumes))
    collector = Collector(specs, providers, clock=clock)
    processors = api.logical_processors()
    if type(processors) is not int or not 1 <= processors <= 4096:
        raise ContractError('invalid_processor_count')
    started, started_at = clock.monotonic(), clock.utcnow()
    rows, reason = [], 'duration_complete'
    previous_resource = None
    previous_resource_at = None
    base_resource = api.own_resources()
    last_resource = base_resource
    try:
        while clock.monotonic() - started < duration:
            cycle = clock.monotonic()
            collector.step()
            now = clock.monotonic()
            snapshot = collector.cache.snapshot(now, clock.utcnow())
            current_resource = api.own_resources()
            resource_at = clock.monotonic()
            own = resource_sample(current_resource, previous_resource,
                                  resource_at - previous_resource_at if previous_resource_at is not None else 0,
                                  processors)
            own['collected_at'] = utc_text(clock.utcnow())
            previous_resource, previous_resource_at = current_resource, resource_at
            last_resource = current_resource
            rows.append({'elapsed_seconds': now - started, 'snapshot': snapshot, 'collector_resources': own,
                         'cycle_seconds': clock.monotonic() - cycle, 'cache_samples': collector.cache.sample_count})
            if (any(m['state'] in (A.ERROR, A.PERMISSION_DENIED) for m in snapshot['metrics']
                    if m['id'] == 'cpu.utilization' or m['id'].startswith('ram.'))
                    or any(e['code'] == 'collector_failed' for e in collector.diagnostics())):
                reason = 'basic_read_failed'
                break
            if len(rows) >= 90:
                reason = 'row_limit'
                break
            remaining = duration - (clock.monotonic() - started)
            if remaining > 0:
                wait(min(remaining, max(0, cycle + 1 - clock.monotonic())))
    except KeyboardInterrupt:
        reason = 'interrupted'
    except Exception:
        reason = 'session_failed'
    finally:
        stopped = collector.stop(3)
    elapsed = clock.monotonic() - started
    last_resource = api.own_resources()
    resource_window = clock.monotonic() - started
    process_cpu = last_resource['cpu_seconds'] - base_resource['cpu_seconds']
    average_cpu = process_cpu * 100 / resource_window / processors if resource_window > 0 and process_cpu >= 0 else None
    report = {'started_at': utc_text(started_at), 'ended_at': utc_text(clock.utcnow()),
              'requested_seconds': duration, 'elapsed_seconds': elapsed, 'reason': reason,
              'metric_slots': len(specs), 'max_cache_samples': len(specs) * 120,
              'final_cache_samples': collector.cache.sample_count, 'logical_processors': processors,
              'rows': rows, 'metrics': summarize(rows), 'diagnostics': list(collector.diagnostics()),
              'stop': {'stopped': stopped.stopped, 'clean': stopped.clean, 'timed_out': stopped.timed_out},
              'monitoring_threads_remaining': [t.name for t in threading.enumerate()
                                               if t.name.startswith('LoneMonitoring')],
              'collector_resources': {'average_cpu_percent_total_normalized': average_cpu,
                                      'measured_cpu_seconds': process_cpu,
                                      'resource_window_seconds': resource_window,
                                      'cpu_goal_percent': 0.5,
                                      'cpu_goal_met': average_cpu < 0.5 if average_cpu is not None else None,
                                      'working_set_bytes': stats(r['collector_resources']['working_set_bytes'] for r in rows),
                                      'private_commit_bytes': stats(r['collector_resources']['private_commit_bytes'] for r in rows)},
              'cycle_seconds': stats(r['cycle_seconds'] for r in rows)}
    return report
