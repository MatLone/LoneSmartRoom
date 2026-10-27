"""Bounded orchestration of an injected transport. No hardware/process calls."""
import math


def run_observation(backend, *, now, wait, duration=30):
    if type(duration) not in (int,float) or not math.isfinite(duration) or not 2 <= duration <= 40:
        raise ValueError('invalid_validation_duration')
    started = now(); next_snapshot = started; next_https = started + 1
    records = []; reason = 'observation_complete'; error = None
    try:
        while now() - started < duration:
            if not backend.alive(): reason = 'transport_exited'; break
            if now() >= next_snapshot:
                backend.request_snapshot(); next_snapshot = now() + 1
            backend.drain()
            if now() >= next_https:
                record = backend.read_telemetry()
                if type(record) is not dict or record.get('ok') is not True:
                    reason = 'read_failed'; break
                records.append(record); next_https = now() + 2
            wait(.05)
    except Exception:
        reason = 'validation_error'; error = 'isolated_transport_failed'
    finally:
        # Only owned stdio EOF; never terminate/kill a process or restart a source.
        closed = backend.close()
    snapshots=[(r,r['body']['snapshot']) for r in records if type(r.get('body')) is dict and r['body'].get('snapshot') is not None]
    valid_ids={m['id'] for receipt,s in snapshots for m in s.get('metrics',[]) if m.get('valid') is True
        and m.get('stale') is False and m.get('value') is not None and type(m.get('age_seconds')) in (int,float)
        and type(receipt.get('transport_seconds',0)) in (int,float) and math.isfinite(receipt.get('transport_seconds',0))
        and receipt.get('transport_seconds',0)>=0 and m['age_seconds']+receipt.get('transport_seconds',0)<m.get('expires_after_seconds',0)}
    required={'cpu.utilization','ram.total','ram.used','ram.available','storage.c.total','storage.d.total',
              'gpu.adlx.utilization','gpu.adlx.temperature'}
    return dict(v=1, reason=reason,error=error,elapsed_seconds=now()-started,
        records=records,clean_stop=closed is True,physical=backend.physical,
        snapshots_received=len(snapshots),valid_metric_ids=sorted(valid_ids),
        transport_validated=closed is True and reason=='observation_complete' and required<=valid_ids,
        repeated=False,forced_shutdown=False)
