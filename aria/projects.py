"""Versioned source-project composition into the existing manifest contract.

Module order controls first appearance and list order, not sequential patching.
Relative module/assets stay confined to the project and owning module folders.
"""
import copy,hashlib,json,re
from pathlib import Path
from .core import PatchError,number

LISTS={'geometry_edits','room_assets','sprite_assets','enemy_encounters','enemy_edits',
       'equipment_edits','table_edits','resource_edits','label_edits'}
META={'schema_version','id','description'}

def _json(path):
    raw=path.read_bytes()
    if len(raw)>2*1024*1024:raise PatchError('Project/module JSON exceeds 2 MiB: '+path.name)
    value=json.loads(raw.decode('utf-8'))
    if not isinstance(value,dict):raise PatchError('Project/module must be an object: '+path.name)
    return value,hashlib.sha256(raw).hexdigest()

def _file(folder,name):
    if not isinstance(name,str) or not name or Path(name).is_absolute():raise PatchError('Project paths must be nonempty relative paths')
    path=(folder/name).resolve()
    if not path.is_relative_to(folder.resolve()):raise PatchError('Project/module path escapes its owning folder: '+name)
    if not path.is_file():raise PatchError('Project input does not exist: '+name)
    return path

def _id(value):
    return isinstance(value,str) and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}',value)

def _room(ref):
    if not isinstance(ref,dict) or set(ref)!={'sector','room'}:raise PatchError('Invalid composed room reference')
    s,i=number(ref['sector']),number(ref['room'])
    if not 0<=s<12 or not 0<=i<256:raise PatchError('Composed room outside bounds')
    return s,i

