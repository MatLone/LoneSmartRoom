"""Opt-in, bounded in-memory diagnostics. No files, native APIs or free-form values.

Only known field names, types, units, numeric time metadata and sensor states survive.
No sensor values, arbitrary keys, exception text, certificates or paths are retained.
"""
import json
import math
from threading import Lock

PROFILE='adlx_frame_diagnostics_v1'
CLOCKS=('uptime_ms','unix_ms','windows_ms')
FRAME_FIELDS=('v','event','timestamp_ms','age_seconds','clock_source','readings')
METRICS=tuple('gpu.adlx.'+name for name in ('utilization','temperature','hotspot_temperature','vram_used_mb','core_clock','power','fan_rpm','vram_total_mb'))
UNITS=dict(zip(METRICS,('percent','celsius','celsius','megabytes','megahertz','watts','rpm','megabytes')))
STATES=frozenset('available unsupported unavailable permission_denied warming_up error stale'.split())
NATIVE_RULES=frozenset(('clock_matched','clock_unmatched','clock_ambiguous','timestamp_negative','reference_range'))
RULES=frozenset('wire_line_limit wire_json wire_duplicate_key wire_nonfinite wire_version wire_object wire_event frame_object frame_required_missing frame_extra_fields frame_version frame_event timestamp_null timestamp_type timestamp_range age_null age_type age_nonfinite age_negative clock_type clock_uncontracted readings_type readings_keys reading_shape reading_state reading_null reading_type reading_nonfinite native_diagnostic_missing native_diagnostic_shape native_diagnostic_rule native_diagnostic_units native_diagnostic_delta native_diagnostic_matches native_diagnostic_conversion native_diagnostic_clock transport_time_nonfinite transport_time_future frame_structure_accepted provider_frame_shape provider_sample_age_limit provider_timestamp_not_advanced provider_reading_invalid provider_vram_inconsistent'.split())
STAGES=frozenset(('wire','frame','time','readings','native_time','transport_time','provider'))


def kind(value):
    t=type(value)
    if value is None:return 'null'
    if t is bool:return 'bool'
    if t is int:return 'int'
    if t is float:return 'float_nan' if math.isnan(value) else 'float_infinite' if not math.isfinite(value) else 'float'
    return {str:'string',dict:'object',list:'array'}.get(t,'other')


def number(value):
    return value if type(value) in (int,float) and abs(value)<=2**63-1 and math.isfinite(value) else None


def convert_time(value,source,target):
    """Diagnostic calculation only; never rewrites a wire timestamp or metric."""
    if number(value) is None:raise ValueError('time_number')
    scales={'seconds':1000,'milliseconds':1}
    if type(source) is not str or type(target) is not str or source not in scales or target not in scales:raise ValueError('time_unit')
    result=value*scales[source]/scales[target]
    if not math.isfinite(result):raise ValueError('time_overflow')
    return result


def temporal_summary(value):
    if type(value) is not dict:return {}
    result={'expected_timestamp_unit':'milliseconds','received_timestamp_unit':'milliseconds_implicit',
        'timestamp_ms':number(value.get('timestamp_ms')),'expected_age_unit':'seconds',
        'age_seconds':number(value.get('age_seconds')),
        'clock_source':value.get('clock_source') if value.get('clock_source') in (*CLOCKS,'fixture','unverified') else 'unknown'}
    native=value.get('diagnostic')
    if type(native) is dict:
        result['received_timestamp_unit']=native.get('timestamp_unit') if native.get('timestamp_unit') in ('milliseconds','seconds') else 'unknown'
        result['native_rule_reported']=native.get('rule') if type(native.get('rule')) is str and native.get('rule') in NATIVE_RULES else 'unknown'
        result['native_age_unit']=native.get('age_unit') if native.get('age_unit') in ('milliseconds','seconds') else 'unknown'
        result['reported_conversion_seconds']=number(native.get('converted_age_seconds'))
        deltas=native.get('deltas_ms')
        result['candidate_deltas_ms']={name:number(deltas.get(name)) for name in CLOCKS} if type(deltas) is dict else {}
        result['candidate_seconds_calculated']={name:None if delta is None else delta/1000
            for name,delta in result['candidate_deltas_ms'].items()}
    return result


class DiagnosticBuffer:
    MAX_RECORDS=16
    MAX_BYTES=32768
    MAX_RECORD_BYTES=4096

    def __init__(self,enabled=False):
        if type(enabled) is not bool:raise ValueError('boolean_required')
        self.enabled=enabled;self._records=[];self._bytes=0;self._dropped=0;self._lock=Lock();self._first_rejection=None

    def emit(self,stage,rule,payload=None,*,field=None,metric=None,transport=None):
        if not self.enabled:return
        # Unknown control strings are discarded, not recorded or formatted.
        if type(stage) is not str or type(rule) is not str or stage not in STAGES or rule not in RULES:return
        value=payload if type(payload) is dict else {}
        record={'v':1,'stage':stage,'rule':rule}
        if field in (*FRAME_FIELDS,'diagnostic','value','state','transport_received_at','transport_now'):
            record['field']=field
        if metric in METRICS:record['metric']=metric
        if type(transport) is dict:
            record['transport_time']={'received_type':kind(transport.get('received')),'now_type':kind(transport.get('now')),
                'queue_age_seconds':number(transport.get('queue_age_seconds')),
                'calculated_age_seconds':number(transport.get('calculated_age_seconds'))}
        if payload is not None:
            record['payload_type']=kind(payload)
            record['field_types']={name:kind(value[name]) if name in value else 'missing' for name in FRAME_FIELDS}
            record['time']=temporal_summary(value)
            sensors=value.get('readings')
            if type(sensors) is dict:
                record['sensors']={}
                for name in METRICS:
                    if name not in sensors:continue
                    sensor=sensors[name]
                    if type(sensor) is dict:
                        state=sensor.get('state')
                        state=state if type(state) is str and state in STATES else 'unknown'
                        record['sensors'][name]={'state':state,'unit':UNITS[name],'value_type':kind(sensor.get('value')),
                            'validity':'unavailable' if state in STATES-{'available'} else 'unvalidated'}
                    else:record['sensors'][name]={'state':'unknown','value_type':kind(sensor),'validity':'invalid_structure'}
        encoded=json.dumps(record,allow_nan=False,separators=(',',':')).encode('utf-8')
        with self._lock:
            if len(encoded)>self.MAX_RECORD_BYTES:
                self._dropped=min(self._dropped+1,2**31-1);return
            if self._first_rejection is None and rule!='frame_structure_accepted':self._first_rejection=encoded
            self._records.append(encoded);self._bytes+=len(encoded)
            while len(self._records)>self.MAX_RECORDS or self._bytes>self.MAX_BYTES:
                index=1 if self._records[0] is self._first_rejection else 0
                removed=self._records.pop(index);self._bytes-=len(removed);self._dropped=min(self._dropped+1,2**31-1)

    def snapshot(self):
        with self._lock:
            return {'enabled':self.enabled,'records':[json.loads(x) for x in self._records],
                    'encodedBytes':self._bytes,'dropped':self._dropped,'persistentFileLogging':False,
                    'retention':'first_rejection_and_recent'}
