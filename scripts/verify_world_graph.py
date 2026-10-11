"""Static graph evidence; no campaign progression or landing certification."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.world_graph import audit_world_graph,compare_world_graphs
host=ROOT/'CastlevaniaAoS.gba';r=load_image(host);original=bytes(r.data)
a=audit_world_graph(r)
assert a['enumeration_complete'] and a['summary']['rooms']==343 and a['summary']['doors']==725
assert a['summary']['unresolved_destinations']==0
assert bytes(r.data)==original and not r.ledger and not r.allocations
apply_manifest(r,ROOT/'examples/three-room-art/mod.json');patched=bytes(r.data);ledger=list(r.ledger)
b=audit_world_graph(r);d=compare_world_graphs(a,b)
assert b['enumeration_complete'] and len(d['changed_edges'])==4
displaced=sorted({edge for c in d['changed_edges'] for edge in c['surviving_incoming_edges_without_return']})
assert len(displaced)==4 and bytes(r.data)==patched and r.ledger==ledger and host.read_bytes()==original
report={'passed':['343 rooms and 725 original doors resolve','graph inspection leaves original/patched images and ledger unchanged',
                  'three-room route reports four changed endpoints and four displaced incoming links','original unchanged'],
        'original_summary':a['summary'],'modified_summary':b['summary'],'displaced_incoming_edges':displaced,
        'limitations':['static base-slot observations only','missing direct return is not a softlock proof','no graph repair, event/progression or native landing verification']}
folder=ROOT/'local';folder.mkdir(exist_ok=True)
(folder/'world-graph-verification.json').write_text(json.dumps(report,indent=2))
(folder/'three-room-world-graph.json').write_text(json.dumps({'graph':b,'changes':d},indent=2))
print(json.dumps(report,indent=2))
