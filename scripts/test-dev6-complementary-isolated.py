"""Tests only; the audit hook rejects any native collection or subprocess."""
import ctypes
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/monitoring')]
def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('ctypes.dlopen','ctypes.call_function','subprocess.Popen','os.system','os.startfile','os.startfile/2','os.exec','os.posix_spawn'):
        raise RuntimeError('Physical operations forbidden in complementary mocks')
if __name__=='__main__':
    sys.addaudithook(deny)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_dev6_complementary'))
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'realSensors':False,'nativeProcesses':False,'countersScope':'fixture_only_at_provider_admission_not_operational_telemetry'}
    out=ROOT/'.cache/validation/dev6-complementary-plan-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    (out/'admission-python-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report));raise SystemExit(0 if report['ok'] else 1)
