"""Gate only. Never executes the physical session; verifies completed test receipts."""
import json
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from monitoring.basic_validation import source_hashes as basic_hashes
from monitoring.development_gate import source_hashes


def main():
    folder=ROOT/'.cache/validation/monitoring-electron-2026-10-25'
    read=lambda name:json.loads((folder/name).read_text(encoding='utf-8-sig'))
    basic=json.loads((ROOT/'.cache/validation/monitoring-basic-2026-10-25/simulated-tests.json').read_text())
    mocks=read('mock-tests.json');native=read('native-pipe-tests.json');visual=read('simulated/electron-result.json')
    state=read('physical-agent-before.json');preserved=read('preservation-before.json')
    current=source_hashes(ROOT)
    assert basic['ok'] and basic['tests']==133 and basic['source_hashes']==basic_hashes(ROOT)
    assert mocks['ok'] and mocks['source_hashes']==basic_hashes(ROOT)
    assert native['ok'] and native['checks']>=15 and native['source_hashes']==current
    assert visual['ok'] and visual['simulated'] and visual['transport']['cleanStop']
    assert all(visual['sourceHashes'].get(k)==v for k,v in current.items()),'Visual test source changed'
    assert state['identityGatePassed'] and state['collectorProcesses']==0 and state['listenerCount']==1
    assert preserved['ok'] and preserved['zeroGrants'] and preserved['protectedDifferences']==0
    assert not (folder/'physical-attempt.json').exists(),'The single physical attempt was already used'
    report={'ok':True,'utc':datetime.now(timezone.utc).isoformat(),'agentIdentityVerified':True,
            'basicTests':133,'pipeMockTests':mocks['tests'],'nativePipeChecks':native['checks'],
            'nativeElectronSimulatedChecks':visual['checks'],'source_hashes':current,'realSessionStarted':False}
    (folder/'physical-gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}))


if __name__=='__main__':main()
