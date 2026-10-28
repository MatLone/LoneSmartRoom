"""Opt-in, read-only Windows readers. No probing or native load on import.

No pipe connection, sensor startup, registry write, process signal or repair.
Paths and GET target are local constants, never renderer/remote inputs.
"""
import ctypes as ct
from contextlib import closing
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import secrets
import sqlite3
import ssl
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
INSTALL=(Path.home() / 'AppData/Local/Programs/Lone Smart Room')
STATE=ROOT/'.runtime/secure-agent'
PIN='3dec99c6583046483e63e3d03dcf96f64a26f11e10b5e669ceb71be89376e51f'
PIPE_PREFIX='\\\\.\\pipe\\LoneSmartRoom.Monitoring.Dev.v1.'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def norm(value): return os.path.normcase(os.path.abspath(value))


def launcher_arguments(args,python_images,launcher):
    """Allow only the two fixed Python invocation forms documented locally.

    The validated bootstrap uses -I -B before the script. These are interpreter
    flags, not agent arguments. No -c, -m, other flags or arbitrary script passes.
    """
    if not args or norm(args[0]) not in python_images:return False,False
    rest=args[1:]
    if rest[:2]==['-I','-B']:rest=rest[2:]
    valid=(len(rest) in (1,2) and norm(rest[0])==launcher
           and (len(rest)==1 or rest[1]=='--worker'))
    return valid,valid and len(rest)==2


def candidate_arguments(args,python_images,root):
    """Explicit development opt-in: fixed candidate supervisor/cooperative worker.

    Exact interpreter flags and suffixes only; never infer approval from basename.
    This does not itself probe or start a process.
    """
    if (not isinstance(args,list) or not args or not all(isinstance(v,str) for v in args)
            or norm(args[0]) not in python_images or args[1:3]!=['-I','-B']):
        return False,False
    rest=args[3:]
    if len(rest)==1 and norm(rest[0])==norm(root/'agent/development/reliable_bootstrap.py'):
        return True,False
    if len(rest)==2 and norm(rest[0])==norm(root/'agent/development/reliable_bootstrap.py') and rest[1]=='_worker':
        return True,True
    if len(rest)==2 and norm(rest[0])==norm(root/'agent/windows/graceful_launcher.py') and rest[1]=='_worker':
        return True,True
    return False,False


def validate_chain(rows,listeners,own):
    """Only retained native identities and exact argument allowlists qualify."""
    if len(listeners)!=1 or not rows or len(rows)>4:return False
    by_pid={r['pid']:r for r in rows}
    if len(by_pid)!=len(rows):return False
    for r in rows:
        if (r.get('approved') is not True or r['sid']!=own['sid'] or r['session']!=own['session']
                or r['elevated'] or not r['alive']):return False
    roots=[r for r in rows if r['parent'] not in by_pid]
    if len(roots)!=1 or roots[0]['worker']:return False
    chain=[];node=roots[0]
    while node['pid'] not in chain:
        chain.append(node['pid'])
        children=[r for r in rows if r['parent']==node['pid']]
        if len(children)>1:return False
        if not children:break
        node=children[0]
    listener=listeners[0]
    return (len(chain)==len(rows) and node['worker'] and listener['pid']==node['pid']
            and listener['port']==8776 and listener['private_binding'] is True)


def authenticated_get(connection, device, secret, *, certificate_pin=PIN):
    """One bounded fixed GET. Verify the peer before sending identity/HMAC."""
    try:
        connection.connect()
        if hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()!=certificate_pin:
            return {'ok':False,'error':'tls_identity_failed'}
        from secure_protocol import canonical
        stamp,nonce=str(int(time.time())),secrets.token_hex(16)
        signature=hmac.new(secret,canonical(stamp,nonce,device,'GET','/v2/status',b''),hashlib.sha256).hexdigest()
        headers=dict(zip(('X-Lone-Device','X-Lone-Timestamp','X-Lone-Nonce','X-Lone-Signature'),(device,stamp,nonce,signature)))
        tls=connection.sock.version()
        connection.request('GET','/v2/status',headers=headers)
        response=connection.getresponse()
        if response.status==401:return {'ok':False,'error':'authentication_failed'}
        raw=response.read(4097)
        if len(raw)>4096:return {'ok':False,'error':'response_limit'}
        body=json.loads(raw)
        good=(response.status==200 and body.get('ok') is True and body.get('agent')=='online')
        return {'ok':good,'http_status':response.status,'tls':tls,'hostname_verified':True,'pin_verified':True}
    except ssl.SSLError:return {'ok':False,'error':'tls_identity_failed'}
    except (OSError,TimeoutError):return {'ok':False,'error':'connection_failed'}
    except (ValueError,TypeError,AttributeError):return {'ok':False,'error':'invalid_status_response'}
    finally:connection.close()


