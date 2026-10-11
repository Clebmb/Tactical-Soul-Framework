"""Conservative same-room enemy edits; no resource allocator or AI dispatcher."""
import struct
from dataclasses import replace,asdict
from .core import PatchError,number
from .rooms import Entity,dimensions,entities,room_address
from .enemies import SPEC,resolve,describe_enemy
from .tables import layout,read_record

def original_entities(rom,pointer):
    offset=rom.offset(pointer+20,4);address=int.from_bytes(rom.original[offset:offset+4],'little');rows=[]
    for i in range(256):
        off=rom.offset(address+i*12,12);values=struct.unpack('<hhBBBBHH',rom.original[off:off+12])
        if values[0]==32767:return rows
        rows.append(Entity(*values))
    raise PatchError('Original entity list missing terminator')

def native_code_unchanged(rom,index):
    _,address=layout('enemies',index);offset=rom.offset(address,8)
    return rom.read(address,8)==rom.original[offset:offset+8]

def audit_encounters(rom,sector,index):
    pointer=room_address(rom,sector,index);original=original_entities(rom,pointer)
    native={e.subtype for e in original if e.type==1};rows=entities(rom,pointer);report=[];errors=[]
    for entity in rows:
        if entity.type!=1:continue
        enemy=describe_enemy(rom,entity.subtype)
        evidence=entity.subtype in native
        if not evidence:errors.append(f'entity {entity.unique_id}: subtype absent from original room; resource provisioning unproven')
        if not native_code_unchanged(rom,entity.subtype):errors.append(f'entity {entity.unique_id}: native AI pointers changed')
        report.append({'entity_id':entity.unique_id,'enemy':enemy['key'],'index':entity.subtype,'position':[entity.x,entity.y],'parameters':{'byte_8':entity.byte_8,'var_a':entity.var_a,'var_b':entity.var_b},'original_same_subtype':evidence,'protected':enemy['protected_encounter']})
    return {'sector':sector,'room':index,'entities':report,'errors':errors,'scope':'same-subtype original-room evidence only; VRAM/OAM/palette capacity, collision and event behavior require native tests'}

def plan_encounter(rom,pointer,rows,edit):
    op=edit.get('op');required={'op','room','entity_id','enemy','from','to'} if op=='move' else {'op','room','source_id','entity_id','enemy','to'} if op=='clone' else set()
    if not required or set(edit)!=required:raise PatchError('Encounter op must be move or clone with exactly documented fields')
    enemy=resolve(rom,edit['enemy']);index=enemy['index']
    if enemy['protected_encounter']:raise PatchError('Boss/script-sensitive enemy placement is unsupported')
    if not native_code_unchanged(rom,index):raise PatchError('Encounter editing requires unchanged native AI pointers')
    original=original_entities(rom,pointer)
    source_id=number(edit['entity_id'] if op=='move' else edit['source_id'])
    native=[e for e in original if e.unique_id==source_id and e.type==1 and e.subtype==index]
    if len(native)!=1:raise PatchError('Encounter source must be one matching enemy in original room')
    source=native[0];identity=number(edit['entity_id']);to=[number(v) for v in edit['to']];w,h=dimensions(rom,pointer)
    if len(to)!=2 or not 0<=to[0]<w*256 or not 0<=to[1]<h*256:raise PatchError('Enemy position outside room')
    if op=='move':
        matches=[j for j,e in enumerate(rows) if e.unique_id==identity and e.type==1 and e.subtype==index]
        if len(matches)!=1:raise PatchError('Enemy move identity mismatch')
        j=matches[0];old=rows[j]
        if [number(v) for v in edit['from']]!=[old.x,old.y]:raise PatchError('Enemy coordinate precondition mismatch')
        rows[j]=replace(old,x=to[0],y=to[1])
    else:
        template=SPEC['clone_templates'].get(str(index))
        if not template or any(getattr(source,k)!=v for k,v in template.items()):raise PatchError('Enemy source is not a supported single-actor clone template')
        if not 0<=identity<=255 or any(e.unique_id==identity for e in rows+original):raise PatchError('Clone requires unused byte entity identity')
        if len(rows)-len(original)>=SPEC['max_clones_per_room'] or len(rows)>=255:raise PatchError('Conservative per-room clone limit exceeded')
        rows.append(replace(source,unique_id=identity,x=to[0],y=to[1]))
    return {'op':op,'entity_id':identity,'enemy':enemy['key'],'position':to,'resource_policy':'reuse original same-room subtype; native rendering must be tested'}
