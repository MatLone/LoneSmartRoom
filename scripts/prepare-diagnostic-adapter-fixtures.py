"""Test-only mock interoperability fixtures; no readers or runtime wiring."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.mock_evidence import reports


def build():
    data={name:{'schema_version':1,'simulation':True,'report':value['report'],'security':value['audit']['security']} for name,value in reports().items()}
    return json.dumps({'schema_version':1,'simulation':True,'scenarios':data},indent=2,ensure_ascii=False)+'\n'


if __name__=='__main__':
    if sys.argv[1:] not in ([],['--check']):raise ValueError('fixed_arguments_required')
    path=ROOT/'tests/fixtures/diagnostic-evidence.json';data=build()
    if sys.argv[1:]:assert path.read_text(encoding='utf-8')==data,'adapter_fixture_drift'
    else:path.write_text(data,encoding='utf-8',newline='\n')
    print(json.dumps({'ok':True,'simulatedOnly':True,'operationalReaders':False,'scenarios':14}))
