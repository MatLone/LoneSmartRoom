"""Frozen UI demonstrations from the approved pure diagnostic v1 reducer.

No Windows reader, network, process or sensor is instantiated. --check writes
nothing. No telemetry measurements are exported to the desktop fixtures.
"""
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.contracts import Component as C,DetailCode as D,Outcome as O,Probe
from diagnostics.engine import DiagnosticEngine
from diagnostics.simulated import SimulatedProvider
from diagnostics.adapters import ReceiptProvider
from diagnostics.evidence import FixtureReader
from diagnostics.scenarios import NOW,receipt,status_payload,monitoring_payload,startup_payload
from diagnostics.presentation import PRIMARY_CODES,LABELS,DETAILS,FALLBACK_TEXT,present


def inputs():
    startup=startup_payload()  # No proof of login dispatch in the default demo.
    return {C.HTTPS:status_payload(),
        C.LISTENER:dict(schema_version=1,port=8776,present=True,image_verified=True,creation_verified=True,parent_verified=True),
        C.IPC:dict(schema_version=1,connected=True,local=True,sid_verified=True,session_verified=True,server_identity_verified=True,contract_version=1,result='ok'),
        C.CPU:monitoring_payload(C.CPU),C.GPU:monitoring_payload(C.GPU),C.RAM:monitoring_payload(C.RAM),
        C.ADLX:dict(schema_version=1,running=True,library_verified=True,last_frame='valid',ingress_age_seconds=.25,sample_age_seconds=0),
        C.STARTUP:startup}


def build_data():
    scenarios={}
    for name in ('overview','healthy','inactive','offline','listener-mismatch','auth-failure',
                 'pipe-absent','sensor-unavailable','stale','provider-error','unverified',
                 'recovered','startup-inconclusive'):
        data=inputs()
        if name=='healthy':data[C.STARTUP]['dispatch_proven']=True
        if name=='offline':
            data[C.HTTPS]=status_payload(result='connection_refused',http_status=None,
                tls_verified=None,hostname_verified=None,pin_verified=None,hmac_request_used=None)
            data[C.LISTENER]['present']=False
        if name=='listener-mismatch':data[C.LISTENER]['image_verified']=False
        if name=='auth-failure':data[C.HTTPS]['http_status']=401
        if name=='pipe-absent':data[C.IPC].update(connected=False,result='disconnected')
        if name=='sensor-unavailable':
            data[C.GPU]=monitoring_payload(C.GPU,state='unsupported')
            data[C.ADLX].update(last_frame='unavailable',ingress_age_seconds=None,sample_age_seconds=None)
        if name=='stale':
            for c in (C.CPU,C.GPU,C.RAM):data[c]=monitoring_payload(c,age=12)
            data[C.ADLX]['sample_age_seconds']=12
        providers=[ReceiptProvider(c,FixtureReader([receipt(payload)])) for c,payload in data.items()]
        if name=='unverified':providers=[]
        if name=='provider-error':
            providers=[p for p in providers if p.component!=C.CPU]+[SimulatedProvider(C.CPU,[RuntimeError('fixture-private-error')])]
        if name=='inactive':
            for c in (C.CPU,C.GPU,C.RAM,C.ADLX,C.IPC):
                facts=({'running':False,'dll_verified':None,'sample_valid':None,'sample_stale':None} if c==C.ADLX else
                       {'connected':False,'peer_validated':None,'contract_version':1} if c==C.IPC else
                       {'collector_running':False,'sample_valid':None,'sample_stale':None})
                providers=[p for p in providers if p.component!=c]+[SimulatedProvider(c,[
                    Probe(c,NOW,100,facts,O.UNAVAILABLE,detail_code=D.NORMAL_INACTIVE)])]
        if name=='recovered':
            failure=Probe(C.HTTPS,NOW,100,dict(responded=True,authenticated=False,tls_verified=True),detail_code=D.AUTH_FAILED)
            good=ReceiptProvider(C.HTTPS,FixtureReader([receipt(status_payload(),now=NOW+timedelta(seconds=1),monotonic=101)])).read()
            providers=[p for p in providers if p.component!=C.HTTPS]+[SimulatedProvider(C.HTTPS,[failure,good])]
            engine=DiagnosticEngine(providers)
            first=engine.collect(NOW,100)
            assert first['checks'][0]['state']=='error'
            report=engine.collect(NOW+timedelta(seconds=1),101)
            assert report['checks'][0]['state']=='healthy'
        else:report=DiagnosticEngine(providers).collect(NOW,100)
        present(report)  # Existing validated presentation also accepts every fixture.
        scenarios[name]=report
    contract={'schema':1,'components':[c.value for c in C],
        'states':sorted(LABELS),'codes':sorted(PRIMARY_CODES),
        'details':[d.value for d in D],'messages':{d.value:v for d,v in DETAILS.items()},
        'fallback':FALLBACK_TEXT}
    script="'use strict';\n// Generated from the approved Python diagnostic v1 contract.\n"+\
        "(function(root){const data="+json.dumps(contract,ensure_ascii=False,separators=(',',':'))+\
        ";if(typeof module==='object'&&module.exports)module.exports=data;else root.loneDiagnosticContract=data;})(typeof window==='object'?window:globalThis);\n"
    bundle={'v':1,'simulation':True,'clock_policy':'frozen','scenarios':scenarios}
    return script,json.dumps(bundle,ensure_ascii=False,indent=2)+'\n'


def main():
    if sys.argv[1:] not in ([],['--check']):raise ValueError('invalid_arguments')
    script,bundle=build_data();directory=ROOT/'apps/windows-ui'
    files={'diagnostics-contract.js':script,'diagnostics-fixtures.json':bundle}
    if sys.argv[1:]==['--check']:
        assert all((directory/n).read_text(encoding='utf-8')==data for n,data in files.items()),'generated_fixture_drift'
    else:
        for name,data in files.items():(directory/name).write_text(data,encoding='utf-8',newline='\n')
    print(json.dumps({'ok':True,'simulated':True,'scenarios':13,'operationalReaders':False,'checkOnly':bool(sys.argv[1:])}))


if __name__=='__main__':main()
