"""Bounded private stdio to an owned read-only worker; no network or DLL loading here.

Only launch_native() can construct the real command, from a fixed build location.
The test transport is injected locally; it is not exposed to renderer or IPC clients.
"""
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import queue
import subprocess
import threading
import time

from .adlx_provider import BY_ID, Capability, Device, Frame, Reading, WarmingUp
from .contracts import Availability as A, ContractError, DataKind
from .adlx_diagnostics import DiagnosticBuffer, PROFILE, CLOCKS, FRAME_FIELDS

ROOT=Path(__file__).resolve().parents[1]
MAX_LINE=16384
DYNAMIC=set(BY_ID)-{'gpu.adlx.vram_total_mb'}
ERRORS=frozenset('elevation_refused token_query_failed system_path_failed runtime_open_failed runtime_path_mismatch invalid_pe runtime_not_x64 hash_failed runtime_hash_mismatch runtime_signature_rejected runtime_load_failed loaded_path_mismatch runtime_exports_missing adlx_initialize_failed gpu_enumeration_failed gpu_count_invalid gpu_selection_failed performance_service_failed capability_discovery_failed tracking_start_failed history_limit metrics_query_failed timestamp_failed resource_query_failed memory_budget_exceeded command_limit invalid_command rate_limited request_limit bridge_internal_error invalid_value text_limit message_limit'.split())
ERRORS=ERRORS|{'private_transport_required'}


class BridgeError(RuntimeError):
    def __init__(self,code,*,rule=None,stage=None):
        self.code=code;self.rule=rule;self.stage=stage
        super().__init__(code)


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise BridgeError('invalid_message',rule='wire_duplicate_key',stage='wire')
        result[key]=value
    return result


def decode(line,diagnostics=None):
    def fail(rule,value=None):
        if diagnostics:diagnostics.emit('wire',rule,value)
        raise BridgeError('invalid_message',rule=rule,stage='wire')
    if not isinstance(line,bytes) or not line.endswith(b'\n') or len(line)>MAX_LINE:
        if diagnostics:diagnostics.emit('wire','wire_line_limit')
        raise BridgeError('message_limit')
    def floating(text):
        value=float(text)
        if not math.isfinite(value):raise BridgeError('invalid_message',rule='wire_nonfinite',stage='wire')
        return value
    try:
        obj=json.loads(line,object_pairs_hook=unique_object,parse_float=floating,
            parse_constant=lambda _:(_ for _ in ()).throw(BridgeError('invalid_message',rule='wire_nonfinite',stage='wire')))
    except BridgeError as exc:fail(exc.rule)
    except Exception:fail('wire_json')
    if type(obj) is not dict:fail('wire_object')
    if type(obj.get('v')) is not int or obj.get('v')!=1:fail('wire_version',obj)
    if obj.get('event') not in ('phase','ready','frame','warming_up','error','stopped'):fail('wire_event',obj)
    return obj


class LineTransport:
    """One owned process, one bounded queue, one reader; never terminates/kills it."""
    def __init__(self,spawn):
        self._spawn=spawn;self.process=None;self._queue=queue.Queue(maxsize=8)
        self._reader=None;self._fault=None;self._closed=False;self._sent_stop=False;self._started=False
        self._fault_rule=None;self.diagnostic=DiagnosticBuffer()

    def start(self):
        if self._started:raise BridgeError('duplicate_start')
        self._started=True
        try:self.process=self._spawn()
        except Exception:raise BridgeError('process_creation_failed') from None
        self._reader=threading.Thread(target=self._read,name='lone-adlx-output',daemon=True);self._reader.start()

    def _read(self):
        try:
            while True:
                line=self.process.stdout.readline(MAX_LINE+1)
                if not line:break
                try:message=decode(line,self.diagnostic)
                except BridgeError as exc:self._fault=exc.code;self._fault_rule=exc.rule;continue
                try:self._queue.put_nowait((message,time.monotonic()))
                except queue.Full:self._fault='message_queue_limit'
        except Exception:self._fault='read_failed'
        finally:
            if self._fault is None:self._fault='worker_eof'

    def receive(self,timeout):
        if self._fault not in (None,'worker_eof'):raise BridgeError(self._fault,rule=self._fault_rule,stage='wire')
        try:return self._queue.get(timeout=timeout)
        except queue.Empty:raise BridgeError('worker_eof' if self._fault=='worker_eof' else 'read_timeout') from None

    def send(self,command):
        if command not in ('latest','stop'):raise BridgeError('invalid_command')
        if not self.process or self._closed:raise BridgeError('transport_closed')
        if command=='stop':
            if self._sent_stop:return
            self._sent_stop=True
        try:self.process.stdin.write((command+'\n').encode('ascii'));self.process.stdin.flush()
        except (OSError,ValueError):raise BridgeError('write_failed') from None

    def close(self,timeout=5):
        if self._closed:return self.process is None or self.process.poll() is not None
        if not self.process:self._closed=True;return True
        if self.process.poll() is None:
            try:self.send('stop')
            except BridgeError:pass
        try:self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:return False
        self._closed=True
        self.process.stdin.close()
        if self._reader:self._reader.join(timeout=1)
        if self._reader and self._reader.is_alive():return False
        self.process.stdout.close();return True


