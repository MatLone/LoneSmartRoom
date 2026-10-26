from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import math
import time
import unittest
from unittest.mock import patch

from monitoring.adlx_bridge import BridgeError,LineTransport,NativeAdapter,decode,launch_native
from monitoring.adlx_diagnostics import DiagnosticBuffer,convert_time,FRAME_FIELDS
from monitoring.adlx_provider import AdlxProvider,GPU_SPECS
from monitoring.collector import Collector,Schedule
from monitoring.contracts import DataKind
from monitoring_fakes import FakeClock
from adlx_diagnostic_fakes import frame,unmatched,adapter
from test_adlx_bridge import mock_process


class DiagnosticTests(unittest.TestCase):
    def reject(self,value,rule,*,stage=None):
        a=adapter([value]);self.addCleanup(a.close)
        with self.assertRaises(BridgeError) as result:a.latest('amd-rx6750xt')
        self.assertEqual(result.exception.rule,rule)
        if stage:self.assertEqual(result.exception.stage,stage)
        record=a.diagnostics()['frame_diagnostics']['records'][-1];self.assertEqual(record['rule'],rule)
        return record

    def test_utc_ms_valid_without_local_offset(self):
        utc=datetime(2026,10,25,17,0,tzinfo=timezone.utc);local=utc.astimezone(timezone(timedelta(hours=-3)))
        self.assertEqual(utc.timestamp(),local.timestamp())
        value=frame(stamp=int(utc.timestamp()*1000));a=adapter([value]);self.addCleanup(a.close)
        self.assertEqual(a.latest('amd-rx6750xt').sdk_timestamp_ms,value['timestamp_ms'])

    def test_uptime_is_valid_only_with_explicitly_contracted_clock(self):
        a=adapter([frame(clock='uptime_ms',stamp=10000)]);self.addCleanup(a.close)
        self.assertEqual(a.latest('amd-rx6750xt').sdk_timestamp_ms,10000)
        value=frame(clock='monotonic_arbitrary');self.reject(value,'clock_uncontracted',stage='time')

    def test_future_sdk_time_not_clamped_to_zero(self):
        record=self.reject(unmatched(stamp=10001,delta=-1),'age_null')
        self.assertEqual(record['time']['candidate_deltas_ms']['uptime_ms'],-1)
        self.assertEqual(record['time']['native_rule_reported'],'clock_unmatched')

    def test_old_sample_keeps_existing_provider_limit(self):
        a=adapter([frame(age=2)]);self.addCleanup(a.close)
        c=Collector(GPU_SPECS,[AdlxProvider(a,'amd-rx6750xt')],schedule=Schedule(read_budget=1));c.step()
        m=next(x for x in c.snapshot()['metrics'] if x['id']=='gpu.adlx.utilization')
        self.assertFalse(m['valid']);self.assertIsNone(m['value']);c.stop()
        self.assertEqual(a.diagnostics()['frame_diagnostics']['records'][-1]['rule'],'provider_sample_age_limit')

    def test_seconds_milliseconds_explicit_conversion_is_diagnostic_only(self):
        self.assertEqual(convert_time(1.25,'seconds','milliseconds'),1250)
        self.assertEqual(convert_time(1250,'milliseconds','seconds'),1.25)
        self.assertEqual(convert_time(0,'milliseconds','seconds'),0)
        for value in (True,float('nan'),float('inf'),10**1000):
            with self.assertRaises(ValueError):convert_time(value,'seconds','milliseconds')
        with self.assertRaises(ValueError):convert_time(1,'ticks','seconds')

    def test_received_seconds_are_not_silently_reinterpreted_as_ms(self):
        value=frame();value['diagnostic']['timestamp_unit']='seconds'
        record=self.reject(value,'native_diagnostic_units');self.assertEqual(record['time']['received_timestamp_unit'],'seconds')

    def test_missing_timestamp_and_null_are_different(self):
        value=frame();del value['timestamp_ms'];r=self.reject(value,'frame_required_missing');self.assertEqual(r['field'],'timestamp_ms')
        value=frame();value['timestamp_ms']=None;r=self.reject(value,'timestamp_null');self.assertEqual(r['field_types']['timestamp_ms'],'null')

    def test_first_zero_timestamp_unmatched_remains_rejected_then_recovers(self):
        a=adapter([unmatched(),frame()]);self.addCleanup(a.close)
        with self.assertRaises(BridgeError) as result:a.latest('amd-rx6750xt')
        self.assertEqual(result.exception.rule,'age_null');self.assertEqual(a.latest('amd-rx6750xt').readings['gpu.adlx.utilization'].value,12.5)
        self.assertEqual(a.transport.starts,1)

    def test_zero_timestamp_can_be_valid_when_uptime_origin_is_explicit(self):
        a=adapter([frame(clock='uptime_ms',stamp=0,age=0)]);self.addCleanup(a.close)
        self.assertEqual(a.latest('amd-rx6750xt').sdk_timestamp_ms,0)

    def test_partial_and_all_unavailable_never_become_zero(self):
        for all_missing in (False,True):
            value=frame();selected=list(value['readings']) if all_missing else ['gpu.adlx.temperature']
            for key in selected:value['readings'][key]={'state':'unavailable','value':None}
            a=adapter([value]);self.addCleanup(a.close);f=a.latest('amd-rx6750xt')
            for key in selected:self.assertIsNone(f.readings[key].value)

    def test_zero_sensor_value_valid_and_absence_distinct(self):
        value=frame();value['readings']['gpu.adlx.utilization']['value']=0
        a=adapter([value]);self.addCleanup(a.close);f=a.latest('amd-rx6750xt')
        self.assertEqual(f.readings['gpu.adlx.utilization'].value,0);self.assertEqual(f.readings['gpu.adlx.fan_rpm'].value,0)

    def test_sensor_nonfinite_has_precise_readings_rule(self):
        for number in (float('nan'),float('inf'),float('-inf'),10**1000):
            value=frame();value['readings']['gpu.adlx.utilization']['value']=number
            self.reject(value,'reading_nonfinite',stage='readings')

    def test_nan_infinite_json_and_exponent_overflow_rejected_at_wire(self):
        for literal in ('NaN','Infinity','-Infinity','1e999'):
            log=DiagnosticBuffer(True)
            with self.assertRaises(BridgeError) as r:decode(('{"v":1,"event":"frame","age_seconds":'+literal+'}\n').encode(),log)
            self.assertEqual(r.exception.rule,'wire_nonfinite');self.assertEqual(log.snapshot()['records'][-1]['stage'],'wire')

    def test_all_required_fields_missing_have_structured_rules(self):
        for field in FRAME_FIELDS:
            value=frame();del value[field];record=self.reject(value,'frame_required_missing')
            self.assertEqual(record['field'],field)

    def test_contract_version_incompatible_wire_and_frame(self):
        with self.assertRaises(BridgeError) as r:decode(b'{"v":2,"event":"frame"}\n',DiagnosticBuffer(True))
        self.assertEqual(r.exception.rule,'wire_version')
        value=frame();value['v']=2;self.reject(value,'frame_version')

    def test_age_types_units_null_negative_and_nonfinite(self):
        for age,rule in [(None,'age_null'),('100','age_type'),(True,'age_type'),(-.1,'age_negative'),(float('inf'),'age_nonfinite'),(float('nan'),'age_nonfinite')]:
            value=frame();value['age_seconds']=age;self.reject(value,rule)

    def test_timestamp_types_and_bounds(self):
        for stamp,rule in [(True,'timestamp_type'),(1.25,'timestamp_type'),('2026-10-25T17:00Z','timestamp_type'),(-1,'timestamp_range'),(2**63,'timestamp_range')]:
            value=frame();value['timestamp_ms']=stamp;self.reject(value,rule)

    def test_invalid_conversion_result_and_candidate_counts(self):
        value=frame();value['diagnostic']['converted_age_seconds']=100;self.reject(value,'native_diagnostic_conversion')
        value=frame();value['diagnostic']['match_count']=2;self.reject(value,'native_diagnostic_matches')
        value=frame();value['diagnostic']['deltas_ms']['unix_ms']='100';self.reject(value,'native_diagnostic_delta')

    def test_valid_invalid_sequence_recovers_without_restarting(self):
        bad=frame();bad['clock_source']='unknown'
        a=adapter([frame(stamp=100),bad,frame(stamp=200),unmatched(),frame(stamp=300)]);self.addCleanup(a.close)
        outcomes=[]
        for _ in range(5):
            try:outcomes.append(a.latest('amd-rx6750xt').sdk_timestamp_ms)
            except BridgeError as exc:outcomes.append(exc.rule)
        self.assertEqual(outcomes,[100,'clock_uncontracted',200,'age_null',300]);self.assertEqual(a.transport.starts,1)

    def test_default_diagnostics_off_and_legacy_message_unchanged(self):
        value=frame(clock='fixture',diagnostics=False);a=adapter([value],diagnostics=False);self.addCleanup(a.close)
        a.latest('amd-rx6750xt');self.assertNotIn('frame_diagnostics',a.diagnostics())
        self.assertEqual(a._diagnostic.snapshot()['records'],[])
        self.assertEqual(set(value),set(FRAME_FIELDS))

    def test_unknown_fields_paths_and_values_never_appear_in_diagnostics(self):
        marker='fixture-sensitive-not-for-log';value=frame();value[marker]=marker
        r=self.reject(value,'frame_extra_fields');self.assertNotIn(marker,json.dumps(r))
        value=frame();value['clock_source']=marker;r=self.reject(value,'clock_uncontracted');self.assertEqual(r['time']['clock_source'],'unknown')
        value=frame();value['readings'][marker]={'state':marker,'value':marker}
        r=self.reject(value,'readings_keys');self.assertNotIn(marker,json.dumps(r))

    def test_native_free_text_is_not_logged(self):
        value=frame();value['diagnostic']['rule']=['fixture-sensitive-not-for-log']
        r=self.reject(value,'native_diagnostic_rule');self.assertNotIn('fixture-sensitive-not-for-log',json.dumps(r))

    def test_log_memory_limits_and_no_file_io(self):
        disabled=DiagnosticBuffer();disabled.emit('frame','frame_structure_accepted',frame());self.assertEqual(disabled.snapshot()['encodedBytes'],0)
        log=DiagnosticBuffer(True)
        with patch('builtins.open',side_effect=AssertionError('No file logs')):
            for _ in range(1000):log.emit('frame','frame_structure_accepted',frame())
        result=log.snapshot();self.assertLessEqual(len(result['records']),16);self.assertLessEqual(result['encodedBytes'],32768)
        self.assertGreater(result['dropped'],0);self.assertFalse(result['persistentFileLogging'])

    def test_native_mock_emits_opt_in_diagnostic_and_exact_null_age_rule(self):
        a=NativeAdapter(LineTransport(lambda:mock_process('unverified',True)),data_kind=DataKind.SIMULATED,diagnostics=True)
        self.addCleanup(a.close);a.open()
        with self.assertRaises(BridgeError) as r:a.latest('amd-rx6750xt')
        self.assertEqual(r.exception.rule,'age_null');record=a.diagnostics()['frame_diagnostics']['records'][-1]
        self.assertEqual(record['time']['native_rule_reported'],'clock_unmatched');self.assertEqual(record['time']['timestamp_ms'],12000)

    def test_native_mock_valid_opt_in_probe(self):
        a=NativeAdapter(LineTransport(lambda:mock_process('normal',True)),data_kind=DataKind.SIMULATED,diagnostics=True)
        self.addCleanup(a.close);a.open();self.assertEqual(a.latest('amd-rx6750xt').readings['gpu.adlx.utilization'].value,12.5)

    def test_native_launcher_opt_in_is_one_fixed_flag(self):
        with patch('monitoring.adlx_bridge.subprocess.Popen') as popen:
            launch_native(diagnostics=True);self.assertEqual(popen.call_args.args[0][-1],'--diagnostics')
        with self.assertRaises(Exception):launch_native(diagnostics='arbitrary')

    def test_future_transport_receipt_rejected_instead_of_age_zero_clamp(self):
        a=adapter([frame()]);self.addCleanup(a.close);a.transport.received_at=20
        with patch('monitoring.adlx_bridge.time.monotonic',return_value=10):
            with self.assertRaises(BridgeError) as r:a.latest('amd-rx6750xt')
        self.assertEqual(r.exception.rule,'transport_time_future')
        record=a.diagnostics()['frame_diagnostics']['records'][-1]
        self.assertEqual(record['transport_time']['queue_age_seconds'],-10)

    def test_nonfinite_transport_clock_not_published_or_logged_as_number(self):
        for received in (float('nan'),float('inf'),True,10**1000):
            a=adapter([frame()]);self.addCleanup(a.close);a.transport.received_at=received
            with self.assertRaises(BridgeError) as r:a.latest('amd-rx6750xt')
            self.assertEqual(r.exception.rule,'transport_time_nonfinite')
            json.dumps(a.diagnostics(),allow_nan=False)

    def test_queue_age_is_added_without_weakening_provider_freshness(self):
        a=adapter([frame()]);self.addCleanup(a.close);a.transport.received_at=10
        c=Collector(GPU_SPECS,[AdlxProvider(a,'amd-rx6750xt')],clock=FakeClock())
        with patch('monitoring.adlx_bridge.time.monotonic',return_value=12):c.step()
        metric=next(m for m in c.snapshot()['metrics'] if m['id']=='gpu.adlx.utilization')
        self.assertFalse(metric['valid']);self.assertIsNone(metric['value']);c.stop()
        self.assertEqual(a.diagnostics()['frame_diagnostics']['records'][-1]['rule'],'provider_sample_age_limit')

    def test_transport_error_can_recover_on_next_valid_frame_without_restart(self):
        a=adapter([frame(stamp=100),frame(stamp=200)]);self.addCleanup(a.close);a.transport.received_at=20
        with patch('monitoring.adlx_bridge.time.monotonic',return_value=10):
            with self.assertRaises(BridgeError):a.latest('amd-rx6750xt')
        a.transport.received_at=30
        with patch('monitoring.adlx_bridge.time.monotonic',return_value=30):self.assertEqual(a.latest('amd-rx6750xt').sdk_timestamp_ms,200)
        self.assertEqual(a.transport.starts,1)


if __name__=='__main__':unittest.main()
