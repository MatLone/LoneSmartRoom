"""Mock processes/guards only; no operational launch, registry or credentials."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests')]
from test_agent_launcher import FakeWindows
spec=importlib.util.spec_from_file_location('reliable_candidate',ROOT/'agent/development/reliable_bootstrap.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BootstrapTests(unittest.TestCase):
    def run_case(self,results=(0,),guard=None,attempts=1):
        layout=m.Layout(ROOT);layout_validate=Mock();log=Mock()
        children=[SimpleNamespace(wait=Mock(return_value=n)) for n in results]
        spawn=Mock(side_effect=children);sleep=Mock()
        with patch.object(m.Layout,'validate',layout_validate),patch.object(m,'environment_valid',return_value=True):
            code=m.supervise(layout,FakeWindows(),log,popen=spawn,
                guard=guard or Mock(return_value=False),pause=sleep,attempts=attempts)
        return code,spawn,sleep,log

    def test_fixed_spawn_and_normal_stop(self):
        code,spawn,_,_=self.run_case();self.assertEqual(code,0)
        args=spawn.call_args
        self.assertEqual(args.args[0],[str(m.Layout(ROOT).python),'-I','-B',str(ROOT/'agent/windows/graceful_launcher.py'),'_worker'])
        self.assertFalse(args.kwargs['shell']);self.assertEqual(args.kwargs['cwd'],str(ROOT))

    def test_default_no_retry(self):
        code,spawn,sleep,_=self.run_case((17,));self.assertEqual(code,17)
        self.assertEqual(spawn.call_count,1);sleep.assert_not_called()

    def test_bounded_opt_in_recovery(self):
        code,spawn,sleep,_=self.run_case((17,17,0),attempts=3)
        self.assertEqual(code,0);self.assertEqual(spawn.call_count,3)
        self.assertEqual([x.args[0] for x in sleep.call_args_list],[5,10])

    def test_duplicate_and_security_terminal(self):
        for n in (10,11,13,18,21):
            code,spawn,sleep,_=self.run_case((n,),attempts=3)
            self.assertEqual(code,n);self.assertEqual(spawn.call_count,1);sleep.assert_not_called()

    def test_guard_stops_before_any_spawn(self):
        code,spawn,_,_=self.run_case(guard=Mock(return_value=True))
        self.assertEqual(code,13);spawn.assert_not_called()

    def test_recovery_guard_rechecked(self):
        code,spawn,_,_=self.run_case((17,),guard=Mock(side_effect=[False,True]),attempts=2)
        self.assertEqual(code,13);self.assertEqual(spawn.call_count,1)

    def test_startup_command_quotes_spaces(self):
        command=m.startup_command(m.Layout(ROOT));self.assertIn('"',command)
        self.assertIn('-I -B',command);self.assertNotIn('serve',command)

    def test_external_arguments_rejected_before_windows_api(self):
        with patch.object(m,'Windows',side_effect=AssertionError('no native access')):
            self.assertEqual(m.main(['--arbitrary']),20)


if __name__=='__main__': unittest.main()
