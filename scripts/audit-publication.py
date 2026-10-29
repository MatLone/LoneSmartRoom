"""Offline, read-only Git history audit. Reports locations/rules, never matched secrets.

Heuristics are not proof of absence. Does not upload, rewrite Git, or alter originals.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GIT = ['git', '-c', 'safe.directory=' + ROOT.as_posix(), '-c', 'core.quotepath=false']
def git(*args):
    return subprocess.check_output(GIT + list(args), cwd=ROOT)

def run():
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / '.cache' / 'github-publication' / stamp
    out.mkdir(parents=True, exist_ok=False)
    refs = git('for-each-ref', '--format=%(refname) %(objectname)').decode().splitlines()
    (out/'refs.txt').write_text('\n'.join(refs)+'\n', encoding='utf-8')
    (out/'working.patch').write_bytes(git('diff', '--binary', 'HEAD'))
    entries = []
    for line in git('status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0'):
        if not line: continue
        name = line[3:].decode('utf-8')
        source = ROOT / name
        if source.is_file():
            data = source.read_bytes()
            dest = out / 'working-tree' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            entries.append({'path':name, 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)})
    (out/'checkpoint.json').write_text(json.dumps({'head':git('rev-parse','HEAD').decode().strip(),'refs':refs,'working_files':entries},indent=2),encoding='utf-8')
    patterns = {
        'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----',
        'github_token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{30,255})\b',
        'aws_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
        'service_token': rb'\b(?:xox[baprs]-[A-Za-z0-9-]{20,}|AIza[A-Za-z0-9_-]{35}|sk-(?:proj-)?[A-Za-z0-9_-]{30,})\b',
        'personal_windows_path': rb'[A-Za-z]:[\\/]+Users[\\/]+(?!Public\b|Default\b|USER\b|<|\$|%)[^\\/\r\n\x00"\']{2,60}',
        'private_network': rb'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
        'credential_literal': rb'(?i)(?:password|api_key|api_secret|hmac_key|auth_token|pairing_code)\s*[=:]\s*["\'][^"\'\r\n]{8,160}["\']',
    }
    compiled={k:re.compile(v) for k,v in patterns.items()}
    sensitive_path=re.compile(r'(?i)(?:^|/)(?:\.env(?:\..*)?|credentials\.json|secrets\.json|agent_config\.json)$|\.(?:jks|keystore|p12|pfx|pem|key|dpapi|db|sqlite3?)$')
    generated=re.compile(r'(?i)(?:^|/)(?:node_modules|\.venv|\.cache|\.runtime|recovery)/|\.(?:apk|aab|exe|dmp|log|hprof)$')
    objects={}
    for line in git('rev-list','--objects','--all').decode('utf-8').splitlines():
        oid,_,name=line.partition(' ')
        objects[oid]=name
    findings=[]; total=0; binaries=0; blobs=0
    proc=subprocess.Popen(GIT+['cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,name in objects.items():
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
        head=proc.stdout.readline().decode().split();size=int(head[2]);data=proc.stdout.read(size);proc.stdout.read(1)
        total+=size
        if head[1] not in ('blob','commit','tag'):continue
        if head[1]=='blob':
            blobs+=1
            if sensitive_path.search(name):findings.append({'rule':'sensitive_filename','object':oid,'path':name})
            if generated.search(name):findings.append({'rule':'generated_or_operational_file','object':oid,'path':name})
        if b'\x00' in data:
            binaries+=1
            continue
        for rule,pattern in compiled.items():
            matches=list(pattern.finditer(data))
            if matches:findings.append({'rule':rule,'object':oid,'path':name,'count':len(matches),'lines':[data[:m.start()].count(b'\n')+1 for m in matches[:8]]})
    proc.stdin.close();proc.wait()
    # Uncommitted files are part of the candidate, too.
    for entry in entries:
        data=(ROOT/entry['path']).read_bytes()
        if sensitive_path.search(entry['path']):findings.append({'rule':'sensitive_filename','path':entry['path'],'working_tree':True})
        for rule,pattern in compiled.items():
            if pattern.search(data):findings.append({'rule':rule,'path':entry['path'],'working_tree':True})
    counts={k:sum(f['rule']==k for f in findings) for k in sorted({f['rule'] for f in findings})}
    report={'head':git('rev-parse','HEAD').decode().strip(),'refs':len(refs),'commits':int(git('rev-list','--all','--count')),'objects':len(objects),'blobs':blobs,'binary_objects_not_content_scanned':binaries,'bytes_examined':total,'rule_counts':counts,'findings':findings,'push_performed':False,'limitations':['Heuristic audit; binary payloads require separate format review','Synthetic test credentials require manual triage','Object paths reflect one historical name; audit is by unique object identity']}
    (out/'audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'directory':str(out),'commits':report['commits'],'objects':len(objects),'blobs':blobs,'rule_counts':counts,'working_checkpoint_files':len(entries)},ensure_ascii=False))

if __name__ == '__main__':run()