def compose_project(path):
    """Read source files, resolve assets and reject ownership collisions early.

    Produces an ordinary schema-1 manifest plus source fingerprints. No ROM is
    loaded or mutated, and no generated manifest is written to disk.
    """
    path=Path(path).resolve();project,digest=_json(path);root=path.parent
    required={'schema_version','kind','id','modules'}
    if not required<=set(project) or set(project)-required-{'description'}:raise PatchError('Invalid project fields')
    if type(project['schema_version']) is not int or project['schema_version']!=1 or project['kind']!='tsf-project' or not _id(project['id']):
        raise PatchError('Require schema 1, kind tsf-project and safe project id')
    paths=project['modules']
    if not isinstance(paths,list) or not 1<=len(paths)<=64:raise PatchError('Project requires 1..64 ordered module paths')
    merged={'schema_version':1,'id':project['id'],'description':project.get('description','Composed Tactical Soul Framework project')}
    if not isinstance(merged['description'],str):raise PatchError('Project description must be text')
    sources=[];assets={};seen_paths=set();seen_ids=set();geometry={};cell_owners={};custom_owners={};endpoints={};moves={};sprite_owners={}
    for name in paths:
        module_path=_file(root,name)
        if module_path.suffix.lower()!='.json':raise PatchError('Module paths must be JSON')
        if module_path in seen_paths:raise PatchError('Duplicate module path: '+name)
        seen_paths.add(module_path);module,module_hash=_json(module_path);owner=module.get('id')
        if type(module.get('schema_version')) is not int or module['schema_version']!=1 or not _id(owner):raise PatchError('Invalid module schema/id: '+name)
        if owner in seen_ids:raise PatchError('Duplicate module id: '+owner)
        seen_ids.add(owner)
        unsupported=set(module)-META-LISTS-{'room_edits'}
        if unsupported:raise PatchError('Module '+owner+' has unsupported project fields: '+', '.join(sorted(unsupported)))
        sources.append({'id':owner,'path':module_path.relative_to(root).as_posix(),'sha256':module_hash})
        for key in sorted(LISTS):
            if key not in module:continue
            if not isinstance(module[key],list):raise PatchError('Module '+owner+': '+key+' must be a list')
            for source_entry in module[key]:
                if not isinstance(source_entry,dict):raise PatchError('Module '+owner+': '+key+' entries must be objects')
                entry=copy.deepcopy(source_entry)
                if key=='geometry_edits':
                    required_entry={'room','layer','expected_layout_sha256','cells'}
                    if not required_entry<=set(entry) or set(entry)-required_entry-{'metatiles'}:raise PatchError('Invalid geometry entry in '+owner)
                    layer=number(entry['layer'])
                    if not 0<=layer<=2:raise PatchError('Invalid geometry layer in '+owner)
                    group=(*_room(entry['room']),layer)
                    if not isinstance(entry['cells'],list):raise PatchError('Geometry cells must be a list in '+owner)
                    if group in geometry and geometry[group]['expected_layout_sha256']!=entry['expected_layout_sha256']:
                        raise PatchError('Geometry preimage disagreement at '+str(group)+' in '+owner)
                    if group not in geometry:
                        geometry[group]=dict(entry,cells=[]);geometry[group].pop('metatiles',None)
                        merged.setdefault(key,[]).append(geometry[group])
                    for cell in entry['cells']:
                        if not isinstance(cell,dict) or set(cell)!={'x','y','expect','value'}:raise PatchError('Invalid geometry cell in '+owner)
                        claim=(*group,number(cell['x']),number(cell['y']))
                        if claim in cell_owners:raise PatchError('Geometry cell conflict '+str(claim)+' between '+cell_owners[claim]+' and '+owner)
                        cell_owners[claim]=owner;geometry[group]['cells'].append(cell)
                    if 'metatiles' in entry:
                        if group in custom_owners:raise PatchError('Multiple custom metatile providers at '+str(group)+' between '+custom_owners[group]+' and '+owner)
                        custom_owners[group]=owner;geometry[group]['metatiles']=entry['metatiles']
                    continue
                if key=='room_assets':
                    for field in ('graphics_source','palette_source'):
                        asset=_file(module_path.parent,entry.get(field))
                        relative=asset.relative_to(root).as_posix();entry[field]=relative
                        assets[relative]={'path':relative,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest()}
                if key=='sprite_assets':
                    resource=entry.get('resource')
                    if not isinstance(resource,str) or not resource:
                        raise PatchError('Module '+owner+': sprite_assets entries require a resource name')
                    if resource in sprite_owners:
                        raise PatchError('Sprite resource conflict '+resource+' between '+sprite_owners[resource]+' and '+owner)
                    sprite_owners[resource]=owner
                    for field in ('source','palette_source'):
                        if field not in entry:continue
                        asset=_file(module_path.parent,entry.get(field))
                        relative=asset.relative_to(root).as_posix();entry[field]=relative
                        assets[relative]={'path':relative,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest()}
                merged.setdefault(key,[]).append(entry)
        if 'room_edits' in module:
            edits=module['room_edits']
            if not isinstance(edits,dict) or set(edits)-{'moves','connections'}:raise PatchError('Invalid room_edits in '+owner)
            for key,entries in edits.items():
                if not isinstance(entries,list):raise PatchError('room_edits lists required in '+owner)
                for source_entry in entries:
                    entry=copy.deepcopy(source_entry)
                    if not isinstance(entry,dict):raise PatchError('Invalid room edit in '+owner)
                    if key=='connections':
                        if set(entry)!={'a','b'}:raise PatchError('Connection requires a/b in '+owner)
                        for end in entry.values():
                            if not isinstance(end,dict) or set(end)!={'room','door','spawn'}:raise PatchError('Invalid endpoint in '+owner)
                            claim=(*_room(end['room']),number(end['door']))
                            if claim in endpoints:raise PatchError('Door endpoint conflict '+str(claim)+' between '+endpoints[claim]+' and '+owner)
                            endpoints[claim]=owner
                    else:
                        if set(entry)!={'room','entity_id','from','to'}:raise PatchError('Invalid entity move in '+owner)
                        claim=(*_room(entry['room']),number(entry['entity_id']))
                        if claim in moves:raise PatchError('Entity move conflict '+str(claim)+' between '+moves[claim]+' and '+owner)
                        moves[claim]=owner
                    merged.setdefault('room_edits',{}).setdefault(key,[]).append(entry)
    report={'schema_version':1,'project_id':project['id'],'project_sha256':digest,
            'modules':sources,'assets':[assets[k] for k in sorted(assets)],
            'geometry_batches':len(geometry),'geometry_cells':len(cell_owners),'door_endpoints':len(endpoints),
            'scope':'ordered declarative composition; domain writers and patch ledger remain authoritative; no native certification'}
    return {'manifest':merged,'report':report}
