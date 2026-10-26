"""Pure synthetic native frames. Counters below belong to this fixture, not production."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from threading import Event
from unittest.mock import patch
import unittest

from adlx_diagnostic_fakes import MemoryTransport,frame,unmatched
from monitoring.adlx_bridge import NativeAdapter
from monitoring.adlx_provider import AdlxProvider,GPU_SPECS
from monitoring.collector import ReadContext
from monitoring.contracts import Availability as A,DataKind
from monitoring_fakes import FakeClock


class AdmissionTests(unittest.TestCase):
    def exercise(self,frames):
        frames=deepcopy(frames)
        for value in frames:
            if value.get('event')=='frame' and value.get('clock_source')!='unverified':value['clock_source']='fixture'
        transport=MemoryTransport(frames,diagnostics=False)
        adapter=NativeAdapter(transport,data_kind=DataKind.SIMULATED,diagnostics=False)
        provider=AdlxProvider(adapter,'amd-rx6750xt',minimum_interval=2,maximum_sample_age=1.5)
        clock=FakeClock();stop=Event();counts=Counter();observations=[]
        # Count at the actual provider admission boundary, using its existing
        # accepted SDK timestamp; do not count seven metrics as seven frames.
        with patch('monitoring.adlx_bridge.time.monotonic',return_value=100):
            for _ in frames:
                before=provider.diagnostics()['sdk_timestamp_ms'];clock.advance(2)
                context=ReadContext(clock.utcnow(),clock.monotonic(),clock.monotonic()+1,stop)
                rows=provider.read(provider.metric_ids,context);after=provider.diagnostics()['sdk_timestamp_ms']
                counts['attempts']+=1
                if after!=before:counts['accepted']+=1
                elif any(o.state==A.WARMING_UP for o in rows):counts['warming_up']+=1
                else:counts['rejected']+=1
                observations.append(rows)
            self.assertEqual(counts['attempts'],counts['accepted']+counts['rejected']+counts['warming_up'])
            self.assertEqual(transport.starts,1);provider.close();self.assertTrue(transport.closed)
        return counts,observations

    def test_admission_boundary_and_nonfinite_future_old(self):
        values=[0,1.5,1.500001,-.000001,float('nan'),float('inf')]
        frames=[frame(stamp=10000+i,age=value,diagnostics=False) for i,value in enumerate(values)]
        counts,rows=self.exercise(frames)
        self.assertEqual((counts['accepted'],counts['rejected']),(2,4))
        for batch in rows[2:]:self.assertTrue(all(o.value is None for o in batch if o.metric_id!='gpu.adlx.vram_total_mb'))

    def test_first_age_null_and_invalid_valid_sequence_exact_counts(self):
        bad=unmatched();bad.pop('diagnostic')
        duplicate=frame(stamp=100,diagnostics=False)
        future=frame(stamp=101,age=-1,diagnostics=False)
        frames=[bad,frame(stamp=100,diagnostics=False),duplicate,future,frame(stamp=102,diagnostics=False)]
        counts,rows=self.exercise(frames)
        self.assertEqual((counts['attempts'],counts['accepted'],counts['rejected']),(5,2,3))
        self.assertTrue(all(o.value is None for o in rows[0] if o.metric_id!='gpu.adlx.vram_total_mb'))
        self.assertTrue(next(o for o in rows[-1] if o.metric_id=='gpu.adlx.utilization').state==A.AVAILABLE)

    def test_partial_all_unavailable_and_zero_are_not_frame_rejection(self):
        partial=frame(stamp=1,diagnostics=False);partial['readings']['gpu.adlx.temperature']={'state':'unavailable','value':None}
        missing=frame(stamp=2,diagnostics=False)
        for key in missing['readings']:missing['readings'][key]={'state':'unavailable','value':None}
        zero=frame(stamp=3,diagnostics=False);zero['readings']['gpu.adlx.utilization']['value']=0
        counts,rows=self.exercise([partial,missing,zero])
        self.assertEqual((counts['accepted'],counts['rejected']),(3,0))
        self.assertTrue(all(o.value is None for o in rows[1] if o.metric_id!='gpu.adlx.vram_total_mb'))
        self.assertEqual(next(o.value for o in rows[2] if o.metric_id=='gpu.adlx.utilization'),0)

    def test_invalid_readings_shape_version_and_warming_are_distinct(self):
        bad_shape=frame(stamp=1,diagnostics=False);bad_shape.pop('readings')
        bad_version=frame(stamp=2,diagnostics=False);bad_version['v']=2
        bad_nan=frame(stamp=3,diagnostics=False);bad_nan['readings']['gpu.adlx.temperature']['value']=float('nan')
        warm={'v':1,'event':'warming_up'}
        counts,_=self.exercise([bad_shape,bad_version,bad_nan,warm,frame(stamp=4,diagnostics=False)])
        self.assertEqual((counts['accepted'],counts['rejected'],counts['warming_up']),(1,3,1))

    def test_counters_do_not_infer_frames_from_snapshots_or_metric_count(self):
        counts,rows=self.exercise([frame(stamp=i+1,diagnostics=False) for i in range(40)])
        self.assertEqual(counts['accepted'],40)
        self.assertEqual(sum(len(batch) for batch in rows),40*8)
        self.assertNotEqual(counts['accepted'],40*8)


if __name__=='__main__':unittest.main()
