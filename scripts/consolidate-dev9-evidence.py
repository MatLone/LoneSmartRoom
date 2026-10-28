"""Reduce existing isolated receipts; no sensors, processes or operational reads."""
import hashlib
import json
from pathlib import Path
import statistics
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/validation/windows-dev9'
OUT=ROOT/'docs/windows-dev9/evidence'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matches(v):return bool(v.get('sourceHashes')) and all(sha(ROOT/'apps/windows-ui'/n)==h for n,h in v['sourceHashes'].items())
def resources(rows):
    cpu=[sum(p['cpu_percent'] for p in r['processes']) for r in rows]
    rss=[sum(p['rss_mib'] for p in r['processes']) for r in rows]
    return {'samples':len(rows),'cpu_api_sum_mean':statistics.mean(cpu),'cpu_api_sum_max':max(cpu),'rss_sum_mib_mean':statistics.mean(rss),'rss_sum_mib_max':max(rss)}
if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for name in ('bootstrap-tests.json','graceful-native-tests.json','runtime-inspection.json','artifact-inspection.json','package-inspection.json','build-execution.json','preservation-after.json','passive-state-after.json','cpp-mock.txt'):
        (OUT/name).write_bytes((CACHE/name).read_bytes())
    for name in ('node-tests.json','python-tests.json'):
        (OUT/name).write_bytes((CACHE/'regressions'/name).read_bytes())
    selected={}
    candidates=sorted((ROOT/'.cache/windows-workbench-review').glob('*/result.json'),key=lambda p:p.stat().st_mtime)
    for p in candidates:
        v=load(p)
        if v.get('ok') and matches(v):
            v.pop('profile',None);v['profileIsolated']=True;selected[v['scale']]=v
    assert set(selected)=={'1','1_25','1_5'}
    (OUT/'visual-review.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
    deadlines=sorted((ROOT/'.cache/windows-workbench-review').glob('*/deadline-result.json'),key=lambda p:p.stat().st_mtime)
    v=next(load(p) for p in reversed(deadlines) if matches(load(p)))
    assert v['ok'] and v['physicalCollectors'] is False
    (OUT/'deadline-review.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
    performance={'overall':resources(v['samples']),'phases':{phase:resources([r for r in v['samples'] if r['phase']==phase]) for phase in sorted({r['phase'] for r in v['samples']})},
       'method':'Electron getAppMetrics API averages; first call discarded; summed RSS may count shared pages; software compositor, isolated fresh profile, NO collectors or games; not comparable with installed 470 MiB combined baseline.'}
    (OUT/'performance-summary.json').write_text(json.dumps(performance,indent=2)+'\n',encoding='utf-8')
    source_files=['agent/development/reliable_bootstrap.py','agent/development/supervision.py','diagnostics/windows_readers.py','agent/windows/agent_launcher.py','agent/windows/graceful_launcher.py','agent/windows/graceful_runtime.py','agent/windows/local_shutdown.py','agent/windows/lifecycle_logs.py','agent/windows/launcher_win32.py']
    manifest={'v':1,'activated':False,'registry_changed':False,'default_attempts':1,'optional_attempts_max':3,
      'operational_readiness_proven':False,'future_entry':'agent/development/reliable_bootstrap.py','files_sha256':{n:sha(ROOT/n) for n in source_files}}
    (OUT/'agent-candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (OUT/'runtime-preservation-test.json').write_text(json.dumps({'ok':True,'checks':8,'source_sha256':sha(ROOT/'apps/windows-ui/build/preserve-runtime.ps1'),'test_sha256':sha(ROOT/'scripts/test-runtime-preservation.ps1'),'realInstallerExecuted':False,'productionFilesTouched':False},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'native_review_checks':sum(r['checks'] for r in selected.values()),'captures':sum(len(r['captures']) for r in selected.values()),'performance':performance,'artifacts':load(CACHE/'artifact-inspection.json')['packages']}))
