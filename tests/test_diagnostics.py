"""Pure fixtures only; no operational agent, process, sensor, Registry or IPC."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from itertools import repeat
import unittest

from diagnostics.contracts import Component as C, DiagnosticError, MAX_REPORT_BYTES, Outcome, Probe
from diagnostics.engine import DiagnosticEngine
from diagnostics.simulated import SimulatedProvider, healthy_fixture

NOW=datetime(2026,10,26,12,tzinfo=timezone.utc)


def fixture(component=C.HTTPS, **changes):
    p=healthy_fixture(component,NOW,100)
    return replace(p,facts={**p.facts,**changes})


def record(report, component=C.HTTPS):
    return next(r for r in report['checks'] if r['component']==component.value)


def reduce(probe, component=None):
    component=component or probe.component
    return record(DiagnosticEngine([SimulatedProvider(component,[probe])]).collect(NOW,100),component)


class DiagnosticContractTests(unittest.TestCase):
    def test_utc_naive_and_local_timestamps_rejected(self):
        for value in (datetime(2026,10,26),NOW.astimezone(timezone(timedelta(hours=-3)))):
            with self.subTest(value=value),self.assertRaisesRegex(DiagnosticError,'utc_required'):
                replace(fixture(),observed_at=value)

    def test_finite_nonnegative_clock_required(self):
        for value in (-1,float('nan'),float('inf'),True,'100',10**400):
            with self.subTest(value=type(value).__name__),self.assertRaises(DiagnosticError):
                replace(fixture(),observed_monotonic=value)

    def test_contract_version_is_strict(self):
        for version in (2,True,None):
            with self.assertRaisesRegex(DiagnosticError,'incompatible_contract'):
                replace(fixture(),schema_version=version)

    def test_real_provider_not_authorized(self):
        with self.assertRaisesRegex(DiagnosticError,'operational_providers_not_authorized'):
            replace(fixture(),evidence_kind='real')
        provider=SimulatedProvider(C.HTTPS);provider.evidence_kind='real'
        with self.assertRaises(DiagnosticError):DiagnosticEngine([provider])

    def test_unknown_keys_and_free_text_rejected(self):
        for facts in ({'token':'redacted-fixture'}, {'path':'not-a-probe'}, {'responded':'yes'}):
            with self.assertRaises(DiagnosticError):replace(fixture(),facts=facts)

    def test_boolean_zero_is_not_false_fact(self):
        for value in (0,1,0.0,[],{}):
            with self.assertRaises(DiagnosticError):fixture(responded=value)

    def test_null_remains_unknown(self):
        self.assertEqual(reduce(fixture(responded=None))['state'],'unknown')

    def test_port_is_fixed_and_never_a_command_input(self):
        for value in (80,443,'8776',True):
            with self.assertRaises(DiagnosticError):fixture(C.LISTENER,port=value)

    def test_facts_are_immutable_copies(self):
        facts={'responded':True,'authenticated':True,'tls_verified':True}
        p=Probe(C.HTTPS,NOW,100,facts);facts['authenticated']=False
        self.assertTrue(p.facts['authenticated'])
        with self.assertRaises(TypeError):p.facts['tls_verified']=False

    def test_duplicate_components_are_rejected(self):
        with self.assertRaises(DiagnosticError):DiagnosticEngine([SimulatedProvider(C.CPU),SimulatedProvider(C.CPU)])

    def test_provider_limit(self):
        with self.assertRaises(DiagnosticError):DiagnosticEngine([SimulatedProvider(C.CPU)]*9)

    def test_fixture_queue_bound(self):
        with self.assertRaises(DiagnosticError):SimulatedProvider(C.CPU,[None]*65)

    def test_infinite_fixture_iterator_is_bounded_before_materialization(self):
        with self.assertRaisesRegex(DiagnosticError,'fixture_queue_limit'):
            SimulatedProvider(C.CPU,repeat(None))

    def test_infinite_provider_iterator_is_bounded_before_materialization(self):
        with self.assertRaisesRegex(DiagnosticError,'too_many_providers'):
            DiagnosticEngine(repeat(SimulatedProvider(C.CPU)))


class DiagnosticClassificationTests(unittest.TestCase):
    def test_all_components_healthy_fixture_is_explicit_simulation(self):
        engine=DiagnosticEngine([SimulatedProvider(c,[fixture(c)]) for c in C])
        report=engine.collect(NOW,100)
        self.assertTrue(report['simulation']);self.assertFalse(report['repair_capability'])
        self.assertEqual(report['power_state'],'unknown')
        self.assertEqual(len(report['checks']),8)
        self.assertTrue(all(r['state']=='healthy' and r['evidence_kind']=='simulated' for r in report['checks']))
        self.assertLessEqual(len(json.dumps(report).encode()),MAX_REPORT_BYTES)

    def test_no_providers_means_unknown_not_offline(self):
        report=DiagnosticEngine().snapshot(NOW,100)
        self.assertTrue(all(r['state']=='unknown' and r['observed_at'] is None and r['age_seconds'] is None for r in report['checks']))

    def test_missing_required_fact_is_inconclusive(self):
        self.assertEqual(reduce(replace(fixture(),facts={'responded':True}))['code'],'insufficient_evidence')

    def test_https_requires_authentication_and_verified_tls(self):
        for changes in ({'authenticated':False},{'tls_verified':False}):
            with self.subTest(changes=changes):
                self.assertEqual(reduce(fixture(**changes))['state'],'error')

    def test_no_response_is_offline_service_never_pc_power(self):
        report=DiagnosticEngine([SimulatedProvider(C.HTTPS,[fixture(responded=False)])]).collect(NOW,100)
        self.assertEqual(record(report)['state'],'offline');self.assertEqual(report['power_state'],'unknown')

    def test_listener_is_distinct_from_https_identity(self):
        report=DiagnosticEngine([SimulatedProvider(C.LISTENER,[fixture(C.LISTENER)])]).collect(NOW,100)
        self.assertEqual(record(report,C.LISTENER)['state'],'healthy');self.assertEqual(record(report)['state'],'unknown')
        self.assertEqual(reduce(fixture(C.LISTENER,identity_matches=False))['code'],'listener_identity_mismatch')
        self.assertEqual(reduce(fixture(C.LISTENER,present=False))['state'],'offline')

    def test_ipc_disconnection_peer_and_contract_fail_closed(self):
        for changes,code in [({'connected':False},'ipc_disconnected'),({'peer_validated':False},'ipc_peer_unverified'),({'contract_version':2},'ipc_contract_mismatch')]:
            self.assertEqual(reduce(fixture(C.IPC,**changes))['code'],code)

    def test_collectors_and_bridge_failures_are_component_specific(self):
        for c in (C.CPU,C.GPU,C.RAM,C.ADLX):
            running='running' if c==C.ADLX else 'collector_running'
            self.assertEqual(reduce(fixture(c,**{running:False}))['state'],'offline')
            self.assertEqual(reduce(fixture(c,sample_stale=True))['state'],'stale')
            self.assertEqual(reduce(fixture(c,sample_valid=False))['state'],'unavailable')
        self.assertEqual(reduce(fixture(C.ADLX,dll_verified=False))['state'],'error')

    def test_unsupported_is_not_zero_or_error(self):
        result=reduce(replace(fixture(C.GPU),outcome=Outcome.UNSUPPORTED))
        self.assertEqual(result['state'],'unsupported');self.assertFalse(result['valid'])
        self.assertNotIn('value',result)

    def test_other_provider_outcomes_do_not_become_healthy(self):
        for outcome in (Outcome.ERROR,Outcome.UNKNOWN,Outcome.UNAVAILABLE):
            self.assertEqual(reduce(replace(fixture(C.CPU),outcome=outcome))['state'],outcome.value)

    def test_autostart_dispatch_failure_is_only_a_possible_cause(self):
        result=reduce(fixture(C.STARTUP,dispatch_observed=False,bootstrap_succeeded=None))
        self.assertEqual(result['state'],'unknown');self.assertEqual(result['code'],'possible_dispatch_problem_unconfirmed')

    def test_autostart_without_login_evidence_remains_unknown(self):
        self.assertEqual(reduce(fixture(C.STARTUP,login_observed=None,dispatch_observed=False,bootstrap_succeeded=None))['code'],'insufficient_evidence')

    def test_bootstrap_failure_needs_dispatch_evidence(self):
        self.assertEqual(reduce(fixture(C.STARTUP,bootstrap_succeeded=False))['code'],'bootstrap_failure_observed')
        self.assertEqual(reduce(fixture(C.STARTUP,dispatch_observed=None,bootstrap_succeeded=False))['state'],'unknown')

    def test_unconfigured_startup_not_claimed_windows_failure(self):
        self.assertEqual(reduce(fixture(C.STARTUP,configured=False))['code'],'startup_not_configured')


class DiagnosticLifecycleTests(unittest.TestCase):
    def test_snapshot_never_polls_provider(self):
        provider=SimulatedProvider(C.CPU,[fixture(C.CPU)]);engine=DiagnosticEngine([provider])
        for _ in range(20):engine.snapshot(NOW,100)
        self.assertEqual(provider.reads,0)

    def test_none_frame_does_not_refresh_cached_age(self):
        provider=SimulatedProvider(C.CPU,[fixture(C.CPU),None]);engine=DiagnosticEngine([provider])
        engine.collect(NOW,100)
        row=record(engine.collect(NOW+timedelta(seconds=4),104),C.CPU)
        self.assertEqual(row['state'],'stale');self.assertEqual(row['age_seconds'],4)

    def test_active_inactive_gpu_expiry_boundaries(self):
        engine=DiagnosticEngine([SimulatedProvider(C.GPU,[fixture(C.GPU)])]);engine.collect(NOW,100)
        self.assertEqual(record(engine.snapshot(NOW+timedelta(seconds=3),103),C.GPU)['state'],'stale')
        self.assertEqual(record(engine.snapshot(NOW+timedelta(seconds=3.001),103.001),C.GPU)['state'],'stale')
        self.assertEqual(record(engine.snapshot(NOW+timedelta(seconds=11),111,'inactive'),C.GPU)['state'],'stale')
        self.assertEqual(record(engine.snapshot(NOW+timedelta(seconds=11.001),111.001,'inactive'),C.GPU)['state'],'stale')

    def test_new_probe_cannot_claim_future_utc_or_monotonic(self):
        for p in (replace(fixture(),observed_at=NOW+timedelta(seconds=1)),replace(fixture(),observed_monotonic=101)):
            result=reduce(p);self.assertEqual(result['code'],'invalid_time');self.assertFalse(result['valid'])

    def test_snapshot_utc_rollback_does_not_mask_future_with_monotonic_age(self):
        engine=DiagnosticEngine([SimulatedProvider(C.CPU,[fixture(C.CPU)])]);engine.collect(NOW,100)
        row=record(engine.snapshot(NOW-timedelta(seconds=1),101),C.CPU)
        self.assertEqual(row['state'],'unknown');self.assertEqual(row['code'],'invalid_time')
        self.assertIsNone(row['age_seconds'])

    def test_monotonic_rollback_rejected(self):
        engine=DiagnosticEngine();engine.snapshot(NOW,100)
        with self.assertRaises(DiagnosticError):engine.snapshot(NOW,99)

    def test_wall_clock_advance_expires_observation_conservatively(self):
        engine=DiagnosticEngine([SimulatedProvider(C.CPU,[fixture(C.CPU)])]);engine.collect(NOW,100)
        self.assertEqual(record(engine.snapshot(NOW+timedelta(seconds=20),101),C.CPU)['state'],'stale')

    def test_last_authenticated_communication_survives_failure_without_renewal(self):
        provider=SimulatedProvider(C.HTTPS,[fixture(),fixture(responded=False)])
        engine=DiagnosticEngine([provider]);first=record(engine.collect(NOW,100))
        second=record(engine.collect(NOW+timedelta(seconds=1),101))
        self.assertEqual(first['last_communication'],second['last_communication'])
        self.assertEqual(second['state'],'offline')

    def test_stale_or_unverified_https_does_not_establish_last_communication(self):
        for p in (replace(fixture(),observed_monotonic=0),fixture(tls_verified=False)):
            self.assertIsNone(reduce(p)['last_communication'])

    def test_exception_sanitized_and_followed_by_recovery(self):
        provider=SimulatedProvider(C.CPU,[ValueError('private fixture text must disappear'),fixture(C.CPU)])
        engine=DiagnosticEngine([provider]);report=engine.collect(NOW,100)
        self.assertNotIn('private fixture',json.dumps(report));self.assertEqual(record(report,C.CPU)['code'],'provider_failure')
        self.assertEqual(record(engine.collect(NOW,100),C.CPU)['state'],'healthy')

    def test_timeout_is_sanitized_without_repair_or_retry(self):
        provider=SimulatedProvider(C.IPC,[TimeoutError('private')]);engine=DiagnosticEngine([provider])
        row=record(engine.collect(NOW,100),C.IPC)
        self.assertEqual(row['code'],'provider_timeout');self.assertEqual(provider.reads,1)

    def test_component_mismatch_and_unstructured_frame_rejected(self):
        for frame in (fixture(C.GPU),{'state':'healthy'}):
            report=DiagnosticEngine([SimulatedProvider(C.CPU,[frame])]).collect(NOW,100)
            self.assertFalse(record(report,C.CPU)['valid'])

    def test_old_frame_after_failure_cannot_renew_health(self):
        provider=SimulatedProvider(C.HTTPS,[fixture(),RuntimeError('private'),replace(fixture(),observed_monotonic=99,observed_at=NOW-timedelta(seconds=1))])
        engine=DiagnosticEngine([provider]);first=record(engine.collect(NOW,100))
        engine.collect(NOW,100);last=record(engine.collect(NOW,100))
        self.assertEqual(last['code'],'out_of_order');self.assertEqual(last['last_communication'],first['last_communication'])

    def test_returned_report_is_detached_from_cache(self):
        engine=DiagnosticEngine([SimulatedProvider(C.CPU,[fixture(C.CPU)])]);report=engine.collect(NOW,100)
        record(report,C.CPU)['state']='invented'
        self.assertEqual(record(engine.snapshot(NOW,100),C.CPU)['state'],'healthy')

    def test_cache_and_report_stay_bounded(self):
        providers=[SimulatedProvider(c,[fixture(c)]) for c in C];engine=DiagnosticEngine(providers)
        for i in range(1000):
            report=engine.collect(NOW+timedelta(seconds=i),100+i)
        self.assertEqual(len(engine._latest),8);self.assertEqual(len(engine._high_water),8)
        self.assertEqual(len(report['checks']),8)
        self.assertLessEqual(len(json.dumps(report).encode()),MAX_REPORT_BYTES)

    def test_invalid_activity_mode_not_silently_applied(self):
        with self.assertRaises(DiagnosticError):DiagnosticEngine().snapshot(NOW,100,'hidden-but-active')

if __name__=='__main__':unittest.main()
