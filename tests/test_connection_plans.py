import copy,json,unittest
from pathlib import Path
from aria.core import PatchError
from aria.cli import load_image,apply_manifest
from aria.connection_plans import plan_connections

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless((ROOT/'CastlevaniaAoS.gba').exists(),'Private host absent')
class ConnectionPlanTests(unittest.TestCase):
    def setUp(self):
        self.r=load_image(ROOT/'CastlevaniaAoS.gba');apply_manifest(self.r,ROOT/'examples/three-room-art/mod.json')
        self.spec=json.loads((ROOT/'examples/three-room-art/neighbor-repair-plan.json').read_text())
    def snapshot(self):
        return bytes(self.r.data),copy.deepcopy(self.r.ledger),copy.deepcopy(self.r.allocations),self.r.cursors[:],copy.deepcopy(self.r.profile)
    def test_proposal_restores_four_returns_without_mutation(self):
        before=self.snapshot();p=plan_connections(self.r,self.spec)
        self.assertEqual(p['before_summary']['edges_without_observed_direct_return'],7)
        self.assertEqual(p['after_summary']['edges_without_observed_direct_return'],3)
        self.assertEqual(len(p['restored_observed_return_edges']),4)
        self.assertEqual(len(p['changes']['changed_edges']),4);self.assertEqual(self.snapshot(),before)
        self.assertEqual(p['status'],'static_proposal_not_gameplay_verified')
    def test_failure_preserves_image_and_allocation_state(self):
        for key in ('hash','sides','spawn','duplicate'):
            s=copy.deepcopy(self.spec)
            if key=='hash':s['expected_image_sha256']='0'*64
            elif key=='sides':s['connections'][0]['b']['door']=0
            elif key=='spawn':s['connections'][0]['b']['spawn']=[9999,0]
            else:s['connections']*=2
            before=self.snapshot()
            with self.assertRaises(PatchError):plan_connections(self.r,s)
            self.assertEqual(self.snapshot(),before)
    def test_deterministic_and_no_spec_mutation(self):
        original=copy.deepcopy(self.spec);a=plan_connections(self.r,self.spec);b=plan_connections(self.r,self.spec)
        self.assertEqual(a,b);self.assertEqual(self.spec,original)
    def test_empty_unknown_and_boolean_schema_rejected(self):
        for s in ({},dict(self.spec,connections=[]),dict(self.spec,schema_version=True),dict(self.spec,extra=1)):
            with self.assertRaises(PatchError):plan_connections(self.r,s)
