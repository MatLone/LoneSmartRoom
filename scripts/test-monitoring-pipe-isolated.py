"""Mock-only security suite, fails on native sensors, libraries, network or process creation."""
import ctypes
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'tests',ROOT/'tests/monitoring'):sys.path.insert(0,str(p))


def deny(event,args):
    if event.startswith(('socket.','winreg.')) or event in ('subprocess.Popen','os.system','os.startfile',
            'os.startfile/2','ctypes.dlopen','ctypes.call_function','os.posix_spawn','os.exec'):
        raise RuntimeError('External operation forbidden in mock suite')


def main():
    sys.addaudithook(deny)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_pipe_transport'))
    from monitoring.basic_validation import source_hashes
    receipt={'ok':result.wasSuccessful() and not result.skipped,'tests':result.testsRun,'failures':len(result.failures),
             'errors':len(result.errors),'skipped':len(result.skipped),'real_sensors':False,'native_dlls_allowed':False,
             'source_hashes':source_hashes(ROOT)}
    out=ROOT/'.cache/validation/monitoring-electron-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    (out/'mock-tests.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='source_hashes'}))
    return 0 if receipt['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
