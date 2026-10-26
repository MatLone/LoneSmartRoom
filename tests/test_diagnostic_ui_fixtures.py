"""Deterministic diagnostic UI data; no live readers or operational endpoints."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('diagnostic_fixture_generator',ROOT/'scripts/prepare-diagnostic-fixtures.py')
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)


class DiagnosticUIFixtures(unittest.TestCase):
    def setUp(self):
        self.script,self.text=generator.build_data();self.bundle=json.loads(self.text)
    def test_all_scenarios_are_versioned_simulations(self):
        self.assertEqual(len(self.bundle['scenarios']),13)
        for report in self.bundle['scenarios'].values():
            self.assertEqual(report['schema_version'],1);self.assertTrue(report['simulation'])
            self.assertFalse(report['repair_capability']);self.assertEqual(report['power_state'],'unknown')
            self.assertTrue(all(r['evidence_kind']=='simulated' for r in report['checks']))
    def test_output_matches_checked_in_assets(self):
        self.assertEqual((ROOT/'apps/windows-ui/diagnostics-contract.js').read_text(encoding='utf-8'),self.script)
        self.assertEqual((ROOT/'apps/windows-ui/diagnostics-fixtures.json').read_text(encoding='utf-8'),self.text)
    def test_generation_is_deterministic(self):self.assertEqual(generator.build_data(),(self.script,self.text))
    def test_fixture_bundle_bounded(self):
        self.assertLess(len(self.text.encode()),128*1024)
        self.assertTrue(all(len(json.dumps(r).encode())<=16384 for r in self.bundle['scenarios'].values()))
    def test_no_measurements_or_credentials_exported(self):
        for term in ('"metrics"','"value"','fixture-private-error','"secret"','"nonce"','"path"'):
            self.assertNotIn(term,self.text)
    def test_recovery_uses_new_valid_evidence(self):
        report=self.bundle['scenarios']['recovered'];row=report['checks'][0]
        self.assertEqual(row['state'],'healthy');self.assertEqual(row['age_seconds'],0)
        self.assertEqual(row['last_communication'],report['generated_at'])
    def test_stale_samples_retain_original_timestamp(self):
        rows=self.bundle['scenarios']['stale']['checks']
        for row in rows:
            if row['component'] in ('cpu_collector','gpu_collector','ram_collector','adlx_bridge'):
                self.assertEqual(row['state'],'stale');self.assertEqual(row['age_seconds'],12)
                self.assertFalse(row['valid'])
    def test_inactivity_is_explicit_without_failure(self):
        rows=self.bundle['scenarios']['inactive']['checks']
        for row in rows:
            if row['component'] in ('cpu_collector','gpu_collector','ram_collector','adlx_bridge','monitoring_ipc'):
                self.assertEqual(row['detail_code'],'application_normally_inactive')
                self.assertEqual(row['state'],'unavailable')
    def test_missing_evidence_does_not_become_failure(self):
        self.assertTrue(all(r['state']=='unknown' for r in self.bundle['scenarios']['unverified']['checks']))
    def test_login_dispatch_inconclusive(self):
        startup=self.bundle['scenarios']['startup-inconclusive']['checks'][-1]
        self.assertEqual(startup['state'],'unknown')
        self.assertEqual(startup['detail_code'],'startup_dispatch_unconfirmed')


if __name__=='__main__':unittest.main()
