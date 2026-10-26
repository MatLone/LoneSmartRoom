"""Read-only reader tests. Native/network/process methods are replaced or denied."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent/windows'))
from diagnostics.contracts import Component as C,DetailCode as D,DiagnosticError,Outcome as O,Probe
from diagnostics.engine import DiagnosticEngine
from diagnostics.passive import OnceProvider,report_for,run_session
from diagnostics.presentation import present
from diagnostics.windows_readers import WindowsReaders,authenticated_get,validate_chain

NOW=datetime(2026,10,26,12,tzinfo=timezone.utc)


def census():
    return dict(agent_verified=True,agent_identity_digest='a'*64,listener_count=1,
        monitoring_census_complete=True,application_count=0,monitoring_count=0,
        pipe_namespace={'available':True,'matching_count':0},startup={'configured':True})


def healthy():return dict(ok=True,http_status=200,hostname_verified=True,pin_verified=True)


class FakeReader:
    def __init__(self):
        self.calls=[];self.closed=False;self.time=0.;self.grants=0;self.bad_identity=False
        self.https=healthy();self.change=False;self.fail=None
    def clock(self):return self.time
    def step(self,name):
        self.calls.append(name);self.time+=1
        if self.fail==name:raise RuntimeError('secret-not-to-be-logged')
    def begin(self,deadline):self.step('begin')
    def census(self,deadline):
        self.step('census');c=census()
        if self.bad_identity:c['agent_verified']=False
        if self.change and self.calls.count('census')>1:c['agent_identity_digest']='b'*64
        return c
    def database(self):
        self.step('database');return {'integrity_ok':True,'grants':self.grants,'identity_sha256':'fixed'}
    def status(self,deadline):self.step('status');return self.https
    def startup_logs(self):self.step('logs');return {'available':False}
    def close(self):self.closed=True;self.step('close')
    def resource_summary(self,elapsed):return {'available':False}


class SessionTests(unittest.TestCase):
    def run_fake(self,f):return run_session(f,clock=f.clock,utc_now=lambda:NOW)
    def test_one_session_two_fixed_reads_and_close(self):
        f=FakeReader();r=self.run_fake(f)
        self.assertTrue(r['completed']);self.assertTrue(r['within_limit'])
        self.assertEqual(f.calls.count('status'),2);self.assertTrue(f.closed)
        self.assertFalse(r['report']['simulation']);self.assertFalse(r['repairs'])
    def test_no_auth_when_identity_unknown(self):
        f=FakeReader();f.bad_identity=True;r=self.run_fake(f)
        self.assertNotIn('status',f.calls);self.assertFalse(r['completed']);self.assertTrue(f.closed)
    def test_no_auth_with_grants(self):
        f=FakeReader();f.grants=1;r=self.run_fake(f)
        self.assertNotIn('status',f.calls);self.assertEqual(r['stop_code'],'database_gate_failed')
    def test_no_retry_auth_failure(self):
        f=FakeReader();f.https={'ok':False,'error':'authentication_failed'};r=self.run_fake(f)
        self.assertEqual(f.calls.count('status'),1);self.assertFalse(r['completed'])
    def test_identity_change_stops_before_second_get(self):
        f=FakeReader();f.change=True;r=self.run_fake(f)
        self.assertEqual(f.calls.count('status'),1);self.assertEqual(r['stop_code'],'agent_identity_changed')
    def test_reader_exception_is_sanitized_and_closed(self):
        f=FakeReader();f.fail='logs';r=self.run_fake(f)
        self.assertNotIn('secret',json.dumps(r));self.assertTrue(f.closed);self.assertFalse(r['completed'])
    def test_budget_stops_new_work(self):
        f=FakeReader()
        def logs():f.time=36;return {}
        f.startup_logs=logs;r=self.run_fake(f)
        self.assertEqual(f.calls.count('status'),1);self.assertEqual(r['stop_code'],'final_checks_budget_exhausted')
    def test_deadline_miss_never_success(self):
        f=FakeReader()
        def close():f.time=61;f.closed=True
        f.close=close;r=self.run_fake(f)
        self.assertFalse(r['completed']);self.assertFalse(r['within_limit'])


class ProjectionTests(unittest.TestCase):
    def test_normally_inactive_not_failure(self):
        r,v=report_for(census(),healthy(),NOW,10)
        for card in v['cards'][2:7]:
            self.assertEqual(card['label'],'Indisponível')
            self.assertEqual(card['detail_code'],D.NORMAL_INACTIVE)
        self.assertEqual(v['cards'][-1]['label'],'Não verificado')
    def test_running_app_does_not_prove_sensor_health(self):
        c=census();c['application_count']=4;c['monitoring_count']=3
        r,v=report_for(c,healthy(),NOW,10)
        self.assertTrue(all(x['label']=='Não verificado' for x in v['cards'][2:7]))
    def test_unreadable_inventory_is_not_normal_inactivity(self):
        for field in ('monitoring_census_complete','pipe_namespace'):
            c=census();c[field]=None;r,v=report_for(c,healthy(),NOW,10)
            self.assertEqual(v['cards'][2]['label'],'Não verificado')
    def test_pipe_presence_is_not_connected_or_authenticated(self):
        c=census();c['pipe_namespace']={'available':True,'matching_count':1}
        r,v=report_for(c,healthy(),NOW,10);self.assertFalse(r['checks'][2]['valid'])
    def test_old_https_receipt_is_stale_not_renewed(self):
        h=healthy();h.update(observed_at=(NOW-timedelta(seconds=11)).isoformat(),observed_monotonic=0)
        r,v=report_for(census(),h,NOW,11)
        self.assertEqual(v['cards'][0]['label'],'Desatualizado');self.assertEqual(r['checks'][0]['age_seconds'],11)
    def test_future_receipt_is_not_verified(self):
        h=healthy();h.update(observed_at=(NOW+timedelta(seconds=1)).isoformat(),observed_monotonic=11)
        r,v=report_for(census(),h,NOW,10);self.assertEqual(v['cards'][0]['label'],'Não verificado')
    def test_tls_failure_is_proven_failure(self):
        r,v=report_for(census(),{'error':'tls_identity_failed'},NOW,10)
        self.assertEqual(v['cards'][0]['label'],'Falha')
    def test_transport_unavailable_not_pc_off(self):
        r,v=report_for(census(),{'error':'connection_failed'},NOW,10)
        self.assertEqual(v['cards'][0]['label'],'Indisponível');self.assertEqual(r['power_state'],'unknown')
    def test_all_five_categories_are_distinct(self):
        categories=set()
        for c,h in ((census(),healthy()),(census(),{'error':'tls_identity_failed'})):
            r,v=report_for(c,h,NOW,10);categories.update(x['label'] for x in v['cards'])
        h=healthy();h.update(observed_at=(NOW-timedelta(seconds=12)).isoformat(),observed_monotonic=0)
        r,v=report_for(census(),h,NOW,12);categories.add(v['cards'][0]['label'])
        self.assertEqual(categories,{'Saudável','Indisponível','Desatualizado','Falha','Não verificado'})
    def test_simulated_engine_cannot_silently_consume_observed(self):
        p=Probe(C.HTTPS,NOW,0,{},O.UNKNOWN,evidence_kind='observed')
        with self.assertRaises(DiagnosticError):DiagnosticEngine([OnceProvider(p)])
        r,v=report_for(census(),healthy(),NOW,10)
        with self.assertRaises(DiagnosticError):present(r)
    def test_no_metrics_are_fabricated(self):
        r,v=report_for(census(),healthy(),NOW,10)
        self.assertNotIn('value',json.dumps(r));self.assertTrue(all(x['last_communication'] is None for x in r['checks'][1:]))


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.own={'sid':'account','session':1}
        self.rows=[dict(pid=10,parent=1,sid='account',session=1,elevated=False,alive=True,approved=True,worker=False),
            dict(pid=11,parent=10,sid='account',session=1,elevated=False,alive=True,approved=True,worker=True)]
        self.listeners=[dict(pid=11,port=8776,private_binding=True)]
    def test_chain(self):self.assertTrue(validate_chain(self.rows,self.listeners,self.own))
    def test_reject_wrong_or_missing_identity(self):
        for key,value in (('sid','other'),('session',2),('elevated',True),('alive',False),('approved',False),('parent',999)):
            with self.subTest(key=key):
                rows=deepcopy(self.rows);rows[1][key]=value
                self.assertFalse(validate_chain(rows,self.listeners,self.own))
    def test_duplicate_or_wrong_listener(self):
        for listeners in ([],self.listeners*2,[dict(pid=99,port=8776,private_binding=True)],
                          [dict(pid=11,port=8776,private_binding=False)]):
            self.assertFalse(validate_chain(self.rows,listeners,self.own))
    def test_duplicate_worker_or_cycle(self):
        rows=deepcopy(self.rows);rows.append({**rows[1],'pid':12})
        self.assertFalse(validate_chain(rows,self.listeners,self.own))
        rows=deepcopy(self.rows);rows[0]['parent']=11
        self.assertFalse(validate_chain(rows,self.listeners,self.own))


class HTTPTests(unittest.TestCase):
    def connection(self,**kwargs):
        c=Mock();c.sock.getpeercert.return_value=b'official-test-cert';c.sock.version.return_value='TLSv1.3'
        response=c.getresponse.return_value;response.status=kwargs.get('status',200)
        response.read.return_value=kwargs.get('body',b'{"ok":true,"agent":"online"}')
        return c
    def call(self,c,pin=None):
        return authenticated_get(c,'fake-device',b'x'*32,certificate_pin=pin or hashlib.sha256(b'official-test-cert').hexdigest())
    def test_fixed_get_no_body_only_status(self):
        c=self.connection();self.assertTrue(self.call(c)['ok'])
        args=c.request.call_args
        self.assertEqual(args.args,('GET','/v2/status'));self.assertEqual(set(args.kwargs),{'headers'});c.close.assert_called_once()
    def test_no_identity_sent_before_pin(self):
        c=self.connection();r=self.call(c,'0'*64)
        self.assertEqual(r['error'],'tls_identity_failed');c.request.assert_not_called();c.close.assert_called_once()
    def test_tls_certificate_failure_no_request(self):
        import ssl
        c=self.connection();c.connect.side_effect=ssl.SSLCertVerificationError('sensitive text')
        self.assertEqual(self.call(c)['error'],'tls_identity_failed');c.request.assert_not_called()
    def test_auth_failure_no_retry(self):
        c=self.connection(status=401);self.assertEqual(self.call(c)['error'],'authentication_failed');self.assertEqual(c.request.call_count,1)
    def test_size_limit_invalid_json_and_wrong_body(self):
        for body in (b'x'*4097,b'bad',b'{"ok":true,"agent":"offline"}',b'[]'):
            c=self.connection(body=body);r=self.call(c);self.assertFalse(r['ok']);self.assertNotIn('fake-device',json.dumps(r))
            c.getresponse.return_value.read.assert_called_once_with(4097)
    def test_connection_failure_is_sanitized(self):
        c=self.connection();c.connect.side_effect=ConnectionResetError('credential=private')
        r=self.call(c);self.assertEqual(r['error'],'connection_failed');self.assertNotIn('private',json.dumps(r))


class NativeBoundaryTests(unittest.TestCase):
    def test_constructor_does_not_activate_windows(self):
        r=WindowsReaders();self.assertIsNone(r.api);self.assertEqual(r.handles,[])
    def test_native_os_calls_are_explicitly_denied_by_test_harness(self):
        import ctypes
        with patch('ctypes.WinDLL',side_effect=RuntimeError('native_call_denied')):
            with self.assertRaises(RuntimeError):ctypes.WinDLL('kernel32.dll')
    def test_reader_sources_have_no_control_operations(self):
        text=(ROOT/'diagnostics/windows_readers.py').read_text()
        ps=(ROOT/'diagnostics/windows-census.ps1').read_text()
        for forbidden in ('TerminateProcess','SetValue','Set-NetFirewall','CreateNamedPipeW','LoadLibrary','os.startfile',"'POST'",'/v2/apps'):
            self.assertNotIn(forbidden,text+ps)
        self.assertIn('OpenSubKey',ps);self.assertIn(',$false)',ps)
    def test_elevation_is_rejected_before_census(self):
        with patch('monitoring.winpipe.WindowsPipeApi',side_effect=PermissionError('elevated')):
            with self.assertRaises(PermissionError):WindowsReaders().begin(100000000)


class PlatformMockTests(unittest.TestCase):
    def test_complete_census_uses_held_identity_and_exact_launcher(self):
        from diagnostics.windows_readers import ROOT,norm
        image=str(ROOT/'.venv/Scripts/pythonw.exe')
        launch=str(ROOT/'agent/windows/agent_launcher.py')
        r=WindowsReaders();r.api=Mock();r.api.own={'sid':'account','session':1,'elevated':False}
        creation=int(NOW.timestamp()*10000000)+116444736000000000
        r.api.identity.side_effect=[dict(pid=pid,sid='account',session=1,elevated=False,
            created=creation,image=norm(image)) for pid in (10,11)]
        r.api.alive.return_value=True
        r.argv=Mock(side_effect=[[image,launch],[image,launch,'--worker'],[image,launch]])
        r._inventory=Mock(return_value={'processes':[
            dict(ProcessId=10,ParentProcessId=1,ExecutablePath=image,CommandLine='agent_launcher.py',created=NOW.isoformat()),
            dict(ProcessId=11,ParentProcessId=10,ExecutablePath=image,CommandLine='agent_launcher.py --worker',created=NOW.isoformat())],
            'listeners':[dict(OwningProcess=11,LocalPort=8776,LocalAddress='192.168.1.2')],'run':'configured'})
        r.pipes=Mock(return_value={'available':True,'matching_count':0})
        result=r.census(deadline=100000000)
        self.assertTrue(result['agent_verified']);self.assertEqual(result['listener_count'],1)
        self.assertEqual(result['application_count'],0);self.assertTrue(result['startup']['target_verified'])
        self.assertNotIn('CommandLine',json.dumps(result));self.assertNotIn(launch,json.dumps(result))
        r.close();self.assertEqual(r.api.close.call_count,2)
    def test_inventory_only_fixed_system_powershell_read_script(self):
        child=Mock(returncode=0);child.communicate.return_value=(b'{"v":1,"processes":[]}',b'')
        with patch('diagnostics.windows_readers.subprocess.Popen',return_value=child) as popen:
            value=WindowsReaders()._inventory(time.monotonic()+2)
        args=popen.call_args
        self.assertEqual(args.args[0][-2],'-File')
        self.assertTrue(args.args[0][-1].endswith('diagnostics\\windows-census.ps1'))
        self.assertFalse(args.kwargs['shell']);self.assertEqual(value['v'],1)
        child.kill.assert_not_called();child.terminate.assert_not_called()
    def test_inventory_timeout_is_not_force_terminated(self):
        import subprocess
        child=Mock();child.communicate.side_effect=subprocess.TimeoutExpired('fixed-reader',2)
        with patch('diagnostics.windows_readers.subprocess.Popen',return_value=child):
            with self.assertRaises(subprocess.TimeoutExpired):WindowsReaders()._inventory(time.monotonic()+2)
        child.kill.assert_not_called();child.terminate.assert_not_called()
    def test_inventory_excessive_output_and_nonzero_exit(self):
        for code,body in ((0,b'x'*(512*1024+1)),(1,b'private exception')):
            child=Mock(returncode=code);child.communicate.return_value=(body,b'')
            with patch('diagnostics.windows_readers.subprocess.Popen',return_value=child):
                with self.assertRaises(ValueError):WindowsReaders()._inventory(time.monotonic()+2)
    def test_pipe_namespace_absent_does_not_connect(self):
        import ctypes
        api=Mock();first=Mock(return_value=ctypes.c_void_p(-1).value)
        with patch('monitoring.winpipe.bind',side_effect=[first,Mock(),Mock()]),patch('ctypes.get_last_error',return_value=2):
            r=WindowsReaders();r.api=api;result=r.pipes()
        self.assertEqual(result,{'available':True,'matching_count':0});api.connect.assert_not_called()
    def test_pipe_namespace_error_is_not_zero(self):
        import ctypes
        with patch('monitoring.winpipe.bind',side_effect=[Mock(return_value=ctypes.c_void_p(-1).value),Mock(),Mock()]),patch('ctypes.get_last_error',return_value=5):
            r=WindowsReaders();r.api=Mock();result=r.pipes()
        self.assertEqual(result,{'available':False,'matching_count':None})
    def test_pipe_namespace_count_is_bounded_and_handle_closed(self):
        first=Mock(return_value=1);following=Mock(return_value=True);close=Mock()
        with patch('monitoring.winpipe.bind',side_effect=[first,following,close]):
            r=WindowsReaders();r.api=Mock();result=r.pipes()
        self.assertTrue(result['limit']);self.assertEqual(following.call_count,64);close.assert_called_once_with(1)
    def test_census_native_identity_creation_mismatch_rejected(self):
        from diagnostics.windows_readers import ROOT,norm
        r=WindowsReaders();r.api=Mock();r.api.own={'sid':'account','session':1}
        image=str(ROOT/'.venv/Scripts/pythonw.exe')
        r._inventory=Mock(return_value={'processes':[{'ProcessId':10,'ParentProcessId':1,
            'ExecutablePath':image,'CommandLine':'agent_launcher.py','created':NOW.isoformat()}],
            'listeners':[],'run':None})
        r.api.identity.return_value={'created':116444736000000000,'image':norm(image),
            'sid':'account','session':1,'elevated':False}
        with self.assertRaisesRegex(ValueError,'identity'):r.census(deadline=100000000)
        self.assertEqual(len(r.handles),1);r.close();r.api.close.assert_called_once()
    def test_census_unreadable_process_is_inconclusive(self):
        r=WindowsReaders();r.api=Mock();r.api.own={'sid':'account','session':1,'elevated':False}
        r._inventory=Mock(return_value={'processes':[{'CommandLine':None}], 'listeners':[],'run':None})
        r.pipes=Mock(return_value={'available':True,'matching_count':0})
        result=r.census(deadline=100000000)
        self.assertFalse(result['monitoring_census_complete']);self.assertFalse(result['agent_verified'])
    def test_startup_absent_is_not_failed_bootstrap(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as temp,patch('diagnostics.windows_readers.ROOT',Path(temp)):
            r=WindowsReaders().startup_logs()
        self.assertFalse(r['available']);self.assertFalse(r['dispatch_proven'])
    def log_fixture(self,content):
        temp=tempfile.TemporaryDirectory(dir=ROOT/'.cache');root=Path(temp.name)
        path=root/'.runtime/agent-startup-logs/startup.log';path.parent.mkdir(parents=True);path.write_bytes(content)
        return temp,root
    def test_startup_acl_failure_never_read_or_repair(self):
        temp,root=self.log_fixture(b'private')
        try:
            with patch('diagnostics.windows_readers.ROOT',root),patch('launcher_win32.Windows') as win:
                win.return_value.verify_private.side_effect=PermissionError('private path')
                result=WindowsReaders().startup_logs()
                win.return_value.private_file.assert_not_called();win.return_value.private_directory.assert_not_called()
            self.assertFalse(result['available']);self.assertNotIn('private path',json.dumps(result))
        finally:temp.cleanup()
    def test_startup_whitelisted_receipt_not_dispatch_proof(self):
        payload={'utc':NOW.isoformat(),'pid':123,'event':'bootstrap_ready'}
        temp,root=self.log_fixture(json.dumps(payload).encode())
        try:
            with patch('diagnostics.windows_readers.ROOT',root),patch('launcher_win32.Windows'):
                result=WindowsReaders().startup_logs()
            self.assertTrue(result['available']);self.assertFalse(result['dispatch_proven'])
            self.assertNotIn('pid',json.dumps(result));self.assertEqual(result['last']['event'],'bootstrap_ready')
        finally:temp.cleanup()
    def test_startup_free_text_unknown_fields_and_excessive_bytes_rejected(self):
        for payload in (b'x'*65537,b'{"utc":"2026-10-26T00:00:00Z","pid":1,"event":"attempt","secret":"do not print"}',b'bad'):
            temp,root=self.log_fixture(payload)
            try:
                with patch('diagnostics.windows_readers.ROOT',root),patch('launcher_win32.Windows'):
                    result=WindowsReaders().startup_logs()
                self.assertFalse(result['available']);self.assertNotIn('do not print',json.dumps(result))
            finally:temp.cleanup()
    def test_database_read_only_integrity_and_grants(self):
        import sqlite3
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as temp:
            path=Path(temp)/'devices.db'
            with sqlite3.connect(path) as db:
                db.executescript('CREATE TABLE devices(id TEXT,label TEXT,secret BLOB,revoked INT); CREATE TABLE app_permissions(device TEXT,app TEXT);')
                db.execute('INSERT INTO devices VALUES(?,?,?,?)',('fixture','fake-label',b'fake-secret',0));db.commit()
            db.close()
            before=path.read_bytes()
            with patch('diagnostics.windows_readers.STATE',Path(temp)):
                result=WindowsReaders().database()
            self.assertTrue(result['integrity_ok']);self.assertEqual(result['grants'],0)
            self.assertEqual(path.read_bytes(),before);self.assertNotIn('fake-secret',json.dumps(result))
    def test_status_deadline_does_not_open_credentials(self):
        with self.assertRaises(TimeoutError):WindowsReaders().status(deadline=0)
    def test_status_uses_existing_identity_read_only_context_and_no_grant(self):
        import sqlite3,ssl
        with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as temp:
            state=Path(temp);(state/'config.dpapi').write_bytes(b'cipher-config')
            with sqlite3.connect(state/'devices.db') as db:
                db.executescript('CREATE TABLE devices(id TEXT,secret BLOB,revoked INT); CREATE TABLE app_permissions(device TEXT,app TEXT);')
                db.execute('INSERT INTO devices VALUES(?,?,?)',('fixture',b'cipher-device',0));db.commit()
            db.close()
            ctx=Mock(check_hostname=True,verify_mode=ssl.CERT_REQUIRED)
            with patch('diagnostics.windows_readers.STATE',state),patch('secure_store.DPAPI') as dpapi,\
                    patch('diagnostics.windows_readers.ssl.create_default_context',return_value=ctx),\
                    patch('diagnostics.windows_readers.http.client.HTTPSConnection') as connection,\
                    patch('diagnostics.windows_readers.authenticated_get',return_value=healthy()) as get:
                dpapi.return_value.open.side_effect=[b'{"host":"192.168.1.2","network":"192.168.1.0/24","port":8776}',b'x'*32]
                result=WindowsReaders().status(deadline=time.monotonic()+6)
                self.assertTrue(result['ok']);self.assertEqual(connection.call_args.args,('192.168.1.2',8776))
                self.assertEqual(get.call_args.args[1:],('fixture',b'x'*32))
                self.assertEqual(ctx.minimum_version,ssl.TLSVersion.TLSv1_2)
    def test_resources_are_reader_only_not_claimed_machine_total(self):
        r=WindowsReaders();r.api=Mock();r.start_resources={'cpu_seconds':1}
        r.api.resources.return_value={'cpu_seconds':1.1,'working_set_bytes':1048576}
        result=r.resource_summary(5)
        self.assertEqual(result['reader_final_rss_mib'],1)
        self.assertIn('not measured',result['scope'])


if __name__=='__main__':unittest.main()
