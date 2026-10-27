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
    return dict(v=1, reason=reason,error=error,elapsed_seconds=now()-started,
        records=records,clean_stop=closed is True,physical=backend.physical,
        repeated=False,forced_shutdown=False)
