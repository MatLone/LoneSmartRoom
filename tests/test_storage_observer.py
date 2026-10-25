"""Synthetic resource accounting only; no processes, pipes or sensors."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('storage_validation',Path(__file__).resolve().parents[1]/'scripts/validate-storage-session.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ObserverTests(unittest.TestCase):
    def test_components_cpu_normalization_and_total(self):
        cpu={1:{'group':'collector','cpu_seconds':1},2:{'group':'ipc','cpu_seconds':2},3:{'group':'electron','cpu_seconds':3}}
        result=module.summary([],cpu,10,4)
        self.assertEqual(result['collector']['average_cpu_total_percent'],2.5)
        self.assertEqual(result['ipc']['average_cpu_total_percent'],5)
        self.assertEqual(result['electron']['average_cpu_total_percent'],7.5)
        self.assertEqual(result['total']['average_cpu_total_percent'],15)

    def test_partial_startup_not_fake_zero_resident(self):
        result=module.summary([{'complete':False,'groups':{}}],{},10,4)
        self.assertIsNone(result['collector']['working_set_bytes']);self.assertEqual(result['collector']['resident_samples'],0)

    def test_resident_components_and_shared_sum_not_exclusive(self):
        group={k:{'working_set_bytes':v} for k,v in [('collector',10),('ipc',20),('electron',40),('total',70)]}
        result=module.summary([{'complete':True,'groups':group}],{},10,4)
        self.assertEqual(result['total']['working_set_bytes'],{'min':70,'mean':70,'max':70})

    def test_invalid_denominators(self):
        for duration,cores in [(0,4),(10,0),(-1,4)]:
            with self.assertRaises(ValueError):module.summary([],{},duration,cores)


if __name__=='__main__':unittest.main()
