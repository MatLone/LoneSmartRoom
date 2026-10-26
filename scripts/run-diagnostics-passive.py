"""Single authorized passive audit, never an application startup or repair tool."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'.cache/validation/diagnostics-passive-2026-10-26'
sys.path.insert(0,str(ROOT))


def gates():
    receipt=json.loads((PHASE/'tests-summary.json').read_text())
    if not (receipt.get('ok') is True and receipt.get('errors')==0 and
            receipt.get('failures')==0 and receipt.get('externalOperationsDenied') is True):
        raise ValueError('isolated_tests_required')
    for name,expected in receipt['sourceHashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('tested_sources_changed')
    preservation=json.loads((PHASE/'preservation-before.json').read_text())
    if not (preservation.get('ok') is True and preservation.get('zeroGrants') is True):
        raise ValueError('preservation_gate_required')


def main():
    if sys.argv[1:]!=['--once']:raise ValueError('explicit_single_session_required')
    gates()
    # Exclusive marker prevents silently repeating the authorized real session.
    with (PHASE/'SESSION-CONSUMED.json').open('x',encoding='utf-8') as marker:
        json.dump({'started_at':datetime.now(timezone.utc).isoformat(),'limit_seconds':60},marker)
    from diagnostics.passive import run_session
    from diagnostics.windows_readers import WindowsReaders
    result=run_session(WindowsReaders())
    (PHASE/'session.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'completed':result['completed'],'elapsed_seconds':result['elapsed_seconds'],
        'within_limit':result['within_limit'],'stop_code':result.get('stop_code'),
        'evidence':'.cache/validation/diagnostics-passive-2026-10-26/session.json'}))
    return 0 if result['completed'] else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError):
        print('{"completed":false,"stop_code":"passive_gate_or_output_failed"}');raise SystemExit(1)
