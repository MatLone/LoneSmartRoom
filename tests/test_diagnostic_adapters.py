"""Receipt-shaped mocks, no operational connection or sensor is used."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from itertools import repeat
import json
from pathlib import Path
import unittest

from diagnostics.contracts import Component as C, DetailCode as D, DiagnosticError
from diagnostics.engine import DiagnosticEngine
from diagnostics.evidence import ReceiptFrame, FixtureReader, decode
from diagnostics.adapters import ReceiptProvider
from diagnostics.presentation import present, render_html
from diagnostics.scenarios import NOW, receipt, status_payload, monitoring_payload, startup_payload, mixed_review


def row(report,c):return next(r for r in report['checks'] if r['component']==c.value)
def reduce(c,p,**kw):
    return row(DiagnosticEngine([ReceiptProvider(c,FixtureReader([receipt(p,**kw)]))]).collect(kw.get('now',NOW),kw.get('monotonic',100),p.get('mode','active')),c)


class EvidenceBoundaryTests(unittest.TestCase):
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(DiagnosticError):decode(b'{"schema_version":1,"schema_version":1}')

    def test_nonfinite_and_non_utf8_rejected(self):
        for raw in (b'{"x":NaN}',b'{"x":Infinity}',b'{"x":-Infinity}',b'\xff',b'[]'):
            with self.subTest(raw=raw),self.assertRaises(DiagnosticError):decode(raw)

    def test_size_limit_and_infinite_reader_queue(self):
        with self.assertRaises(DiagnosticError):ReceiptFrame(NOW,100,b'x'*32769)
        with self.assertRaises(DiagnosticError):FixtureReader(repeat(None))

    def test_readers_are_fixture_only_and_no_url_or_command_input(self):
        with self.assertRaises(DiagnosticError):ReceiptProvider(C.HTTPS,object())
        with self.assertRaises(DiagnosticError):replace(receipt(status_payload()),evidence_kind='real')
        with self.assertRaises(DiagnosticError):decode(b'"https://not-an-endpoint"')

    def test_unsupported_schema_or_extra_private_fields_fail_safely(self):
        for p in (status_payload(schema_version=2),status_payload(schema_version=True),status_payload(private_path='private fixture')):
            r=reduce(C.HTTPS,p);self.assertFalse(r['valid']);self.assertEqual(r['code'],'provider_failure')

    def test_exceptions_do_not_leak_text_and_no_retry(self):
        reader=FixtureReader([RuntimeError('private fixture payload')]);e=DiagnosticEngine([ReceiptProvider(C.HTTPS,reader)])
        r=e.collect(NOW,100);self.assertEqual(reader.reads,1);self.assertNotIn('private fixture',json.dumps(r))
        self.assertEqual(present(r)['cards'][0]['label'],'Falha')

    def test_null_reader_does_not_renew_observation(self):
        reader=FixtureReader([receipt(status_payload()),None]);e=DiagnosticEngine([ReceiptProvider(C.HTTPS,reader)])
        first=row(e.collect(NOW,100),C.HTTPS);last=row(e.collect(NOW+timedelta(seconds=11),111),C.HTTPS)
        self.assertEqual(last['state'],'stale');self.assertEqual(first['last_communication'],last['last_communication'])

    def test_new_detail_code_is_fixed_enum(self):
        from diagnostics.simulated import healthy_fixture
        with self.assertRaises(DiagnosticError):replace(healthy_fixture(C.CPU,NOW,100),detail_code='private text')


class HttpsAndPipeTests(unittest.TestCase):
    def test_https_requires_all_tls_hostname_pin_hmac_and_200(self):
        self.assertEqual(reduce(C.HTTPS,status_payload())['state'],'healthy')
        for key in ('tls_verified','hostname_verified','pin_verified','hmac_request_used'):
            r=reduce(C.HTTPS,status_payload(**{key:False}));self.assertEqual(r['state'],'error')
            self.assertIsNone(r['last_communication'])

    def test_auth_failures_and_http_errors_are_distinct(self):
        for code in (401,403):self.assertEqual(reduce(C.HTTPS,status_payload(http_status=code))['detail_code'],D.AUTH_FAILED.value)
        self.assertEqual(reduce(C.HTTPS,status_payload(http_status=503))['detail_code'],D.HTTP_FAILED.value)

    def test_connection_timeout_is_not_pc_off(self):
        p=status_payload(result='timeout',http_status=None)
        e=DiagnosticEngine([ReceiptProvider(C.HTTPS,FixtureReader([receipt(p)]))]);r=e.collect(NOW,100)
        self.assertEqual(row(r,C.HTTPS)['state'],'offline');self.assertEqual(r['power_state'],'unknown')

    def test_tampered_methods_endpoints_and_boolean_types_rejected(self):
        for p in (status_payload(method='POST'),status_payload(endpoint='/v2/apps'),status_payload(pin_verified=1),status_payload(http_status=True)):
            self.assertEqual(reduce(C.HTTPS,p)['code'],'provider_failure')

    def test_tls_rejected_never_accepted_even_if_flags_contradict(self):
        self.assertEqual(reduce(C.HTTPS,status_payload(result='tls_rejected'))['detail_code'],D.TLS_FAILED.value)

    def test_listener_identity_needs_more_than_presence(self):
        p=dict(schema_version=1,port=8776,present=True,image_verified=True,creation_verified=True,parent_verified=False)
        self.assertEqual(reduce(C.LISTENER,p)['state'],'error')
        p['parent_verified']=True;self.assertEqual(reduce(C.LISTENER,p)['state'],'healthy')
        p['port']=443;self.assertEqual(reduce(C.LISTENER,p)['code'],'provider_failure')

    def pipe(self,**changes):
        return dict(schema_version=1,connected=True,local=True,sid_verified=True,session_verified=True,server_identity_verified=True,contract_version=1,result='ok')|changes

    def test_pipe_peer_identity_session_and_locality_required(self):
        self.assertEqual(reduce(C.IPC,self.pipe())['state'],'healthy')
        for key in ('local','sid_verified','session_verified','server_identity_verified'):
            self.assertEqual(reduce(C.IPC,self.pipe(**{key:False}))['state'],'error')

    def test_pipe_disconnect_contract_limits_and_recovery(self):
        self.assertEqual(reduce(C.IPC,self.pipe(result='timeout'))['state'],'offline')
        self.assertEqual(reduce(C.IPC,self.pipe(contract_version=2))['detail_code'],D.PIPE_CONTRACT_FAILED.value)
        for value in ('rate_limit','size_limit','invalid_frame'):
            self.assertEqual(reduce(C.IPC,self.pipe(result=value))['detail_code'],D.PIPE_LIMIT.value)
        frames=[receipt(self.pipe(result='disconnected')),receipt(self.pipe(),now=NOW+timedelta(seconds=1),monotonic=101)]
        e=DiagnosticEngine([ReceiptProvider(C.IPC,FixtureReader(frames))]);e.collect(NOW,100)
        self.assertEqual(row(e.collect(NOW+timedelta(seconds=1),101),C.IPC)['state'],'healthy')


class MetricReceiptTests(unittest.TestCase):
    def test_zero_cpu_is_valid_and_not_missing(self):
        p=monitoring_payload(C.CPU);self.assertEqual(p['snapshot']['metrics'][0]['value'],0)
        self.assertEqual(reduce(C.CPU,p)['state'],'healthy')

    def test_ram_consistency_and_null_not_zero(self):
        p=monitoring_payload(C.RAM);self.assertEqual(reduce(C.RAM,p)['state'],'healthy')
        p['snapshot']['metrics'][1]['value']=0
        self.assertEqual(reduce(C.RAM,p)['state'],'error')
        p=monitoring_payload(C.CPU,state='unavailable');self.assertIsNone(p['snapshot']['metrics'][0]['value'])
        self.assertEqual(reduce(C.CPU,p)['state'],'unavailable')

    def test_warming_and_error_are_distinct(self):
        self.assertEqual(reduce(C.CPU,monitoring_payload(C.CPU,state='warming_up'))['detail_code'],D.METRICS_WARMING.value)
        self.assertEqual(reduce(C.CPU,monitoring_payload(C.CPU,state='error'))['state'],'error')

    def test_cpu_expiry_and_cache_query_preserve_sample_age(self):
        stale=reduce(C.CPU,monitoring_payload(C.CPU,age=4))
        self.assertEqual(stale['state'],'stale');self.assertEqual(stale['age_seconds'],4)
        self.assertEqual(stale['observed_at'],(NOW-timedelta(seconds=4)).isoformat(timespec='milliseconds').replace('+00:00','Z'))
        r=reduce(C.CPU,monitoring_payload(C.CPU,age=2));self.assertEqual(r['age_seconds'],2)

    def test_inactive_cpu_ram_follow_existing_five_second_cadence(self):
        for c in (C.CPU,C.RAM):
            r=reduce(c,monitoring_payload(c,age=10,mode='inactive'))
            self.assertEqual(r['state'],'healthy');self.assertEqual(r['freshness_seconds'],15)
            self.assertEqual(reduce(c,monitoring_payload(c,age=15,mode='inactive'))['state'],'stale')

    def test_gpu_active_and_inactive_expiration_not_relaxed(self):
        for mode,age,state in [('active',2.9,'healthy'),('active',3,'stale'),('inactive',10.9,'healthy'),('inactive',11,'stale')]:
            self.assertEqual(reduce(C.GPU,monitoring_payload(C.GPU,age=age,mode=mode))['state'],state)

    def test_cached_gpu_expires_exactly_at_three_and_eleven_without_new_frame(self):
        for mode,initial,limit in [('active',2,3),('inactive',10,11)]:
            p=monitoring_payload(C.GPU,age=initial,mode=mode)
            e=DiagnosticEngine([ReceiptProvider(C.GPU,FixtureReader([receipt(p)]))])
            self.assertTrue(row(e.collect(NOW,100,mode),C.GPU)['valid'])
            self.assertEqual(row(e.snapshot(NOW+timedelta(seconds=1),101,mode),C.GPU)['state'],'stale')

    def test_snapshot_delivery_delay_counts_toward_age(self):
        p=monitoring_payload(C.CPU)
        r=reduce(C.CPU,p,now=NOW+timedelta(seconds=4),monotonic=104)
        self.assertEqual(r['state'],'stale')

    def test_future_generated_and_collected_times_rejected(self):
        for key in ('generated','collected'):
            p=monitoring_payload(C.CPU)
            if key=='generated':p['snapshot']['generated_at']=(NOW+timedelta(seconds=1)).isoformat()
            else:p['snapshot']['metrics'][0]['collected_at']=(NOW+timedelta(seconds=1)).isoformat()
            self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')

    def test_gpu_partial_support_and_all_unsupported_are_distinct(self):
        p=monitoring_payload(C.GPU);m=p['snapshot']['metrics'][-1]
        m.update(state='unsupported',valid=False,value=None);m.pop('ingress_age_seconds');m.pop('information_age_seconds')
        self.assertEqual(reduce(C.GPU,p)['detail_code'],D.METRICS_PARTIAL.value)
        self.assertEqual(reduce(C.GPU,monitoring_payload(C.GPU,state='unsupported'))['state'],'unsupported')

    def test_static_vram_alone_does_not_prove_dynamic_gpu_healthy(self):
        p=monitoring_payload(C.GPU,state='unsupported')
        total=next(m for m in p['snapshot']['metrics'] if m['id'].endswith('total_mb'))
        total.update(state='available',valid=True,value=12288)
        self.assertEqual(reduce(C.GPU,p)['state'],'unsupported')

    def test_gpu_ingress_missing_or_over_limit_is_rejected(self):
        for ingress in (None,1.5001,float('nan'),float('inf')):
            p=monitoring_payload(C.GPU);m=p['snapshot']['metrics'][0]
            if ingress is None:m.pop('ingress_age_seconds')
            elif ingress in (float('inf'),):
                raw=json.dumps(p).replace('"ingress_age_seconds": 0.25','"ingress_age_seconds": Infinity',1).encode()
                r=DiagnosticEngine([ReceiptProvider(C.GPU,FixtureReader([ReceiptFrame(NOW,100,raw)]))]).collect(NOW,100)
                self.assertFalse(row(r,C.GPU)['valid']);continue
            else:
                if ingress!=ingress:continue  # Explicit raw NaN is covered by decoder test.
                m['ingress_age_seconds']=ingress
            self.assertFalse(reduce(C.GPU,p)['valid'])

    def test_invalid_values_units_sources_and_real_data_rejected(self):
        for update in ({'value':-1},{'unit':'bytes'},{'source':'private source'},{'data_kind':'real'},{'value':101},{'value':True}):
            p=monitoring_payload(C.CPU);p['snapshot']['metrics'][0].update(update)
            self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')

    def test_unavailable_numeric_zero_is_rejected(self):
        p=monitoring_payload(C.CPU,state='unavailable');p['snapshot']['metrics'][0]['value']=0
        self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')

    def test_duplicate_missing_unknown_and_excess_metrics(self):
        p=monitoring_payload(C.CPU);p['snapshot']['metrics']*=2
        self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')
        p=monitoring_payload(C.CPU);p['snapshot']['metrics']=[];p['snapshot']['contains_simulated']=False
        self.assertEqual(reduce(C.CPU,p)['state'],'unavailable')
        p=monitoring_payload(C.CPU);p['snapshot']['metrics'][0]['id']='arbitrary.metric'
        self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')
        p=monitoring_payload(C.CPU);p['snapshot']['metrics']*=65
        self.assertEqual(reduce(C.CPU,p)['code'],'provider_failure')

    def test_restore_pending_hides_even_otherwise_fresh_gpu_health(self):
        p=monitoring_payload(C.GPU);p['resume_pending']=True
        self.assertEqual(reduce(C.GPU,p)['detail_code'],D.AWAITING_FRESH.value)
        self.assertEqual(reduce(C.GPU,p)['state'],'unavailable')

    def test_invalid_frame_then_new_valid_sample_recovers(self):
        bad=monitoring_payload(C.CPU);bad['snapshot']['metrics'][0]['value']=101
        new=monitoring_payload(C.CPU,now=NOW+timedelta(seconds=1))
        e=DiagnosticEngine([ReceiptProvider(C.CPU,FixtureReader([receipt(bad),receipt(new,now=NOW+timedelta(seconds=1),monotonic=101)]))])
        self.assertFalse(row(e.collect(NOW,100),C.CPU)['valid'])
        self.assertEqual(row(e.collect(NOW+timedelta(seconds=1),101),C.CPU)['state'],'healthy')


class AdlxAndStartupTests(unittest.TestCase):
    def adlx(self,**changes):return dict(schema_version=1,running=True,library_verified=True,last_frame='valid',ingress_age_seconds=1.5,sample_age_seconds=0)|changes

    def test_adlx_valid_and_age_policy(self):
        self.assertEqual(reduce(C.ADLX,self.adlx())['state'],'healthy')
        self.assertFalse(reduce(C.ADLX,self.adlx(ingress_age_seconds=1.5001))['valid'])
        self.assertEqual(reduce(C.ADLX,self.adlx(sample_age_seconds=4))['state'],'stale')

    def test_adlx_rejected_first_frame_not_healthy_and_no_restart(self):
        p=self.adlx(last_frame='invalid_frame',ingress_age_seconds=None,sample_age_seconds=None)
        self.assertEqual(reduce(C.ADLX,p)['state'],'unavailable')
        r=DiagnosticEngine([ReceiptProvider(C.ADLX,FixtureReader([receipt(p)]))]).collect(NOW,100)
        self.assertFalse(r['repair_capability']);self.assertNotIn('restart',json.dumps(r))

    def test_adlx_missing_or_unverified_bridge(self):
        self.assertEqual(reduce(C.ADLX,self.adlx(running=False))['state'],'offline')
        self.assertEqual(reduce(C.ADLX,self.adlx(library_verified=False))['state'],'error')

    def test_startup_bootstrap_logs_do_not_prove_run_dispatch(self):
        r=reduce(C.STARTUP,startup_payload())
        self.assertEqual(r['state'],'unknown');self.assertEqual(r['detail_code'],D.STARTUP_DISPATCH_UNCONFIRMED.value)

    def test_startup_requires_verified_login_session_lineage_and_target(self):
        for key in ('same_session_verified','lineage_verified','target_verified'):
            p=startup_payload();p[key]=False
            self.assertNotEqual(reduce(C.STARTUP,p)['state'],'healthy')
        p=startup_payload();p['login_at']=None
        self.assertEqual(reduce(C.STARTUP,p)['state'],'unknown')

    def test_startup_verified_dispatch_and_bootstrap_remain_distinct_from_https(self):
        p=startup_payload();p['dispatch_proven']=True
        e=DiagnosticEngine([ReceiptProvider(C.STARTUP,FixtureReader([receipt(p)]))]);r=e.collect(NOW,100)
        self.assertEqual(row(r,C.STARTUP)['state'],'healthy');self.assertEqual(row(r,C.HTTPS)['state'],'unknown')

    def test_startup_failure_without_dispatch_proof_is_inconclusive(self):
        p=startup_payload();p['events'][-1]['event']='spawn_failed'
        self.assertEqual(reduce(C.STARTUP,p)['state'],'unknown')
        p['dispatch_proven']=True;self.assertEqual(reduce(C.STARTUP,p)['state'],'error')

    def test_old_success_is_not_reused_after_new_failed_attempt(self):
        p=startup_payload();p['dispatch_proven']=True
        p['events']+=[dict(utc=NOW.isoformat(),pid=201,event='attempt'),dict(utc=NOW.isoformat(),pid=201,event='paths_invalid')]
        self.assertEqual(reduce(C.STARTUP,p)['state'],'error')

    def test_startup_old_events_before_login_are_ignored(self):
        p=startup_payload();p['dispatch_proven']=True;p['login_at']=NOW.isoformat()
        self.assertEqual(reduce(C.STARTUP,p)['state'],'unknown')

    def test_startup_returned_process_and_missing_entry(self):
        p=startup_payload();p['dispatch_proven']=True;p['events'][-1]['event']='agent_returned'
        self.assertEqual(reduce(C.STARTUP,p)['state'],'unavailable')
        p['configured']=False;self.assertEqual(reduce(C.STARTUP,p)['detail_code'],D.STARTUP_NOT_CONFIGURED.value)

    def test_startup_child_exit_zero_and_duplicate_do_not_request_restart(self):
        p=startup_payload();p['dispatch_proven']=True
        p['events'].append(dict(utc=NOW.isoformat(),pid=101,event='child_exit',code=0))
        self.assertEqual(reduce(C.STARTUP,p)['state'],'unavailable')
        p['events'][-1]['event']='duplicate'
        r=reduce(C.STARTUP,p);self.assertEqual(r['state'],'unknown')
        self.assertEqual(r['detail_code'],D.STARTUP_EXISTING_INSTANCE.value)

    def test_startup_bounded_logs_and_private_extra_fields_rejected(self):
        for mutation in ('count','private','future','order'):
            p=startup_payload()
            if mutation=='count':p['events']*=33
            if mutation=='private':p['events'][0]['message']='private fixture content'
            if mutation=='future':p['events'][-1]['utc']=(NOW+timedelta(seconds=1)).isoformat()
            if mutation=='order':p['events'].reverse()
            self.assertEqual(reduce(C.STARTUP,p)['code'],'provider_failure')


class PresentationTests(unittest.TestCase):
    def test_four_labels_and_inconclusive_are_explicit(self):
        view=present(mixed_review());labels={c['label'] for c in view['cards']}
        self.assertEqual(labels,{'Saudável','Indisponível','Desatualizado','Falha'})
        startup=next(c for c in view['cards'] if c['component']==C.STARTUP)
        self.assertEqual(startup['verification'],'Não verificado');self.assertEqual(startup['raw_state'],'unknown')
        self.assertTrue(view['simulation']);self.assertFalse(view['repair_capability'])

    def test_static_html_has_no_scripts_forms_or_network(self):
        html=render_html(mixed_review())
        self.assertNotIn('<script',html);self.assertNotIn('<form',html);self.assertIn("connect-src 'none'",html)
        self.assertIn('SIMULADO',html);self.assertIn('não significa PC desligado',html)

    def test_private_free_code_and_unknown_detail_cannot_cross_presentation(self):
        for key in ('code','detail_code'):
            r=mixed_review();r['checks'][0][key]='private fixture content'
            with self.assertRaises(DiagnosticError):present(r)

    def test_fake_healthy_and_non_simulated_report_rejected(self):
        r=mixed_review();r['simulation']=False
        with self.assertRaises(DiagnosticError):present(r)
        for age in (10,1000):
            r=mixed_review();r['checks'][0]['age_seconds']=age
            with self.assertRaises(DiagnosticError):present(r)

    def test_failed_probe_does_not_publish_arbitrary_exception(self):
        e=DiagnosticEngine([ReceiptProvider(C.HTTPS,FixtureReader([TimeoutError('private fixture content')]))])
        view=present(e.collect(NOW,100));self.assertNotIn('private fixture',json.dumps(view))
        self.assertEqual(view['cards'][0]['label'],'Falha')

    def test_new_interval_field_cannot_relax_gpu_or_adlx(self):
        from diagnostics.simulated import healthy_fixture
        for c in (C.GPU,C.ADLX,C.HTTPS):
            with self.assertRaises(DiagnosticError):replace(healthy_fixture(c,NOW,100),sample_interval_seconds=5)

    def test_every_fixed_detail_has_a_localized_message(self):
        from diagnostics.presentation import DETAILS
        self.assertEqual(set(DETAILS),set(D))

if __name__=='__main__':unittest.main()
