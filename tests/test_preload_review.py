"""Mechanical review of the exact a7310a4 preload delta; no hash auto-update."""
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from preservation_rules import reviewed_version_update


class PreloadReview(unittest.TestCase):
    def test_only_enumerated_simulated_query_was_added_to_previous_pin(self):
        current = (ROOT / 'apps/windows-ui/preload.cjs').read_bytes()
        delta = b"""  getDiagnostics: (scenario='overview') => {
    if(typeof scenario!=='string'||!['overview','healthy','inactive','offline','listener-mismatch','auth-failure','pipe-absent','sensor-unavailable','stale','provider-error','unverified','recovered','startup-inconclusive'].includes(scenario))
      return Promise.reject(new Error('Invalid diagnostic scenario'));
    return ipcRenderer.invoke('diagnostics:snapshot',{v:1,scenario});
  },
"""
        self.assertEqual(current.count(delta), 1)
        self.assertEqual(hashlib.sha256(current.replace(delta, b'', 1)).hexdigest(),
                         '5fc9553bd9f9cddb98f099a8fc1c0d7ea53ae197c12e87eb5f628755a6481eba')
        self.assertEqual(hashlib.sha256(current).hexdigest(),
                         'c20b427fea83d32c456cabacdc894fa5286df2647dbf5c693ea005b2011d3046')
        self.assertEqual(reviewed_version_update('apps/windows-ui/preload.cjs', b''), current)


if __name__ == '__main__':
    unittest.main()
