"""Pure command parsing; no Windows readers activated."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.windows_readers import candidate_arguments,WindowsReaders,norm

class CandidateIdentityTests(unittest.TestCase):
    def test_fixed_candidate_and_worker(self):
        image=norm(ROOT/'.venv/Scripts/pythonw.exe')
        for script,suffix,worker in [('agent/development/reliable_bootstrap.py',[],False),('agent/windows/graceful_launcher.py',['_worker'],True)]:
            args=[image,'-I','-B',str(ROOT/script),*suffix]
            self.assertEqual(candidate_arguments(args,{image},ROOT),(True,worker))

    def test_no_basename_or_flag_shortcuts(self):
        image=norm(ROOT/'.venv/Scripts/pythonw.exe')
        valid=[image,'-I','-B',str(ROOT/'agent/development/reliable_bootstrap.py')]
        for args in (valid+['--start'],[image,valid[-1]],[image,'-c','x'],[image,'-I','-B',str(ROOT/'other/reliable_bootstrap.py')],['other.exe',*valid[1:]]):
            self.assertEqual(candidate_arguments(args,{image},ROOT),(False,False))

    def test_candidate_opt_in_is_not_default(self):
        self.assertFalse(WindowsReaders().candidate)
        self.assertTrue(WindowsReaders(candidate=True).candidate)
        with self.assertRaises(ValueError):WindowsReaders(candidate='true')

if __name__=='__main__':unittest.main()
