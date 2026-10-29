"""Passive bounded resource observer for this installed app only; never launches or stops it."""
import ctypes as ct
from ctypes import wintypes as w
from datetime import datetime,timezone
import json,os
from pathlib import Path
import statistics
import sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from monitoring.winpipe import WindowsPipeApi,bind

def main():
    if sys.argv[1:]:raise ValueError('fixed_scope_only')
    api=WindowsPipeApi();enum=bind(api.k,'K32EnumProcesses',[ct.POINTER(w.DWORD),w.DWORD,ct.POINTER(w.DWORD)],w.BOOL)
    installed=os.path.normcase(str(Path.home()/'AppData/Local/Programs/Lone Smart Room'))+os.sep
    handles={};previous={};rows=[];seen=False;first=None;start=time.monotonic();empty=0
    try:
        while time.monotonic()-start<210:
            ids=(w.DWORD*4096)();size=w.DWORD()
            if not enum(ids,ct.sizeof(ids),ct.byref(size)):raise OSError('process_inventory_failed')
            if size.value>=ct.sizeof(ids):raise ValueError('process_inventory_limit')
            for pid in ids[:size.value//4]:
                if pid in handles or not pid:continue
                handle=None
                try:
                    handle=api.hold_process(int(pid));image=ct.create_unicode_buffer(32768);length=w.DWORD(32768)
                    if not api.k.QueryFullProcessImageNameW(handle,0,image,ct.byref(length)):continue
                    name=os.path.normcase(image.value)
                    if not name.startswith(installed):continue
                    identity=api.identity(handle)
                    if identity['elevated'] or identity['sid']!=api.own['sid'] or identity['session']!=api.own['session']:raise ValueError('component_identity')
                    role='electron' if name.endswith('lone smart room.exe') else 'adlx' if name.endswith('bridge.exe') else 'python_ipc_collector' if name.endswith('python.exe') else 'other_owned'
                    handles[pid]=(handle,role);handle=None
                except OSError:pass
                finally:
                    if handle is not None:api.close(handle)
            now=time.monotonic();values=[]
            for pid,(handle,role) in list(handles.items()):
                if not api.alive(handle):api.close(handle);handles.pop(pid);continue
                resource=api.resources(handle);cpu=None
                if pid in previous:
                    at,used=previous[pid];cpu=max(0,(resource['cpu_seconds']-used)/(now-at)/(os.cpu_count() or 1)*100)
                previous[pid]=(now,resource['cpu_seconds']);values.append(dict(pid=pid,role=role,cpu_total_percent=cpu,rss_mib=resource['working_set_bytes']/1048576))
            if values:
                if not seen:seen=True;first=now
                empty=0;rows.append(dict(at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=now-first,processes=values))
            elif seen:
                empty+=1
                if empty>=2:break
            if not seen and now-start>30:break
            if seen and now-first>180:break
            time.sleep(2)
        remaining=[dict(pid=pid,role=role) for pid,(handle,role) in handles.items() if api.alive(handle)]
        components={}
        for role in ['electron','adlx','python_ipc_collector']:
            series=[sum(p['rss_mib'] for p in r['processes'] if p['role']==role) for r in rows]
            cpu=[sum(p['cpu_total_percent'] or 0 for p in r['processes'] if p['role']==role) for r in rows[1:]]
            components[role]=dict(rss_mean_mib=statistics.mean(series) if series else None,rss_peak_mib=max(series,default=None),cpu_mean_total_percent=statistics.mean(cpu) if cpu else None,cpu_peak_total_percent=max(cpu,default=None))
        report=dict(v=1,observed=seen,elapsed_observation_seconds=time.monotonic()-first if first else None,sample_interval_target_seconds=2,logical_processors=os.cpu_count(),components=components,rows=rows,residual=remaining,forced_actions=False,method='GetProcessTimes delta / wall interval / logical CPU count; sum RSS can double-count shared pages; Python IPC and collector grouped by image')
        out=ROOT/'.cache/validation/windows-focused-installation';out.mkdir(parents=True,exist_ok=True)
        with (out/'physical-resources.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
        print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    finally:
        for handle,_ in handles.values():api.close(handle)
if __name__=='__main__':main()
