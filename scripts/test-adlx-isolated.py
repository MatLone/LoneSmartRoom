"""ADLX fixture suite with native loads, sensors, process creation, sockets and Registry denied."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT,ROOT/'tests/monitoring'):sys.path.insert(0,str(path))


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('ctypes.dlopen','ctypes.call_function','subprocess.Popen',
            'os.system','os.startfile','os.startfile/2','os.exec','os.posix_spawn'):
        raise RuntimeError('Native operations forbidden in ADLX mock suite')


def main():
    sys.addaudithook(deny)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_adlx_provider'))
    files=['monitoring/adlx_provider.py','monitoring/contracts.py','tests/monitoring/test_adlx_provider.py']
    report={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,'errors':len(result.errors),
        'failures':len(result.failures),'skipped':len(result.skipped),'nativeADLXLoaded':False,'realSensors':False,
        'sourceHashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}}
    out=ROOT/'.cache/validation/adlx-preparation-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    (out/'adlx-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='sourceHashes'}));return 0 if report['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
