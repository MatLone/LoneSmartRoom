"""Pure mocks; no process, socket, registry or operational agent import."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

spec = importlib.util.spec_from_file_location('supervision_candidate',
    Path(__file__).resolve().parents[1] / 'agent/development/supervision.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Policy, Evidence, Action = module.SupervisorPolicy, module.Evidence, module.Action
CLEAN = Evidence(worker_exited=True, mutex_released=True, listener_absent=True, preflight_verified=True)
READY = Evidence(worker_alive=True, identity_verified=True, listener_verified=True, tls_verified=True, authenticated=True)


class PolicyTests(unittest.TestCase):
    def start(self, **options):
        p = Policy(enabled=True, **options)
        self.assertEqual(p.step(0, Evidence(preflight_verified=True)), Action.START)
        return p

    def test_disabled_by_default(self):
        self.assertEqual(Policy().step(0, Evidence()), Action.NONE)

    def test_preflight_fail_closed(self):
        for facts in (Evidence(), Evidence(preflight_verified=True, worker_alive=True),
                      Evidence(preflight_verified=True, duplicate=True),
                      Evidence(preflight_verified=True, security_failure=True)):
            p = Policy(enabled=True)
            self.assertEqual(p.step(0, facts), Action.NONE)
            self.assertEqual(p.state, 'blocked')

    def test_process_alone_not_healthy(self):
        p = self.start()
        p.step(1, Evidence(worker_alive=True))
        self.assertEqual(p.state, 'starting')
        p.step(2, READY)
        self.assertEqual(p.state, 'serving')

    def test_cooperative_stop_and_complete_cleanup(self):
        p = self.start()
        p.step(1, READY)
        self.assertEqual(p.step(2, READY, stop=True), Action.COOPERATIVE_STOP)
        self.assertEqual(p.step(3, READY, stop=True), Action.NONE)
        p.step(4, CLEAN)
        self.assertEqual(p.state, 'stopped')

    def test_startup_deadline_does_not_kill_or_restart(self):
        p = self.start(attempts=3)
        self.assertEqual(p.step(30, Evidence(worker_alive=True)), Action.COOPERATIVE_STOP)
        p.step(60, Evidence(worker_alive=True))
        self.assertEqual(p.state, 'stop_timeout')
        self.assertEqual(p.step(100, CLEAN), Action.NONE)
        self.assertEqual(p.attempts, 1)

    def test_exit_without_cleanup_blocks_recovery(self):
        p = self.start(attempts=3)
        p.step(1, Evidence(worker_exited=True))
        self.assertEqual(p.state, 'blocked')

    def test_bounded_recovery_requires_fresh_preflight(self):
        p = self.start(attempts=2)
        p.step(1, CLEAN)
        self.assertEqual(p.state, 'backoff')
        self.assertEqual(p.step(5, CLEAN), Action.NONE)
        self.assertEqual(p.step(6, CLEAN), Action.START)
        p.step(7, CLEAN)
        self.assertEqual(p.state, 'stopped')
        self.assertEqual(p.attempts, 2)

    def test_no_recovery_on_security_failure(self):
        p = self.start(attempts=3)
        p.step(1, Evidence(**{**vars(CLEAN), 'security_failure': True}))
        self.assertEqual(p.state, 'stopped')

    def test_supervisor_without_worker_ambiguous(self):
        p = self.start()
        p.step(1, Evidence(spawn_failed=True))
        self.assertEqual(p.state, 'blocked')

    def test_readiness_loss_does_not_spawn_duplicates(self):
        p = self.start()
        p.step(1, READY)
        self.assertEqual(p.step(2, Evidence(worker_alive=True)), Action.NONE)
        self.assertEqual(p.state, 'degraded')
        p.step(3, READY)
        self.assertEqual(p.state, 'serving')
        self.assertEqual(p.attempts, 1)

    def test_clock_validation(self):
        p = self.start()
        for invalid in (float('nan'), float('inf'), -1, True):
            with self.assertRaises(ValueError): p.step(invalid, READY)
        p.step(1, READY)
        with self.assertRaises(ValueError): p.step(0, READY)

    def test_boolean_evidence_not_coerced(self):
        with self.assertRaises(ValueError): Evidence(authenticated='200')
        with self.assertRaises(ValueError): Evidence(worker_alive=True, worker_exited=True)

    def test_cancellation_during_backoff(self):
        p = self.start(attempts=2)
        p.step(1, CLEAN)
        p.step(2, CLEAN, stop=True)
        self.assertEqual(p.state, 'stopped')

    def test_logs_bounded_sanitized(self):
        p = self.start()
        for i in range(1, 200): p.step(i, READY if i % 2 else Evidence(worker_alive=True))
        self.assertEqual(len(p.events), 64)
        self.assertTrue(all(set(e) == {'code', 'at_monotonic_seconds'} for e in p.events))
        self.assertNotIn('path', json.dumps(list(p.events)))

    def test_budget_and_deadlines_validated(self):
        for options in ({'attempts': 4}, {'attempts': True}, {'stop_seconds': 0}, {'retry_seconds': float('inf')}):
            with self.assertRaises(ValueError): Policy(**options)


if __name__ == '__main__': unittest.main()
