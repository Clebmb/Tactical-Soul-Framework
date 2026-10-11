"""Reproduce static repair evidence; no native traversal certification."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.connection_plans import plan_connections
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes()
r=load_image(host);apply_manifest(r,ROOT/'examples/three-room-art/mod.json')
snapshot=copy.deepcopy(r.__dict__)
spec=json.loads((ROOT/'examples/three-room-art/neighbor-repair-plan.json').read_text())
p=plan_connections(r,spec)
assert p==plan_connections(r,spec) and r.__dict__==snapshot and host.read_bytes()==original
assert len(p['changes']['changed_edges'])==4 and len(p['restored_observed_return_edges'])==4
assert p['before_summary']['edges_without_observed_direct_return']==7
assert p['after_summary']['edges_without_observed_direct_return']==3
report={k:p[k] for k in ('status','input_sha256','proposed_image_sha256','before_summary','after_summary','restored_observed_return_edges')}
report['passed']=['deterministic proposal','four restored observed returns','source image and allocation state unchanged','original host unchanged']
report['limitations']=['native landing and progression unverified','proposal emits no playable ROM']
(ROOT/'local').mkdir(exist_ok=True)
(ROOT/'local/connection-plan-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
