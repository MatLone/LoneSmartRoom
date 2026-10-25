"""Guarded lifecycle suite: only toy processes/events and ephemeral loopback TCP.

Never allows port 8776, operational event namespace, production agent launch or
access to operational DPAPI data. No package/dependency installation.
"""
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
MODULES=('test_graceful_shutdown','test_local_shutdown_native')

def main():
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in MODULES)
    from local_shutdown import LocalEvents
    from launcher_win32 import Windows
    from secure_store import DPAPI
    elevated=Windows().elevated
    original_popen,original_bind,original_connect,original_connect_ex=(subprocess.Popen,socket.socket.bind,socket.socket.connect,socket.socket.connect_ex)
    original_create,original_request=LocalEvents.create,LocalEvents.request
    allocated=set()
    helper=str(ROOT/'tests/graceful_substitute.py')
    def toy_only(args,*a,**kw):
        if not (isinstance(args,list) and len(args)==6 and Path(args[0]).resolve()==Path(sys.executable).resolve()
                and args[1:4]==['-I','-B',helper] and args[4] in ('worker','slow','supervisor','supervisor-crash')
                and args[5].startswith('Global\\LoneSmartRoom.GracefulTests.')):
            raise AssertionError('Real process denied')
        return original_popen(args,*a,**kw)
    def bind(sock,address):
        if address[0]!='127.0.0.1' or address[1]==8776 or address[1] not in (0,*allocated):
            raise AssertionError('Non-fixture bind denied')
        result=original_bind(sock,address)
        port=sock.getsockname()[1]
        if port==8776:
            sock.close();raise AssertionError('Reserved production port refused')
        allocated.add(port);return result
    def connect(sock,address):
        if address[0]!='127.0.0.1' or address[1]==8776 or address[1] not in allocated:
            raise AssertionError('Non-fixture connect denied')
        return original_connect(sock,address)
    def connect_ex(sock,address):
        if address[0]!='127.0.0.1' or address[1]==8776 or address[1] not in allocated:
            raise AssertionError('Non-fixture connect denied')
        return original_connect_ex(sock,address)
    def channel_create(self,name):
        if not name.startswith('Global\\LoneSmartRoom.GracefulTests.'):raise AssertionError('Production event denied')
        return original_create(self,name)
    def channel_request(self,name,*a,**kw):
        if not name.startswith('Global\\LoneSmartRoom.GracefulTests.'):raise AssertionError('Production stop denied')
        return original_request(self,name,*a,**kw)
    with patch('subprocess.Popen',side_effect=toy_only),patch.object(socket.socket,'bind',bind), \
            patch.object(socket.socket,'connect',connect),patch.object(socket.socket,'connect_ex',connect_ex), \
            patch.object(LocalEvents,'create',channel_create),patch.object(LocalEvents,'request',channel_request), \
            patch.object(DPAPI,'open',side_effect=AssertionError('Operational decryption denied')):
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    residual=[thread.name for thread in threading.enumerate() if thread.name.startswith(('lsr-https','lsr-stop-deadline','lsr-app-launch'))]
    receipt={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'ok':result.wasSuccessful(),'testContextElevated':elevated,
        'productionEventsAllowed':False,'productionCredentialsAllowed':False,'port8776Allowed':False,
        'processesAllowed':'disposable test helper only','networkAllowed':'ephemeral IPv4 loopback fixtures only',
        'residualLifecycleThreads':residual}
    folder=ROOT/'.cache/validation/graceful-shutdown-2026-10-24';folder.mkdir(parents=True,exist_ok=True)
    (folder/'tests.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
    return 0 if result.wasSuccessful() and not result.skipped and not residual else 1

if __name__=='__main__':raise SystemExit(main())
