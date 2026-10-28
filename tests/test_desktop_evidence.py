"""No native readers, credentials, Registry, sensors or HTTP are activated."""
from datetime import datetime,timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from diagnostics.desktop_evidence import collect

class DesktopEvidenceTests(unittest.TestCase):
    def reader(self,verified=False):
        now=datetime.now(timezone.utc)
        return Mock(census=Mock(return_value=dict(agent_verified=verified,listener_count=1 if verified else 0,
            monitoring_census_complete=True,application_count=0,monitoring_count=0,
            pipe_namespace=dict(available=True,matching_count=0),startup=dict(configured=True),
            observed_at=now.isoformat(),observed_monotonic=100)))
    def test_offline_not_failure_or_fake_authentication(self):
        reader=self.reader();report=collect(reader,clock=lambda:100)
        rows={r['component']:r for r in report['checks']}
        self.assertEqual(rows['listener_8776']['state'],'offline')
        self.assertEqual(rows['agent_https']['state'],'unknown')
        self.assertEqual(rows['agent_startup']['state'],'unknown')
        self.assertFalse(report['simulation']);self.assertFalse(report['repair_capability'])
        reader.status.assert_not_called();reader.database.assert_not_called();reader.close.assert_called_once()
    def test_process_and_listener_not_authentication(self):
        reader=self.reader(True);rows={r['component']:r for r in collect(reader,clock=lambda:100)['checks']}
        self.assertEqual(rows['listener_8776']['state'],'healthy');self.assertEqual(rows['agent_https']['state'],'unknown')
        self.assertEqual(rows['agent_startup']['state'],'unknown')
        self.assertEqual(rows['cpu_collector']['detail_code'],'application_normally_inactive')
    def test_failure_and_deadline_close_handles(self):
        reader=self.reader();reader.census.side_effect=ValueError('private path must not be serialized')
        with self.assertRaises(ValueError):collect(reader,clock=lambda:100)
        reader.close.assert_called_once()
        reader=self.reader()
        with self.assertRaises(TimeoutError):collect(reader,clock=Mock(side_effect=[100,113]))
        reader.close.assert_called_once()
    def test_only_fixed_reader_methods_used(self):
        reader=self.reader();report=collect(reader,clock=lambda:100)
        self.assertEqual([c[0] for c in reader.method_calls],['begin','census','close'])
        import json
        data=json.dumps(report)
        for word in ('secret','token','certificate','command','C:\\Users'):self.assertNotIn(word,data)
    def test_owned_inventory_helper_is_reaped_before_reader_closes(self):
        reader=self.reader();child=Mock();reader.scanners=[child]
        reader.close.side_effect=lambda:child.wait.assert_called_once()
        collect(reader,clock=lambda:100)
        reader.close.assert_called_once()

if __name__=='__main__':unittest.main()
