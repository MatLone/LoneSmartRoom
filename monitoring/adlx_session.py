"""One bounded session with injected adapter/resources/clock; no native construction."""
from .adlx_provider import AdlxProvider, GPU_SPECS
from .basic_session import resource_sample, stats, summarize
from .collector import Collector, Schedule
from .contracts import ContractError, utc_text


def run_session(adapter,resources,clock,wait,*,duration=70,on_row=None):
    if type(duration) not in (int,float) or not 0<duration<=75:raise ContractError('invalid_session_duration')
    processors=resources.logical_processors()
    if type(processors) is not int or not 1<=processors<=4096:raise ContractError('invalid_processor_count')
    start=clock.monotonic();started=clock.utcnow();base=resources.collector();rows=[];reason='duration_complete';collector=None
    clean=False;failure=None;resource_failure=False;previous={};previous_time={};last_cpu=None
    try:
        adapter.open()
        devices=adapter.devices()
        if len(devices)!=1:raise ContractError('invalid_device_count')
        provider=AdlxProvider(adapter,devices[0].key)
        collector=Collector(GPU_SPECS,[provider],clock=clock,schedule=Schedule(fast=2,thermal=2,capacity=60,read_budget=1))
        while clock.monotonic()-start<duration:
            cycle=clock.monotonic();collector.step();snapshot=collector.snapshot();samples={}
            for name,read in [('collector',resources.collector),('bridge',resources.bridge)]:
                value=read();at=clock.monotonic();interval=at-previous_time.get(name,at)
                samples[name]=resource_sample(value,previous.get(name),interval,processors)
                previous[name]=value;previous_time[name]=at
            rows.append({'elapsed_seconds':clock.monotonic()-start,'snapshot':snapshot,
                         'sdk_frame':getattr(adapter,'last_frame',None),'resources':samples,
                         'cycle_seconds':clock.monotonic()-cycle,'cache_samples':collector.cache.sample_count})
            if on_row:on_row(rows[-1])
            if any(m['state'] in ('error','permission_denied') for m in snapshot['metrics']):reason='gpu_read_failed';break
            if any(v['working_set_bytes']>512*1024**2 for v in samples.values()):reason='memory_budget_exceeded';break
            if len(rows)>=40:reason='row_limit';break
            remaining=duration-(clock.monotonic()-start)
            if remaining>0:wait(min(remaining,max(0,2-(clock.monotonic()-cycle))))
    except Exception as exc:
        failure=exc.code if hasattr(exc,'code') else 'session_failed';reason='session_failed'
    finally:
        if collector:
            stopped=collector.stop(timeout=6);clean=stopped.stopped and stopped.clean
        else:
            try:adapter.close();clean=adapter.clean is True
            except Exception:clean=False
        try:last_cpu={'collector':resources.collector()['cpu_seconds'],'bridge':resources.bridge_cpu()}
        except Exception:resource_failure=True
    elapsed=clock.monotonic()-start;summary={}
    for component in ('collector','bridge'):
        values=[r['resources'][component] for r in rows]
        cpu=(last_cpu[component]-(base['cpu_seconds'] if component=='collector' else 0)) if last_cpu else None
        summary[component]={'cpu_percent_total_normalized':None if cpu is None or elapsed<=0 else cpu*100/elapsed/processors,
            'rss_bytes':stats(v['working_set_bytes'] for v in values),'private_commit_bytes':stats(v['private_commit_bytes'] for v in values),
            'interval_cpu_percent':stats(v['cpu_percent_total_normalized'] for v in values if v['cpu_percent_total_normalized'] is not None)}
    combined=None if any(v['cpu_percent_total_normalized'] is None for v in summary.values()) else sum(v['cpu_percent_total_normalized'] for v in summary.values())
    metrics=summarize(rows)
    if not rows and reason=='duration_complete':reason='no_gpu_samples'
    return {'startedUtc':started.isoformat(),'elapsedSeconds':elapsed,'reason':reason,'failure':failure,
        'shutdownClean':clean,'resourceReadFailed':resource_failure,'logicalProcessors':processors,'rows':rows,
        'metrics':metrics,'resourceSummary':summary,'combinedCpuPercentOfMachine':combined,
        'validDynamicMetrics':[key for key,value in metrics.items() if key!='gpu.adlx.vram_total_mb' and value['values']['count']>0],
        'combinedResidentBytes':stats(sum(v['working_set_bytes'] for v in row['resources'].values()) for row in rows),
        'adapterDiagnostics':adapter.diagnostics(),'collectorDiagnostics':list(collector.diagnostics()) if collector else [],
        'forcedTermination':False,'restarted':False}
