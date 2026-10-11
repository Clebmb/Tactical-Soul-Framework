"""Named native enemy balance and item drops. No AI-pointer swapping or grants."""
import json
from pathlib import Path
from .core import PatchError,number
from .tables import layout,read_record,edit_record,LAYOUTS
from .equipment import key_for,item_name
from .text import original_label
SPEC=json.loads((Path(__file__).resolve().parents[1]/'framework/enemies.json').read_text())

def flags_view(field,value):
    names=SPEC['flags'][field];known=sum(1<<b for b in names.values())
    return {'names':[n for n,b in names.items() if value&(1<<b)],'raw':value,'unknown_mask':f'0x{value&~known:04X}'}

def item_drop(rom,pickup_id,rarity):
    if pickup_id==0:return {'item':None,'pickup_id':0,'rarity':rarity}
    if not 1<=pickup_id<=136:return {'item':None,'pickup_id':pickup_id,'rarity':rarity,'warning':'outside ordinary item range'}
    name=item_name(rom,pickup_id-1)
    return {'item':name,'key':key_for(name),'global_id':pickup_id-1,'pickup_id':pickup_id,'rarity':rarity}

def describe_enemy(rom,index):
    index=number(index);_,address=layout('enemies',index);fields=read_record(rom,'enemies',index)
    name=original_label(rom,0x25d+index)
    return {'key':key_for(name),'name':name,'index':index,'entity_subtype':index,'address':hex(address),'protected_encounter':index in SPEC['protected_encounter_indices'],'fields':fields,'flags':{f:flags_view(f,fields[f]) for f in SPEC['flags']},'drops':{f:item_drop(rom,fields[f],fields[f+'_rarity']) for f in ('item_1','item_2')},'soul':{'type':fields['soul_type'],'index':fields['soul'],'rarity':fields['soul_rarity'],'policy':'preserved reference; zero rarity disables drop'},'behavior':{'create_code':hex(fields['create_code']),'update_code':hex(fields['update_code']),'policy':'native entrypoints preserved; arbitrary AI replacement unsupported'}}

def catalog(rom,query=None):
    rows=[describe_enemy(rom,i) for i in range(LAYOUTS['enemies']['count'])]
    return [r for r in rows if not query or query.casefold() in r['name'].casefold() or query.casefold() in r['key']]

def resolve(rom,enemy=None,index=None):
    if (enemy is None)==(index is None):raise PatchError('Specify exactly one enemy name/key or index')
    if index is not None:return describe_enemy(rom,index)
    if not isinstance(enemy,str):raise PatchError('Enemy name must be a string')
    matches=[r for r in catalog(rom) if enemy.casefold() in (r['name'].casefold(),r['key'].casefold())]
    if len(matches)!=1:raise PatchError('Enemy name/key must match exactly one record')
    return matches[0]

def resolve_drop(rom,value):
    if value is None:return 0
    if not isinstance(value,str):raise PatchError('Drop item must be an exact name/key or null')
    matches=[i+1 for i in range(136) if value.casefold() in (item_name(rom,i).casefold(),key_for(item_name(rom,i)))]
    if len(matches)!=1:raise PatchError('Drop name/key must match exactly one ordinary item')
    return matches[0]

def apply_enemy_edits(rom,edits):
    pending=[];claimed=set()
    for edit in edits:
        if set(edit)-{'enemy','index','expect','fields','flags','drops'}:raise PatchError('Unknown enemy edit properties')
        row=resolve(rom,edit.get('enemy'),edit.get('index'));old=row['fields']
        fields=edit.get('fields',{});flags=edit.get('flags',{});drops=edit.get('drops',{});expect=edit.get('expect',{})
        if not fields and not flags and not drops:raise PatchError('Enemy edit is empty')
        if set(fields)-set(SPEC['editable_fields']):raise PatchError('Enemy field outside safe editable set')
        if set(flags)-set(SPEC['flags']):raise PatchError('Unknown enemy flag field')
        if set(drops)-{'item_1','item_2'}:raise PatchError('Unknown drop slot')
        changed=set(fields)|set(flags)|set(drops)|{f+'_rarity' for f in drops}
        if not changed<=set(expect):raise PatchError('expect must cover every changed enemy/drop/flag field')
        for field,value in expect.items():
            if field not in old or number(value)!=old[field]:raise PatchError('Enemy precondition mismatch: '+field)
        values={}
        for field,value in fields.items():
            value=number(value);size=LAYOUTS['enemies']['fields'][field]['size'];low=1 if field=='hp' else 0
            if not low<=value<(1<<(size*8)):raise PatchError('Enemy field outside semantic range: '+field)
            values[field]=value
        for field,update in flags.items():
            if not isinstance(update,dict) or set(update)-{'add','remove'} or not update:raise PatchError('Flag update requires add/remove lists')
            add,remove=update.get('add',[]),update.get('remove',[])
            if not isinstance(add,list) or not isinstance(remove,list) or any(not isinstance(n,str) for n in add+remove):raise PatchError('Flag names must be string lists')
            if set(add)&set(remove) or len(set(add))!=len(add) or len(set(remove))!=len(remove):raise PatchError('Duplicate/contradictory enemy flag update')
            names=SPEC['flags'][field]
            if set(add+remove)-set(names):raise PatchError('Unknown enemy flag name')
            value=old[field]
            for n in add:value|=1<<names[n]
            for n in remove:value&=~(1<<names[n])
            values[field]=value
        for field,drop in drops.items():
            if not isinstance(drop,dict) or set(drop)!={'item','rarity'}:raise PatchError('Drop requires item and rarity')
            rarity=number(drop['rarity'])
            if not 0<=rarity<=255:raise PatchError('Item rarity outside byte range')
            values[field]=resolve_drop(rom,drop['item']);values[field+'_rarity']=rarity
        for field in values:
            claim=(row['index'],field)
            if claim in claimed:raise PatchError('Repeated enemy field edit')
            claimed.add(claim)
        pending.append((row,values))
    report=[]
    for row,values in pending:
        edit_record(rom,'enemies',row['index'],values)
        after=describe_enemy(rom,row['index'])
        report.append({'key':row['key'],'index':row['index'],'before':{f:row['fields'][f] for f in values},'after':{f:after['fields'][f] for f in values},'drops':after['drops'],'flags':after['flags']})
    return report
