from pathlib import Path
import sys,importlib.util,http.client,json,collections,time,ssl
ROOT=Path.cwd();OUT=ROOT/'.cache/validation/final-review-2026-10-24'
spec=importlib.util.spec_from_file_location('review_app_tests',ROOT/'tests/test_app_commands.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
Case=module.AppCommandTests;Case.setUpClass();case=Case('test_strict_json_duplicate_headers_and_limits');case.setUp();trials=[]
assert Path(case.temp.name).resolve().is_relative_to((ROOT/'.cache/tests').resolve())
try:
 device=case.device(('steam',));path='/v2/apps/commands'
 cases=[('json-invalid-small',b'{bad',False),('json-invalid-1024',b'x'*1024,False),('oversized-1025-sent',b'x'*1025,False),('oversized-1025-header-only',b'x'*1025,True)]
 for index in range(12):
  for name,body,header_only in cases:
   entry={'case':name,'iteration':index+1,'declaredBytes':len(body),'sentBytes':0 if header_only else len(body),'status':None,'responseBytes':0}
   connection=http.client.HTTPSConnection('127.0.0.1',case.server.server_port,timeout=4,context=case.context)
   stage='connect-send'
   try:
    headers=case.headers(device,'POST',path,body);headers['Content-Length']=str(len(body))
    connection.request('POST',path,body=None if header_only else body,headers=headers)
    stage='read-status';response=connection.getresponse();entry['status']=response.status;entry['declaredResponseBytes']=int(response.getheader('Content-Length','0'))
    stage='read-body';raw=response.read();entry['responseBytes']=len(raw);entry['responseOkFalse']=json.loads(raw).get('ok') is False
    entry['outcome']='complete'
   except (OSError,http.client.HTTPException,ValueError) as error:
    entry.update(outcome='error',stage=stage,errorType=type(error).__name__,winerror=getattr(error,'winerror',None),errno=getattr(error,'errno',None))
   finally:connection.close()
   trials.append(entry)
 summary={}
 for name,_,_ in cases:
  subset=[t for t in trials if t['case']==name]
  summary[name]={'trials':len(subset),'completeResponses':sum(t['outcome']=='complete' for t in subset),'resets':sum(t.get('errorType')=='ConnectionResetError' for t in subset),'statuses':dict(collections.Counter(str(t['status']) for t in subset))}
 assert not case.calls
 result={'testFixtureOnly':True,'listen':'127.0.0.1:ephemeral','serverCodeChanged':False,'testFileChanged':False,'retries':0,'python':sys.version.split()[0],'openssl':ssl.OPENSSL_VERSION,'fakeExecutorCalls':len(case.calls),'summary':summary,'trials':trials}
 (OUT/'tls-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'summary':summary,'fakeExecutorCalls':len(case.calls),'python':result['python'],'openssl':result['openssl']},indent=2))
finally:
 case.tearDown();Case.tearDownClass()