class WindowsReaders:
    def __init__(self,*,candidate=False):
        if type(candidate) is not bool:raise ValueError('candidate_boolean_required')
        self.candidate=candidate
        self.handles=[];self.scanners=[];self.api=None;self.started=None;self.start_resources=None

    def begin(self,deadline):
        if time.monotonic()>=deadline:raise TimeoutError('deadline')
        from monitoring.winpipe import WindowsPipeApi,bind
        self.api=WindowsPipeApi()  # Current token must be non-elevated.
        self.started=time.monotonic()
        self.start_resources=self.api.resources(self.api.k.GetCurrentProcess())
        self.shell=ct.WinDLL('shell32.dll',use_last_error=True,winmode=0x800)
        self.argv_api=bind(self.shell,'CommandLineToArgvW',[w.LPCWSTR,ct.POINTER(ct.c_int)],ct.POINTER(w.LPWSTR))

    def argv(self,command):
        if not isinstance(command,str) or len(command)>32768:raise ValueError('invalid_command_line')
        count=ct.c_int();ptr=self.argv_api(command,ct.byref(count))
        if not ptr:raise ValueError('command_line_unavailable')
        try:
            if not 1<=count.value<=16:raise ValueError('argument_limit')
            return [ptr[i] for i in range(count.value)]
        finally:self.api.k.LocalFree(ct.cast(ptr,ct.c_void_p))

    def _inventory(self,deadline):
        remaining=min(8,deadline-time.monotonic())
        if remaining<=0:raise TimeoutError('inventory_deadline')
        program=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        child=subprocess.Popen([str(program),'-NoLogo','-NoProfile','-NonInteractive','-File',
            str(Path(__file__).with_name('windows-census.ps1'))],shell=False,
            cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        self.scanners.append(child)
        # On timeout do not kill any process. The CLI reports incomplete/remaining
        # read-only inventory, and no subsequent operational action is permitted.
        output,error=child.communicate(timeout=remaining)
        if child.returncode or len(output)>512*1024:raise ValueError('inventory_failed')
        value=json.loads(output.decode('utf-8-sig'))
        if value.get('v')!=1 or len(value['processes'])>256:raise ValueError('inventory_limit')
        return value

    def pipes(self):
        # Namespace enumeration only: never opens an instance or sends data.
        class FindData(ct.Structure):
            _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('access',w.FILETIME),
                ('written',w.FILETIME),('sizeHigh',w.DWORD),('sizeLow',w.DWORD),
                ('reserved0',w.DWORD),('reserved1',w.DWORD),('name',w.WCHAR*260),('alternate',w.WCHAR*14)]
        from monitoring.winpipe import bind
        first=bind(self.api.k,'FindFirstFileW',[w.LPCWSTR,ct.POINTER(FindData)],w.HANDLE)
        next_file=bind(self.api.k,'FindNextFileW',[w.HANDLE,ct.POINTER(FindData)],w.BOOL)
        close_find=bind(self.api.k,'FindClose',[w.HANDLE],w.BOOL)
        data=FindData();handle=first(PIPE_PREFIX+'*',ct.byref(data))
        if handle==ct.c_void_p(-1).value:
            if ct.get_last_error()==2:return {'available':True,'matching_count':0}
            return {'available':False,'matching_count':None}
        try:
            count=0
            while True:
                count+=1
                if count>64:return {'available':False,'matching_count':None,'limit':True}
                if not next_file(handle,ct.byref(data)):
                    if ct.get_last_error()!=18:return {'available':False,'matching_count':None}
                    return {'available':True,'matching_count':count}
        finally:close_find(handle)

    def census(self,*,deadline):
        raw=self._inventory(deadline);agents=[];apps=0;monitoring=0;complete=True
        python_images={norm(ROOT/'.venv/Scripts/pythonw.exe'),norm('C:/Python313/pythonw.exe')}
        launcher=norm(ROOT/'agent/windows/agent_launcher.py')
        for r in raw['processes']:
            command=r.get('CommandLine');image=r.get('ExecutablePath') or ''
            if not command:
                complete=False
                continue
            low=command.lower()
            agent=any(x in low for x in ('agent_launcher.py','secure_agent.py','graceful_launcher.py','reliable_bootstrap.py'))
            app=norm(image) in {norm(INSTALL/'Lone Smart Room.exe'),norm(ROOT/'apps/windows-ui/node_modules/electron/dist/electron.exe')}
            monitor=any(x in low for x in ('monitoring-pipe-client.py','monitoring-pipe-server.py','native/adlx/bridge.exe','native\\adlx\\bridge.exe'))
            if not (agent or app or monitor):continue
            handle=self.api.hold_process(int(r['ProcessId']));self.handles.append(handle)
            identity=self.api.identity(handle)
            created=datetime.fromtimestamp((identity['created']-116444736000000000)/10000000,timezone.utc)
            census_created=datetime.fromisoformat(r['created'].replace('Z','+00:00'))
            if (abs((created-census_created).total_seconds())>.001 or identity['image']!=norm(image)
                    or identity['sid']!=self.api.own['sid'] or identity['session']!=self.api.own['session']
                    or identity['elevated'] or not self.api.alive(handle)):
                raise ValueError('process_identity_unverified')
            if agent:
                args=self.argv(command)
                approved,worker=launcher_arguments(args,python_images,launcher)
                if not approved and self.candidate:
                    approved,worker=candidate_arguments(args,python_images,ROOT)
                approved=approved and identity['image'] in python_images
                agents.append({**identity,'parent':int(r['ParentProcessId']),
                    'worker':worker,'approved':approved,'alive':True})
            apps+=int(app);monitoring+=int(monitor)
        import ipaddress
        listeners=[]
        for r in raw['listeners']:
            addr=ipaddress.ip_address(r['LocalAddress'])
            listeners.append({'pid':int(r['OwningProcess']),'port':int(r['LocalPort']),
                'private_binding':addr.is_private and not addr.is_unspecified and not addr.is_loopback and not addr.is_multicast})
        value=raw.get('run');configured=isinstance(value,str) and bool(value)
        run_target=False
        if configured:
            try:
                args=self.argv(value)
                approved,worker=launcher_arguments(args,python_images,launcher)
                if not approved and self.candidate:
                    approved,worker=candidate_arguments(args,python_images,ROOT)
                run_target=approved and not worker
            except ValueError:pass
        return {'agent_verified':validate_chain(agents,listeners,self.api.own),
            'agent_identity_digest':digest(sorted(agents,key=lambda r:r['pid'])),'agent_processes':[
                {k:r[k] for k in ('pid','parent','created','worker','approved','alive')} for r in agents],
            'same_account_session_verified':bool(agents),'listener_count':len(listeners),'listeners':listeners,
            'application_count':apps,'monitoring_count':monitoring,'monitoring_census_complete':complete,
            'pipe_namespace':self.pipes(),'startup':{'configured':configured,'target_verified':run_target,
                'run_sha256':hashlib.sha256(value.encode()).hexdigest() if configured else None,
                'dispatch_proven':False},'elevated':self.api.own['elevated'],
            'observed_at':datetime.now(timezone.utc).isoformat(),'observed_monotonic':time.monotonic()}

    def database(self):
        with closing(sqlite3.connect((STATE/'devices.db').as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            return {'integrity_ok':db.execute('PRAGMA quick_check').fetchall()==[('ok',)],
                'grants':db.execute('SELECT count(*) FROM app_permissions').fetchone()[0],
                'identity_sha256':digest(db.execute('SELECT id,label,hex(secret),revoked FROM devices ORDER BY id').fetchall()),
                'permissions_sha256':digest(db.execute('SELECT * FROM app_permissions ORDER BY 1,2').fetchall())}

    def status(self,*,deadline):
        budget=min(2,deadline-time.monotonic())
        if budget<=0:raise TimeoutError('status_deadline')
        sys.path.insert(0,str(ROOT/'agent/windows'))
        from secure_store import DPAPI
        from secure_protocol import validate_lan
        protector=DPAPI()
        config=json.loads(protector.open((STATE/'config.dpapi').read_bytes()))
        validate_lan(config['host'],config['network'])
        if config['port']!=8776:raise ValueError('port_mismatch')
        with closing(sqlite3.connect((STATE/'devices.db').as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            rows=db.execute('SELECT id,secret FROM devices WHERE revoked=0').fetchall()
            if len(rows)!=1 or db.execute('SELECT count(*) FROM app_permissions').fetchone()[0]!=0:
                raise ValueError('identity_gate_failed')
        device,cipher=rows[0];secret=protector.open(cipher)
        if len(secret)!=32:raise ValueError('credential_invalid')
        context=ssl.create_default_context(cafile=str(STATE/'server.crt'))
        context.minimum_version=ssl.TLSVersion.TLSv1_2
        if not context.check_hostname or context.verify_mode!=ssl.CERT_REQUIRED:raise ValueError('tls_policy')
        result=authenticated_get(http.client.HTTPSConnection(config['host'],8776,context=context,timeout=budget),device,secret)
        return {**result,'observed_at':datetime.now(timezone.utc).isoformat(),'observed_monotonic':time.monotonic()}

    def startup_logs(self):
        sys.path.insert(0,str(ROOT/'agent/windows'))
        from launcher_win32 import Windows,checked_path
        path=ROOT/'.runtime/agent-startup-logs/startup.log'
        if not path.exists():return {'available':False,'reason':'absent','dispatch_proven':False}
        try:
            checked_path(path);Windows().verify_private(path)
            st=path.stat()
            if st.st_nlink!=1 or st.st_size>65536:raise ValueError('unsafe_log')
            with path.open('rb') as source:
                opened=os.fstat(source.fileno())
                if (opened.st_ino,opened.st_dev)!=(st.st_ino,st.st_dev):raise ValueError('log_changed')
                data=source.read(65537)
            if len(data)>65536:raise ValueError('log_limit')
            from .startup_evidence import EVENTS
            from .evidence import utc_string
            events=[]
            for line in data.decode('utf-8').splitlines()[-64:]:
                row=json.loads(line)
                if (set(row)-{'utc','pid','event','phase','code','dependency'} or
                        not {'utc','pid','event'}<=set(row) or row['event'] not in EVENTS):raise ValueError('log_schema')
                when=utc_string(row['utc'])
                if when>datetime.now(timezone.utc):raise ValueError('future_log')
                events.append({'utc':row['utc'],'event':row['event']})
            return {'available':True,'acl_verified':True,'records':len(events),'last':events[-1] if events else None,
                'dispatch_proven':False,'login_correlation':'not_verified'}
        except (OSError,ValueError,TypeError,KeyError,UnicodeError):
            return {'available':False,'reason':'log_not_safely_verifiable','dispatch_proven':False}

    def close(self):
        for handle in self.handles:
            self.api.close(handle)
        self.handles.clear()

    def resource_summary(self,elapsed):
        if self.api is None or self.start_resources is None:return {'available':False}
        last=self.api.resources(self.api.k.GetCurrentProcess())
        seconds=last['cpu_seconds']-self.start_resources['cpu_seconds']
        return {'available':True,'reader_cpu_seconds':round(seconds,6),
            'reader_cpu_percent_total_machine':round(100*seconds/max(elapsed,.001)/os.cpu_count(),6),
            'reader_final_rss_mib':round(last['working_set_bytes']/1048576,3),
            'scope':'Python reader only; transient PowerShell/CIM overhead not measured',
            'inventory_processes_remaining':sum(p.poll() is None for p in self.scanners)}
