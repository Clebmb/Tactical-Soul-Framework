"""Refresh source hashes/documentation and available bounded local evidence.

Does not copy private images or ROM bytes. The inventory is a development index,
not a license audit, package allowlist or substitute for running verification.
Historical milestone fields are preserved; missing evidence is not a test pass.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'docs/PROJECT-INVENTORY.json'
data=json.loads(path.read_text())
data['project']='Tactical Soul Framework'
data['framework_version']=json.loads((ROOT/'framework/capabilities.json').read_text())['version']
data['documentation']=sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*.md')
                             if p.relative_to(ROOT).parts[0] in ('docs','examples') or p.parent==ROOT)
files=[]
for folder in ('aria','native','framework','examples','tests','docs','scripts','src'):
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(ROOT/name for name in ('.gitignore','README.md','AGENTS.md','handoff.md','BUILD.md','LICENSE','TacticalSoul.cmd','Dominance.cmd','Framework.cmd'))
data['files']=[{'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,
                'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files)) if p!=path]
for key,name in [('geometry_workshop','geometry-verification.json'),('rendering','rendering-verification.json'),('room_catalog','room-catalog-verification.json'),('custom_terrain','custom-terrain-verification.json'),('original_room_art','original-room-art-verification.json'),('room_resources','room-resource-verification.json'),('backgrounds','background-verification.json'),('background_rendering','background-rendering-verification.json'),('room_states','room-state-verification.json'),('two_room_art','two-room-art-verification.json'),('three_room_art','three-room-art-verification.json'),('world_graph','world-graph-verification.json'),('connection_plans','connection-plan-verification.json'),('connection_traversal','connection-traversal-verification.json'),('room5_search','room5-search-verification.json'),('bridge_route','bridge-route-traversal-verification.json'),('bridge_lifecycle','bridge-route-lifecycle-verification.json'),('terrain_support','terrain-support-verification.json'),('projects','project-verification.json'),('sprites','sprite-verification.json'),('sprite_assets','sprite-assets-verification.json'),('bridge_art','bridge-art-verification.json')]:
    evidence=ROOT/'local'/name
    if evidence.exists():
        value=json.loads(evidence.read_text())
        if key=='sprites':value={**value,'sprites':[{k:v for k,v in sprite.items() if k!='frames'} for sprite in value['sprites']]}
        if key=='room5_search':value={k:v for k,v in value.items() if k!='trials'}
        data[key]={k:v for k,v in value.items() if k!='rooms'} if key=='room_resources' else ({k:v for k,v in value.items() if k!='layers'} if key=='backgrounds' else value)
data['inventory_note']='Source inventory excludes its own hash, private assets/evidence files, builds, dev tools and runtime bulk files. Embedded bounded verification summaries reflect available local evidence, not newly executed tests. Historical milestone fields retain their original scope.'
path.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'project':data['project'],'version':data['framework_version'],'source_files':len(data['files']),'documentation_files':len(data['documentation'])},indent=2))
