"""Mocks only: no native DLLs, sensors, processes or operational application."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import os

from monitoring.lifetime import duration_for,end_at,finish_collector
from monitoring.application_context import validate_mode,application_owner


class LifetimeTests(unittest.TestCase):
    def test_default_bounded_development_and_explicit_application(self):
        self.assertEqual(duration_for(),70)
        self.assertEqual(duration_for(15),15)
        self.assertIsNone(duration_for(application=True))
        self.assertEqual(end_at(10,None),float('inf'))
        self.assertEqual(end_at(10,15),25)

    def test_invalid_or_ambiguous_lifetime_rejected(self):
        for value in (0,76,True,-1,1.5,'70'):
            with self.assertRaises(ValueError):duration_for(value)
        with self.assertRaises(ValueError):duration_for(70,True)

    def test_normal_stop_called_once(self):
        collector=Mock();collector.stop.return_value=SimpleNamespace(stopped=True,clean=True)
        pending=Mock();self.assertTrue(finish_collector(collector,pending).clean)
        collector.stop.assert_called_once_with(3);pending.assert_not_called()

    def test_timeout_waits_for_actual_owned_collector_no_kill_or_false_success(self):
        collector=Mock();pending=Mock();collector.stop.side_effect=[SimpleNamespace(stopped=False),SimpleNamespace(stopped=False),SimpleNamespace(stopped=True,clean=True)]
        self.assertTrue(finish_collector(collector,pending).clean);pending.assert_called_once()
        self.assertEqual([c.args for c in collector.stop.call_args_list],[(3,),(0.25,),(0.25,)])

    def test_closed_with_cleanup_error_preserves_failure(self):
        collector=Mock();collector.stop.return_value=SimpleNamespace(stopped=True,clean=False)
        self.assertFalse(finish_collector(collector).clean)

    def test_bundle_cannot_run_fixtures_or_duration_only(self):
        workspace=Path(__file__).resolve().parents[2];cache=workspace/'.cache/tests';cache.mkdir(parents=True,exist_ok=True)
        assert cache.resolve().is_relative_to(workspace)
        with tempfile.TemporaryDirectory(dir=cache,prefix='application-mode-') as folder:
            root=Path(folder)
            self.assertFalse(validate_mode(root,False,True))
            with self.assertRaises(PermissionError):validate_mode(root,True,False)
            (root/'BUNDLED-MONITORING.json').write_text('{}')
            self.assertTrue(validate_mode(root,True,False))
            for application,simulated in [(True,True),(False,False),(False,True)]:
                with self.assertRaises(PermissionError):validate_mode(root,application,simulated)

    def test_application_owner_identity_and_handle_cleanup(self):
        root=Path('C:/test install/resources/monitoring/code').resolve()
        api=Mock();api.own={'image':os.path.normcase(os.path.realpath(root.parent/'runtime/python.exe')),'sid':'test-sid','session':4}
        parent={'image':os.path.normcase(os.path.realpath(root.parents[2]/'Lone Smart Room.exe')),'sid':'test-sid','session':4,'elevated':False}
        api.identity.return_value=parent;api.hold_process.return_value=99;api.alive.return_value=True
        with patch('monitoring.application_context.os.getppid',return_value=12):
            self.assertEqual(application_owner(api,root,12),99)
            for key,value in [('sid','wrong'),('session',5),('elevated',True),('image','C:/unexpected.exe')]:
                api.identity.return_value={**parent,key:value}
                with self.assertRaises(PermissionError):application_owner(api,root,12)
            api.close.assert_called_with(99)
            with self.assertRaises(PermissionError):application_owner(api,root,13)


if __name__=='__main__':unittest.main()
