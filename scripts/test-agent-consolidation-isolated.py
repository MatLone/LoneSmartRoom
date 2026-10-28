"""Loopback fixtures only; production state, DPAPI, subprocesses and 8776 denied."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT),str(ROOT/'agent/windows')]
from secure_store import DPAPI
allocated=set();original_bind=socket.socket.bind;original_connect=socket.socket.connect
original_read=Path.read_bytes

def bind(sock,address):
    if address!=('127.0.0.1',0):raise AssertionError('fixture bind only')
    result=original_bind(sock,address);allocated.add(sock.getsockname()[1]);return result

def connect(sock,address):
    if address[0]!='127.0.0.1' or address[1] not in allocated or address[1]==8776:raise AssertionError('fixture connect only')
    return original_connect(sock,address)

def read(path):
    if '.runtime' in path.parts:raise AssertionError('production state forbidden')
    return original_read(path)

def main():
    names=['test_reliable_bootstrap','test_candidate_runtime','test_candidate_identity','test_supervision_policy','test_desktop_evidence','test_agent_launcher','test_diagnostic_readers']
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
    start=time.perf_counter();cpu=time.process_time()
    with patch('subprocess.Popen',side_effect=AssertionError('process forbidden')),patch.object(DPAPI,'__init__',side_effect=AssertionError('production secrets forbidden')),patch.object(Path,'read_bytes',read),patch.object(socket.socket,'bind',bind),patch.object(socket.socket,'connect',connect):
        result=unittest.TextTestRunner(verbosity=1).run(suite)
    report=dict(ok=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),elapsed_seconds=time.perf_counter()-start,process_cpu_seconds=time.process_time()-cpu,hardware_collection=False,production_state_allowed=False,production_listener_allowed=False)
    out=ROOT/'.cache/validation/agent-consolidation';out.mkdir(parents=True,exist_ok=True)
    (out/'python-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
