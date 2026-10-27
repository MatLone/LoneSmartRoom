"""Public allowlisted metric projection. No paths, process data or credentials."""
from datetime import datetime, timezone
import json
import math
import re

from monitoring.windows_basic import basic_catalog
from monitoring.adlx_provider import GPU_SPECS

MAX_BYTES = 32768
SPECS = {s.metric_id: s for s in (*basic_catalog(('C:\\', 'D:\\')), *GPU_SPECS)}
STATES = frozenset(('available', 'stale', 'warming_up', 'unsupported', 'unavailable', 'permission_denied', 'error'))


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('invalid_number')
    return value


def stamp(value):
    if type(value) is not str or len(value) > 32 or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z', value):
        raise ValueError('invalid_timestamp')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def source_for(key):
    if key.startswith('gpu.'): return 'amd.adlx'
    if key.startswith('cpu.'): return 'win32.systemtimes'
    if key.startswith('ram.'): return 'win32.memory'
    return 'win32.pdh.logicaldisk' if key.endswith(('read_rate', 'write_rate', 'activity')) else 'win32.volume.' + key.split('.')[1]


def limit(key, interval):
    return interval + 1 if key.startswith('gpu.') and not key.endswith('total_mb') else interval * 3


def project(snapshot, *, simulation=False, now=None):
    """Validate before caching, strip unapproved fields. Snapshot time is UTC seconds."""
    now = datetime.now(timezone.utc).timestamp() if now is None else number(now)
    if type(snapshot) is not dict or snapshot.get('schema_version') != 1 or type(snapshot.get('schema_version')) is not int:
        raise ValueError('incompatible_snapshot')
    seq = snapshot.get('sequence')
    if type(seq) is not int or not 0 <= seq <= 2**53 - 1 or snapshot.get('contains_simulated') is not simulation:
        raise ValueError('invalid_provenance')
    generated = stamp(snapshot.get('generated_at'))
    if generated > now or now - generated > 5:
        raise ValueError('expired_snapshot')
    values = snapshot.get('metrics')
    if type(values) is not list or len(values) > len(SPECS): raise ValueError('metric_limit')
    metrics, seen = [], set()
    for raw in values:
        if type(raw) is not dict: raise ValueError('invalid_metric')
        key = raw.get('id'); spec = SPECS.get(key)
        if spec is None or key in seen: raise ValueError('unexpected_metric')
        seen.add(key)
        state, valid, stale = raw.get('state'), raw.get('valid'), raw.get('stale')
        if state not in STATES or type(valid) is not bool or type(stale) is not bool or valid != (state == 'available' and not stale):
            raise ValueError('invalid_state')
        kind, source = raw.get('data_kind'), raw.get('source')
        expected = ('fixture.adlx' if key.startswith('gpu.') else 'fixture.metrics') if simulation else source_for(key)
        if kind not in (('simulated', 'not_collected') if simulation else ('real', 'not_collected')):
            raise ValueError('invalid_provenance')
        if source != expected and not (kind == 'not_collected' and source == 'unconfigured' and not valid):
            raise ValueError('unexpected_source')
        if raw.get('unit') != spec.unit.value: raise ValueError('unexpected_unit')
        interval = raw.get('interval_seconds')
        allowed = [60] if spec.cadence.value == 'capacity' else [2, 10] if key.startswith('gpu.') else [1, 5]
        if interval not in allowed or type(interval) not in (int, float): raise ValueError('invalid_interval')
        age, collected = raw.get('age_seconds'), raw.get('collected_at')
        if age is not None and number(age) < 0: raise ValueError('invalid_age')
        if collected is not None and stamp(collected) > generated: raise ValueError('future_sample')
        if valid and (age is None or collected is None or kind == 'not_collected'): raise ValueError('missing_sample')
        value = raw.get('value')
        if valid: spec.validate_value(value)
        elif value is not None: raise ValueError('null_required')
        ingress = raw.get('ingress_age_seconds')
        if ingress is not None and (not key.startswith('gpu.') or key.endswith('total_mb') or not 0 <= number(ingress) <= 1.5):
            raise ValueError('invalid_adlx_ingress')
        # UTC lag and cache residence count towards age; wall clock never renews a sample.
        age = None if age is None else max(age, generated - stamp(collected)) if collected else age
        metrics.append(dict(id=key, source=source, unit=spec.unit.value, value=value, state=state,
            valid=valid, stale=stale, data_kind=kind, collected_at=collected, age_seconds=age,
            interval_seconds=interval, expires_after_seconds=limit(key, interval), ingress_age_seconds=ingress))
    by_id = {m['id']: m for m in metrics}
    for prefix, parts in [('ram.', ('total', 'used', 'available')), ('storage.c.', ('total', 'used', 'free')), ('storage.d.', ('total', 'used', 'free'))]:
        group = [by_id.get(prefix + k) for k in parts]
        if all(m and m['valid'] for m in group) and len({m['collected_at'] for m in group}) == 1:
            total, used, free = [m['value'] for m in group]
            if total <= 0 or used + free != total: raise ValueError('inconsistent_capacity')
    used, total = by_id.get('gpu.adlx.vram_used_mb'), by_id.get('gpu.adlx.vram_total_mb')
    if total and total['valid'] and (total['value'] <= 0 or used and used['valid'] and used['value'] > total['value']):
        raise ValueError('inconsistent_vram')
    result = dict(schema_version=1, sequence=seq, generated_at=snapshot['generated_at'], contains_simulated=simulation, metrics=metrics)
    if len(json.dumps(result, allow_nan=False).encode()) > MAX_BYTES: raise ValueError('response_limit')
    return result
