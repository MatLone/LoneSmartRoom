"""Mocks only: no Windows reader, network, Registry, pipe or sensor activation."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
import unittest

from diagnostics.contracts import Component as C,DiagnosticError
from diagnostics.engine import classify
from diagnostics.evidence_adapters import ADAPTERS
from diagnostics.evidence_contract import AdapterKind as A,EvidenceFrame,KNOWN_ISSUES
from diagnostics.evidence_cache import EvidenceHub
from diagnostics.mock_evidence import NOW,agent_payload,pipe_payload,monitor_payload,security_payload,frame,seed,reports,MockEvidenceSource,drain
from diagnostics.scenarios import startup_payload


def submit(hub,kind,payload,*,seconds=2,sequence=2,mode='active'):
    return hub.submit(frame(kind,payload,seconds=seconds,sequence=sequence),now=NOW+timedelta(seconds=seconds),monotonic=100+seconds,mode=mode)


def snapshot(hub,seconds=2,mode='active'):
    return hub.snapshot(now=NOW+timedelta(seconds=seconds),monotonic=100+seconds,mode=mode)


def row(report,component):return next(r for r in report['checks'] if r['component']==component.value)


class AdapterContractTests(unittest.TestCase):
    def test_mock_only_origin_and_version(self):
        base=frame(A.AGENT,agent_payload())
        for changes in ({'evidence_kind':'observed'},{'evidence_kind':'real'},{'schema_version':2},{'schema_version':True},
                        {'sequence':True},{'sequence':0},{'observed_monotonic':float('inf')},{'payload':b'x'*32769}):
            with self.subTest(changes=changes),self.assertRaises(DiagnosticError):replace(base,**changes)
    def test_exact_adapter_kind(self):
        with self.assertRaises(DiagnosticError):ADAPTERS[A.AGENT].project(frame(A.IPC,agent_payload()))
    def test_duplicate_json_and_nonfinite_rejected(self):
        for raw in (b'{"schema_version":1,"schema_version":1}',b'{"schema_version":1,"x":NaN}',b'[]',b'null',b'bad'):
            f=replace(frame(A.AGENT,agent_payload()),payload=raw)
            with self.assertRaises(DiagnosticError):ADAPTERS[A.AGENT].project(f)
    def test_private_and_arbitrary_fields_rejected(self):
        for field in ('password','certificate_private','hmac_key','executable','arguments','endpoint'):
            p=agent_payload();p[field]='PRIVATE-MARKER'
            with self.assertRaises(DiagnosticError):ADAPTERS[A.AGENT].project(frame(A.AGENT,p))
    def test_bounded_source_and_no_arbitrary_reader(self):
        with self.assertRaises(DiagnosticError):MockEvidenceSource(A.AGENT,[None]*65)
        with self.assertRaises(DiagnosticError):drain(object(),EvidenceHub(),now=NOW,monotonic=100)


class AgentEvidenceTests(unittest.TestCase):
    def projection(self,p):return ADAPTERS[A.AGENT].project(frame(A.AGENT,p,seconds=2))
    def test_identity_listener_and_authenticated_status(self):
        p=self.projection(agent_payload(seconds=2));self.assertEqual([classify(r)[0] for r in p.probes],['healthy','healthy'])
    def test_running_process_without_status_is_not_healthy(self):
        p=agent_payload(seconds=2);p['status']=None
        hp,lp=self.projection(p).probes
        self.assertEqual(classify(hp)[0],'unknown');self.assertEqual(classify(lp)[0],'healthy')
    def test_listener_owner_mismatch_with_correct_process(self):
        p=agent_payload(seconds=2);p['listener']['owner_pid']=999
        hp,lp=self.projection(p).probes
        self.assertEqual(classify(lp)[0],'error');self.assertEqual(classify(hp)[0],'unknown')
    def test_unknown_identity_never_healthy_or_proven_failure(self):
        for key in ('supervisor','worker'):
            p=agent_payload(seconds=2);p['processes'][key]['verdict']='unknown'
            self.assertTrue(all(classify(x)[0]=='unknown' for x in self.projection(p).probes))
    def test_absent_or_future_process_not_accepted(self):
        p=agent_payload(seconds=2);p['processes']['supervisor']=None
        self.assertEqual(classify(self.projection(p).probes[0])[0],'unknown')
        p=agent_payload(seconds=2);p['processes']['worker']['created_at']=(NOW+timedelta(seconds=3)).isoformat()
        with self.assertRaises(DiagnosticError):self.projection(p)
    def test_auth_failure_and_tls_rejection(self):
        p=agent_payload(seconds=2);p['status']['http_status']=401
        self.assertEqual(self.projection(p).probes[0].detail_code.value,'authentication_failed')
        p=agent_payload(seconds=2);p['status'].update(result='tls_rejected',http_status=None,tls_verified=False,pin_verified=False)
        self.assertEqual(classify(self.projection(p).probes[0])[0],'error')
    def test_unknown_certificate_check_not_proven_failure(self):
        p=agent_payload(seconds=2);p['status']['pin_verified']=None
        self.assertEqual(classify(self.projection(p).probes[0])[0],'unknown')
    def test_fixed_status_method_and_endpoint(self):
        for changes in ({'method':'POST'},{'endpoint':'/v2/apps'},{'checked_at':None}):
            p=agent_payload(seconds=2);p['status'].update(changes)
            with self.assertRaises(DiagnosticError):self.projection(p)
    def test_old_status_keeps_original_time(self):
        p=agent_payload(seconds=0)
        hp=self.projection(p).probes[0]
        self.assertEqual(hp.observed_at,NOW);self.assertEqual(hp.observed_monotonic,100)
    def test_https_success_does_not_certify_startup(self):
        r=snapshot(seed());self.assertEqual(row(r,C.HTTPS)['state'],'healthy');self.assertEqual(row(r,C.STARTUP)['state'],'unknown')


class PipeAndMetricsTests(unittest.TestCase):
    def test_verified_acl_required(self):
        for value,expected in ((True,'healthy'),(False,'error'),(None,'unknown')):
            p=pipe_payload();p['acl_verified']=value
            result=ADAPTERS[A.IPC].project(frame(A.IPC,p))
            self.assertEqual(classify(result.probes[0])[0],expected)
    def test_all_peer_checks_and_contract(self):
        for key in ('local','sid_verified','session_verified','server_identity_verified'):
            p=pipe_payload();p[key]=False
            self.assertEqual(classify(ADAPTERS[A.IPC].project(frame(A.IPC,p)).probes[0])[0],'error')
        p=pipe_payload();p['contract_version']=2
        self.assertEqual(classify(ADAPTERS[A.IPC].project(frame(A.IPC,p)).probes[0])[0],'error')
    def test_disconnected_is_unavailable_not_pc_off(self):
        p=ADAPTERS[A.IPC].project(frame(A.IPC,pipe_payload(connected=False)))
        self.assertEqual(classify(p.probes[0])[0],'offline')
    def test_zero_valid_unsupported_null_and_invalid_value(self):
        p=monitor_payload();p['snapshot']['metrics'][0]['value']=0
        projection=ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1))
        self.assertEqual(classify(projection.probes[0])[0],'healthy')
        p=monitor_payload(state='unsupported');self.assertEqual(classify(ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1)).probes[0])[0],'unsupported')
        p=monitor_payload();p['snapshot']['metrics'][0]['value']=None
        with self.assertRaises(DiagnosticError):ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1))
    def test_inactive_normal_not_failure(self):
        r=reports()['inactive']['report']
        for c in (C.CPU,C.GPU,C.RAM,C.ADLX,C.IPC):
            self.assertEqual(row(r,c)['detail_code'],'application_normally_inactive');self.assertEqual(row(r,c)['state'],'unavailable')
    def test_unsupported_sensor_does_not_turn_into_zero(self):
        r=reports()['unsupported']['report'];self.assertEqual(row(r,C.GPU)['state'],'unsupported');self.assertFalse(row(r,C.GPU)['valid'])
    def test_adlx_ingress_limit_preserved(self):
        p=monitor_payload();p['bridge']['ingress_age_seconds']=1.50001
        with self.assertRaises(DiagnosticError):ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1))
    def test_contradictory_lifecycle_rejected(self):
        p=monitor_payload();p['application_open']=False
        with self.assertRaises(DiagnosticError):ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1))
    def test_missing_snapshot_and_unknown_library_not_health(self):
        p=monitor_payload();p['snapshot']=None;p['bridge']['library_verified']=None
        projection=ADAPTERS[A.MONITORING].project(frame(A.MONITORING,p,seconds=1))
        self.assertEqual(classify(projection.probes[0])[0],'unavailable');self.assertEqual(classify(projection.probes[-1])[0],'unknown')


class CacheLifecycleTests(unittest.TestCase):
    def test_all_online_after_fresh_generation_sample(self):
        r=snapshot(seed())
        self.assertTrue(all(row(r,c)['state']=='healthy' for c in (C.HTTPS,C.LISTENER,C.IPC,C.CPU,C.GPU,C.RAM,C.ADLX)))
    def test_query_never_refreshes_evidence_timestamp(self):
        h=seed();a=snapshot(h);b=snapshot(h,3)
        self.assertEqual(row(a,C.HTTPS)['observed_at'],row(b,C.HTTPS)['observed_at'])
        self.assertGreater(row(b,C.HTTPS)['age_seconds'],row(a,C.HTTPS)['age_seconds'])
        self.assertEqual(row(snapshot(h,10),C.HTTPS)['state'],'stale')
    def test_ttl_boundaries_active_and_inactive(self):
        for t,mode,state in ((3.999,'active','healthy'),(4,'active','stale'),(11.999,'inactive','healthy'),(12,'inactive','stale')):
            h=seed();self.assertEqual(row(snapshot(h,t,mode),C.GPU)['state'],state)
    def test_disconnect_reconnect_requires_new_sample(self):
        h=seed();submit(h,A.IPC,pipe_payload(connected=False))
        self.assertEqual(row(snapshot(h),C.CPU)['state'],'unavailable')
        submit(h,A.IPC,pipe_payload(generation=2),seconds=3,sequence=3)
        self.assertEqual(row(snapshot(h,3),C.GPU)['state'],'unknown')
        # A fresh receipt carrying a pre-reconnect sample cannot restore health.
        p=monitor_payload(seconds=4,generation=2,age=2)
        submit(h,A.MONITORING,p,seconds=4,sequence=2)
        self.assertFalse(row(snapshot(h,4),C.GPU)['valid'])
        submit(h,A.MONITORING,monitor_payload(seconds=5,generation=2),seconds=5,sequence=3)
        self.assertEqual(row(snapshot(h,5),C.GPU)['state'],'healthy')
    def test_old_generation_cannot_reconnect(self):
        h=seed();submit(h,A.IPC,pipe_payload(generation=2),seconds=2)
        result=submit(h,A.MONITORING,monitor_payload(seconds=3,generation=1),seconds=3)
        self.assertFalse(result['accepted']);self.assertFalse(row(snapshot(h,3),C.CPU)['valid'])
    def test_expired_peer_cannot_certify_new_metrics(self):
        h=seed();submit(h,A.MONITORING,monitor_payload(seconds=6),seconds=6)
        self.assertFalse(row(snapshot(h,6),C.CPU)['valid'])
        submit(h,A.IPC,pipe_payload(),seconds=7)
        submit(h,A.MONITORING,monitor_payload(seconds=7),seconds=7,sequence=3)
        self.assertTrue(row(snapshot(h,7),C.CPU)['valid'])
    def test_invalid_mode_does_not_mutate_evidence(self):
        h=seed()
        with self.assertRaises(DiagnosticError):submit(h,A.AGENT,agent_payload(seconds=2),mode='arbitrary')
        self.assertEqual(row(snapshot(h),C.HTTPS)['observed_at'],'2026-10-26T12:00:00.000Z')
    def test_duplicate_sequence_and_future_frame_rejected(self):
        h=seed();self.assertEqual(submit(h,A.AGENT,agent_payload(seconds=2),sequence=1)['code'],'replayed_or_out_of_order')
        f=frame(A.AGENT,agent_payload(seconds=3),seconds=3,sequence=2)
        self.assertEqual(h.submit(f,now=NOW+timedelta(seconds=2),monotonic=102)['code'],'future_evidence')
        self.assertFalse(row(snapshot(h,2),C.HTTPS)['valid'])
    def test_clock_regression_rejected(self):
        h=seed();p=agent_payload(seconds=.1)
        with self.assertRaises(DiagnosticError):submit(h,A.AGENT,p,seconds=.1)
    def test_rate_limit_new_hub(self):
        h=EvidenceHub();submit(h,A.AGENT,agent_payload(seconds=0),seconds=0,sequence=1)
        self.assertEqual(submit(h,A.AGENT,agent_payload(seconds=.1),seconds=.1)['code'],'rate_limited')
        self.assertTrue(submit(h,A.AGENT,agent_payload(seconds=.5),seconds=.5)['accepted'])
    def test_provider_errors_sanitized_then_recover(self):
        h=seed();s=MockEvidenceSource(A.AGENT,[RuntimeError('PRIVATE-TOKEN'),frame(A.AGENT,agent_payload(seconds=3),seconds=3,sequence=2)])
        drain(s,h,now=NOW+timedelta(seconds=2),monotonic=102)
        self.assertEqual(row(snapshot(h),C.HTTPS)['code'],'provider_failure')
        self.assertNotIn('PRIVATE-TOKEN',json.dumps(h.audit(now=NOW+timedelta(seconds=2),monotonic=102)))
        drain(s,h,now=NOW+timedelta(seconds=3),monotonic=103)
        self.assertEqual(row(snapshot(h,3),C.HTTPS)['state'],'healthy')
        self.assertEqual(row(snapshot(h,3),C.HTTPS)['last_communication'],'2026-10-26T12:00:03.000Z')
    def test_confirmed_failure_does_not_auto_repair(self):
        h=seed()
        for seq in range(2,6):
            p=agent_payload(seconds=seq);p['status']['http_status']=401
            submit(h,A.AGENT,p,seconds=seq,sequence=seq)
            self.assertEqual(row(snapshot(h,seq),C.HTTPS)['state'],'error')
        self.assertEqual(row(snapshot(h,5),C.HTTPS)['last_communication'],'2026-10-26T12:00:00.000Z')
    def test_invalid_payload_cannot_keep_a_healthy_state(self):
        h=seed();p=agent_payload(seconds=2);p['status']['password']='PRIVATE-MARKER'
        self.assertFalse(submit(h,A.AGENT,p)['accepted']);self.assertFalse(row(snapshot(h),C.HTTPS)['valid'])
        self.assertNotIn('PRIVATE-MARKER',json.dumps(h.audit(now=NOW+timedelta(seconds=2),monotonic=102)))
    def test_cache_bounds_and_normal_close(self):
        h=seed()
        for seq in range(2,130):submit(h,A.AGENT,agent_payload(seconds=seq),seconds=seq,sequence=seq)
        info=h.audit(now=NOW+timedelta(seconds=129),monotonic=229)
        self.assertLessEqual(info['cache']['diagnostic_slots'],8);self.assertLessEqual(info['cache']['source_watermarks'],5)
        self.assertLessEqual(len(json.dumps(info).encode()),8192);self.assertLessEqual(len(json.dumps(snapshot(h,129)).encode()),16384)
        h.close();info=h.audit(now=NOW+timedelta(seconds=129),monotonic=229)
        self.assertTrue(info['closed']);self.assertEqual(info['cache']['diagnostic_slots'],0)
        self.assertFalse(any(r['valid'] for r in snapshot(h,129)['checks']))


class StartupAndSecurityTests(unittest.TestCase):
    def test_all_pending_issues_remain_open(self):
        self.assertEqual(len(KNOWN_ISSUES),5)
        info=seed().audit(now=NOW+timedelta(seconds=1),monotonic=101)
        self.assertEqual(info['security']['state'],'unknown')
        self.assertIn('crashpad_0xe9',info['security']['known_issues'])
    def test_login_and_bootstrap_without_dispatch_stays_unknown(self):
        p=startup_payload();probe=ADAPTERS[A.STARTUP].project(frame(A.STARTUP,p)).probes[0]
        self.assertEqual(classify(probe)[0],'unknown')
        p['dispatch_proven']=True;self.assertEqual(classify(ADAPTERS[A.STARTUP].project(frame(A.STARTUP,p)).probes[0])[0],'healthy')
    def test_failed_authorized_check_and_old_checks(self):
        h=seed();p=security_payload(seconds=2);p['checks'][0]['result']='failed'
        submit(h,A.SECURITY,p)
        self.assertEqual(h.audit(now=NOW+timedelta(seconds=2),monotonic=102)['security']['state'],'error')
        self.assertEqual(h.audit(now=NOW+timedelta(seconds=12),monotonic=112)['security']['state'],'stale')
    def test_unauthorized_unknown_and_private_claims(self):
        p=security_payload();p['checks'][0]['authorized']=False
        with self.assertRaises(DiagnosticError):ADAPTERS[A.SECURITY].project(frame(A.SECURITY,p))
        p['checks'][0]['result']='unknown';self.assertEqual(ADAPTERS[A.SECURITY].project(frame(A.SECURITY,p)).security['state'],'unknown')
        p['checks'][0]['private_certificate']='PRIVATE'
        with self.assertRaises(DiagnosticError):ADAPTERS[A.SECURITY].project(frame(A.SECURITY,p))
    def test_sidecar_does_not_change_report_v1(self):
        h=seed();r=snapshot(h);self.assertEqual(len(r['checks']),8)
        self.assertNotIn('security',r);self.assertEqual(r['schema_version'],1)


if __name__=='__main__':unittest.main()
