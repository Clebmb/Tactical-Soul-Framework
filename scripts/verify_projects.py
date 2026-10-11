"""Reproduce modular/flat image equivalence; no native execution required."""
import sys,json,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image,apply_manifest
from aria.projects import compose_project
host=ROOT/'CastlevaniaAoS.gba';original=host.read_bytes();a=load_image(host);b=load_image(host)
project=ROOT/'examples/bridge-project/project.json';bundle=compose_project(project);assert bundle==compose_project(project)
apply_manifest(a,project);apply_manifest(b,ROOT/'examples/bridge-route/mod.json')
assert a.data==b.data and a.ledger==b.ledger and a.allocations==b.allocations and a.cursors==b.cursors
assert hashlib.sha256(a.data).hexdigest()=='bbe3d4b0cc80eee76bec1c77322050caf4547b9641c4e450457bbf22fe7fe840'
assert len(bundle['manifest']['geometry_edits'])==4 and len(bundle['report']['modules'])==5 and host.read_bytes()==original
sky_project=ROOT/'examples/sky-invaders/project.json';sky_bundle=compose_project(sky_project)
c=load_image(host);d=load_image(host)
apply_manifest(c,sky_project);apply_manifest(d,ROOT/'examples/sky-invaders/mod.json')
assert c.data==d.data and c.ledger==d.ledger and c.allocations==d.allocations and c.cursors==d.cursors
assert hashlib.sha256(c.data).hexdigest()=='3b17a2fd90da7c332d0181c66da55583432d56b1a3013af3378ae9ed4b02f1bd'
assert [m['id'] for m in sky_bundle['report']['modules']]==['sky-art'] and len(sky_bundle['report']['assets'])==2
assert host.read_bytes()==original
report={'status':'project_composition_verified','output_sha256':hashlib.sha256(a.data).hexdigest(),'modules':5,'geometry_batches':4,
        'sprite_project_sha256':hashlib.sha256(c.data).hexdigest(),
        'passed':['modular and flat images, ledgers, allocations and cursors identical','two room5 terrain modules combined into one checked batch','source/module/asset fingerprints recorded','composed sky-invaders project reproduces the flat sprite reskin bytes exactly','original unchanged'],
        'limitations':['no new native behavior; identical final images reuse prior bridge/sprite evidence','project supports declared data/terrain/room-art/sprite modules; hooks/content/raw patch modules excluded','module order is declarative merge order, not sequential patch semantics']}
(ROOT/'local').mkdir(exist_ok=True);(ROOT/'local/project-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
