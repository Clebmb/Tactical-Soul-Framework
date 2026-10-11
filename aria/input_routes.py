"""Bounded input-only replay contracts, independent of the native core library.

Assertions are sampled after each segment, not continuously during it. No
position/ability/HP writes occur here; callers must declare bootstrap fixtures.
"""
import copy
from .core import PatchError

FIELDS={'room_address','state','substate','world_x','world_y','hp'}

def validate_input_route(spec):
    if not isinstance(spec,dict) or set(spec)!={'schema_version','id','segments'}:
        raise PatchError('Input route requires schema_version, id and segments')
    if type(spec['schema_version']) is not int or spec['schema_version']!=1:
        raise PatchError('Unsupported input route schema')
    if not isinstance(spec['id'],str) or not 1<=len(spec['id'])<=80:
        raise PatchError('Input route ID must be 1..80 characters')
    rows=spec['segments']
    if not isinstance(rows,list) or not 1<=len(rows)<=1024:raise PatchError('Input route requires 1..1024 segments')
    labels=set();total=0
    for row in rows:
        if not isinstance(row,dict) or set(row)-{'label','frames','keys','expect'} or not {'label','frames','keys'}<=set(row):
            raise PatchError('Input segment requires label, frames, keys and optional expect')
        label=row['label']
        if not isinstance(label,str) or not 1<=len(label)<=80 or label in labels:raise PatchError('Segment labels must be unique nonempty strings up to 80 characters')
        labels.add(label)
        if type(row['frames']) is not int or not 1<=row['frames']<=3600:raise PatchError('Segment frames must be integer 1..3600')
        total+=row['frames']
        keys=row['keys']
        if not isinstance(keys,list) or any(type(k) is not int or not 0<=k<=15 for k in keys) or len(set(keys))!=len(keys):
            raise PatchError('Keys must be unique libretro joypad IDs 0..15')
        expect=row.get('expect',{})
        if not isinstance(expect,dict) or set(expect)-FIELDS:raise PatchError('Unknown input-route observation')
        for value in expect.values():
            if type(value) is int:continue
            if not isinstance(value,list) or len(value)!=2 or any(type(v) is not int for v in value) or value[0]>value[1]:
                raise PatchError('Expectation must be integer or inclusive integer range')
    if total>36000:raise PatchError('Input route exceeds 36000 frames')
    return copy.deepcopy(spec)

def observe_native(emulator):
    """Read the currently established AoS USA runtime observations only."""
    return {'room_address':emulator.read(0x02000088),'state':emulator.read(0x02000010,1),
            'substate':emulator.read(0x02000064,1),
            'world_x':emulator.read(0x02000526,2)+emulator.read(0x0200A09A,2),
            'world_y':emulator.read(0x0200052A,2)+emulator.read(0x0200A09E,2),
            'hp':emulator.read(0x0201327A,2)}

def replay_input_route(emulator,spec,observer=observe_native):
    """Validate before input; stop at first failed endpoint assertion."""
    route=validate_input_route(spec);samples=[];elapsed=0
    for row in route['segments']:
        emulator.run(row['frames'],row['keys']);elapsed+=row['frames']
        observation=observer(emulator);failures=[]
        for field,value in row.get('expect',{}).items():
            actual=observation.get(field)
            match=type(actual) is int and (actual==value if type(value) is int else value[0]<=actual<=value[1])
            if not match:failures.append({'field':field,'expected':value,'actual':actual})
        samples.append({'label':row['label'],'elapsed_frames':elapsed,'frames':row['frames'],
                        'keys':row['keys'],'observation':observation,'failures':failures})
        if failures:return {'schema_version':1,'id':route['id'],'status':'failed','samples':samples}
    return {'schema_version':1,'id':route['id'],'status':'passed','samples':samples}