def launch_native(*,diagnostics=False):
    """Fixed x64 build path, no user paths/arguments or shell; source/hash checked."""
    if type(diagnostics) is not bool:raise ContractError('boolean_required')
    build=ROOT/'.cache/adlx-build';exe=build/'bridge.exe'
    info=json.loads((build/'bridge-build.json').read_text())
    if (info.get('mock') is not False or info.get('verifyOnly') is not False or info.get('sdkCommit')!='66557d410ce4c463f5f7106597d94f53dd84bc82'
            or exe.is_symlink() or not exe.is_file()
            or exe.resolve()!=exe.absolute()
            or hashlib.sha256(exe.read_bytes()).hexdigest()!=info.get('exeSha256')
            or hashlib.sha256((ROOT/'native/adlx/bridge.cpp').read_bytes()).hexdigest()!=info.get('sourceSha256')):
        raise BridgeError('worker_integrity_failed')
    command=[str(exe)]+(['--diagnostics'] if diagnostics else [])
    return subprocess.Popen(command,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                            shell=False,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW,bufsize=0)


class NativeAdapter:
    def __init__(self,transport,*,data_kind=DataKind.REAL,timeout=2,diagnostics=False):
        if data_kind not in (DataKind.REAL,DataKind.SIMULATED) or type(timeout) not in (float,int) or not 0<timeout<=10:
            raise ContractError('invalid_bridge_configuration')
        self.data_kind=data_kind;self.transport=transport;self.timeout=timeout;self.ready=None
        self.phases=deque(maxlen=8);self.clock_sources=set();self._opened=False;self._attempted=False;self._pending=False;self._closed=False
        self._events=deque(maxlen=32);self._last_received=None;self.clean=None
        self.last_frame=None
        self._last_payload=None
        self._diagnostic=DiagnosticBuffer(diagnostics);self.transport.diagnostic=self._diagnostic

    def _next(self,timeout=None):
        value,received=self.transport.receive(self.timeout if timeout is None else timeout)
        self._last_received=received
        if value.get('event')=='error':
            code=value.get('code');raise BridgeError(code if code in ERRORS else 'native_error')
        return value

    def open(self):
        if self._opened:return
        if self._attempted or self._closed:raise BridgeError('duplicate_start')
        self._attempted=True;self.transport.start();deadline=time.monotonic()+10
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise BridgeError('bootstrap_timeout')
            value=self._next(remaining)
            if value['event']=='phase':
                if value.get('code') not in ('runtime_verified','adlx_loaded','adlx_initialized'):raise BridgeError('invalid_message')
                self.phases.append(value['code']);continue
            if value['event']!='ready':raise BridgeError('invalid_ready')
            self._validate_ready(value);self.ready=value;self._opened=True;return

    def _validate_ready(self,value):
        required={'v','event','simulated','pid','device','sdk_version','sdk_interval_ms','total_vram_mb','capabilities'}
        if self._diagnostic.enabled:
            required=required|{'diagnostic_profile'}
            if value.get('diagnostic_profile')!=PROFILE:raise BridgeError('invalid_ready')
        if (set(value)!=required or type(value['simulated']) is not bool
                or value['simulated']!=(self.data_kind==DataKind.SIMULATED)
                or type(value['pid']) is not int or value['pid']!=self.transport.process.pid):raise BridgeError('invalid_identity')
        d=value['device'];caps=value['capabilities']
        if (type(d) is not dict or set(d)!={'key','name','vendor_id','discrete'} or d['key']!='amd-rx6750xt'
                or type(d['name']) is not str or not 1<=len(d['name'])<=128 or type(d['vendor_id']) is not int or d['vendor_id']!=4098 or d['discrete'] is not True
                or type(value['sdk_version']) is not str or len(value['sdk_version'])>128
                or type(value['sdk_interval_ms']) is not int or not 0<=value['sdk_interval_ms']<=60000
                or type(caps) is not dict or set(caps)!=DYNAMIC):raise BridgeError('invalid_ready')
        for cap in caps.values():
            if type(cap) is not dict or set(cap)!={'ok','supported'} or any(type(x) is not bool for x in cap.values()) or cap['supported'] and not cap['ok']:
                raise BridgeError('invalid_capabilities')
        self._reading(value['total_vram_mb'])

    @staticmethod
    def _reading(value):
        if type(value) is not dict or set(value)!={'state','value'}:raise BridgeError('invalid_reading',rule='reading_shape',stage='readings')
        try:state=A(value['state'])
        except Exception:raise BridgeError('invalid_reading',rule='reading_state',stage='readings') from None
        if state==A.STALE:raise BridgeError('invalid_reading',rule='reading_state',stage='readings')
        if state!=A.AVAILABLE and value['value'] is not None:raise BridgeError('invalid_reading',rule='reading_null',stage='readings')
        if state==A.AVAILABLE:
            if type(value['value']) not in (int,float):raise BridgeError('invalid_reading',rule='reading_type',stage='readings')
            try:finite=math.isfinite(value['value'])
            except OverflowError:finite=False
            if not finite:raise BridgeError('invalid_reading',rule='reading_nonfinite',stage='readings')
        return Reading(state,value['value'])

    def devices(self):return (Device(**self.ready['device']),)
    def capabilities(self,key):
        self._key(key);return {name:Capability(**cap) for name,cap in self.ready['capabilities'].items()}
    def total_vram(self,key):self._key(key);return self._reading(self.ready['total_vram_mb'])
    def _key(self,key):
        if not self._opened or key!=self.ready['device']['key']:raise BridgeError('invalid_device_key')

    def _reject(self,stage,rule,value,field=None):
        self._events.append('invalid_frame');self._diagnostic.emit(stage,rule,value,field=field)
        raise BridgeError('invalid_frame',rule=rule,stage=stage)

    def _validate_frame(self,value):
        def reject(rule,field=None,stage='frame'):self._reject(stage,rule,value,field)
        if type(value) is not dict:reject('frame_object')
        required=set(FRAME_FIELDS)|({'diagnostic'} if self._diagnostic.enabled else set())
        if required-set(value):reject('frame_required_missing',next(name for name in (*FRAME_FIELDS,'diagnostic') if name not in value))
        if set(value)-required:reject('frame_extra_fields')
        if type(value['v']) is not int or value['v']!=1:reject('frame_version','v')
        if value['event']!='frame':reject('frame_event','event')
        if value['timestamp_ms'] is None:reject('timestamp_null','timestamp_ms','time')
        if type(value['timestamp_ms']) is not int:reject('timestamp_type','timestamp_ms','time')
        if not 0<=value['timestamp_ms']<=2**63-1:reject('timestamp_range','timestamp_ms','time')
        age=value['age_seconds']
        if age is None:reject('age_null','age_seconds','time')
        if type(age) not in (int,float):reject('age_type','age_seconds','time')
        try:finite=math.isfinite(age)
        except OverflowError:finite=False
        if not finite:reject('age_nonfinite','age_seconds','time')
        if age<0:reject('age_negative','age_seconds','time')
        if type(value['clock_source']) is not str:reject('clock_type','clock_source','time')
        clocks=set(CLOCKS) if self.data_kind==DataKind.REAL or self._diagnostic.enabled else set()
        if self.data_kind==DataKind.SIMULATED:clocks.add('fixture')
        if value['clock_source'] not in clocks:reject('clock_uncontracted','clock_source','time')
        if type(value['readings']) is not dict:reject('readings_type','readings','readings')
        if set(value['readings'])!=DYNAMIC:reject('readings_keys','readings','readings')
        if self._diagnostic.enabled:self._validate_native_diagnostic(value)

    def _validate_native_diagnostic(self,value):
        def reject(rule):self._reject('native_time',rule,value,'diagnostic')
        d=value['diagnostic']
        expected={'profile','rule','timestamp_unit','age_unit','deltas_ms','match_count','converted_age_seconds','selected_clock'}
        if type(d) is not dict or set(d)!=expected or d.get('profile')!=PROFILE:reject('native_diagnostic_shape')
        if d['timestamp_unit']!='milliseconds' or d['age_unit']!='seconds':reject('native_diagnostic_units')
        deltas=d['deltas_ms']
        if type(deltas) is not dict or set(deltas)!=set(CLOCKS) or any(type(n) is not int or not -2**63<n<=2**63-1 for n in deltas.values()):reject('native_diagnostic_delta')
        matched=[name for name,n in deltas.items() if 0<=n<=5000]
        if type(d['match_count']) is not int or d['match_count']!=len(matched):reject('native_diagnostic_matches')
        if d['rule']!='clock_matched' or len(matched)!=1:reject('native_diagnostic_rule')
        if d['selected_clock']!=matched[0] or value['clock_source']!=matched[0]:reject('native_diagnostic_clock')
        conversion=deltas[matched[0]]/1000
        converted=d['converted_age_seconds']
        if (type(converted) not in (int,float) or not 0<=converted<=5 or not math.isfinite(converted)
                or not math.isclose(d['converted_age_seconds'],conversion,rel_tol=0,abs_tol=1e-9)
                or not math.isclose(value['age_seconds'],conversion,rel_tol=0,abs_tol=1e-9)):
            reject('native_diagnostic_conversion')

    def note_provider(self,rule,*,metric=None):
        self._diagnostic.emit('provider',rule,self._last_payload,metric=metric)

    def latest(self,key):
        self._key(key)
        if self._pending:raise BridgeError('read_still_pending')
        self._pending=True;self.transport.send('latest')
        try:value=self._next()
        except BridgeError as exc:
            if exc.code!='read_timeout':self._pending=False
            self._events.append(exc.code);raise
        self._pending=False
        if value.get('event')=='warming_up':raise WarmingUp()
        self._last_payload=value if self._diagnostic.enabled else None
        self._validate_frame(value)
        self.clock_sources.add(value['clock_source'])
        readings={}
        for name,r in value['readings'].items():
            try:readings[name]=self._reading(r)
            except BridgeError as exc:
                self._diagnostic.emit('readings',exc.rule,value,metric=name)
                raise
        age=value['age_seconds']+max(0,time.monotonic()-self._last_received)
        self.last_frame={'sdk_timestamp_ms':value['timestamp_ms'],'age_seconds':age,'clock_source':value['clock_source']}
        self._diagnostic.emit('frame','frame_structure_accepted',value)
        return Frame(key,value['timestamp_ms'],age,readings)

    def close(self):
        if self._closed:return
        self.clean=self.transport.close()
        if not self.clean:self._events.append('shutdown_timeout');raise BridgeError('shutdown_timeout')
        self._closed=True
        process=self.transport.process
        if process and process.returncode!=0:self.clean=False;raise BridgeError('worker_exit_failed')

    def diagnostics(self):
        result={'phases':list(self.phases),'clock_sources':sorted(self.clock_sources),'events':list(self._events),'closed':self._closed,'clean':self.clean}
        if self._diagnostic.enabled:result['frame_diagnostics']=self._diagnostic.snapshot()
        return result


def real_adapter(*,diagnostics=False):
    return NativeAdapter(LineTransport(lambda:launch_native(diagnostics=diagnostics)),diagnostics=diagnostics)
