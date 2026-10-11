"""Named, signed equipment view over verified native tables.

Names are read locally from the immutable original, not bundled extracted text.
Safe edits preserve IDs, sprites, attack families, unknown bytes and unknown flags.
The low-level tables API intentionally retains its unsigned storage contract.
"""
import json,re
from pathlib import Path
from .core import PatchError,number
from .tables import layout,read_record,edit_record
SPEC=json.loads((Path(__file__).resolve().parents[1]/'framework/equipment.json').read_text())
from .text import original_label

def item_name(rom,global_id):
    return original_label(rom,0x5b+global_id)

def key_for(name):return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')

def flags_view(field,value):
    names=SPEC['flags'][field]
    known=sum(1<<bit for bit in names.values())
    return {'names':[n for n,b in names.items() if value&(1<<b)],'unknown_mask':f'0x{value&~known:04X}','raw':value}

def describe_equipment(rom,table,index):
    if table not in SPEC['tables']:raise PatchError('Equipment table must be weapons or armor')
    index=number(index);spec,address=layout(table,index);raw=read_record(rom,table,index)
    global_id=SPEC['tables'][table]['global_base']+index
    name=item_name(rom,global_id);values=dict(raw)
    for field in SPEC['signed_fields']:
        if values[field]>=128:values[field]-=256
    flag='effects' if table=='weapons' else 'resistances'
    slot='weapon' if table=='weapons' else {0:'body',1:'accessory'}.get(raw['type'],'unknown')
    return {'key':key_for(name),'name':name,'table':table,'index':index,'global_id':global_id,'pickup_id':global_id+1,'equipped_id':index,'slot':slot,'address':hex(address),'fields':values,'raw_fields':raw,'flags':{flag:flags_view(flag,raw[flag])},'attack_type':SPEC['attack_types'].get(str(raw.get('attack_type'))),'identity_matches':raw['item_id']==global_id}

def catalog(rom,table=None,query=None):
    tables=[table] if table else list(SPEC['tables'])
    if any(t not in SPEC['tables'] for t in tables):raise PatchError('Unknown equipment table')
    rows=[describe_equipment(rom,t,i) for t in tables for i in range(SPEC['tables'][t]['count'])]
    return [r for r in rows if not query or query.casefold() in r['name'].casefold() or query.casefold() in r['key']]

def resolve(rom,table,item=None,index=None):
    if (item is None)==(index is None):raise PatchError('Specify exactly one equipment item key/name or index')
    if index is not None:return describe_equipment(rom,table,index)
    if not isinstance(item,str):raise PatchError('Equipment item must be a name or key')
    matches=[r for r in catalog(rom,table) if item.casefold() in (r['key'].casefold(),r['name'].casefold())]
    if len(matches)!=1:raise PatchError('Equipment name/key must match exactly one record')
    return matches[0]

def apply_equipment_edits(rom,edits):
    """Validate the entire batch before writing; shared ledger still rejects conflicts."""
    pending=[];claimed=set()
    for edit in edits:
        if set(edit)-{'table','item','index','expect','fields','flags'}:raise PatchError('Unknown equipment edit properties')
        row=resolve(rom,edit['table'],edit.get('item'),edit.get('index'))
        if not row['identity_matches']:raise PatchError('Equipment identity field was changed by another edit')
        fields=edit.get('fields',{});flag_edits=edit.get('flags',{});expect=edit.get('expect',{})
        if not fields and not flag_edits:raise PatchError('Equipment edit is empty')
        if set(fields)-set(SPEC['editable_fields']):raise PatchError('Equipment field is not in the safe editable set')
        allowed_flag='effects' if row['table']=='weapons' else 'resistances'
        if set(flag_edits)-{allowed_flag}:raise PatchError('Wrong flag field for equipment table')
        changed=set(fields)|set(flag_edits)
        if not changed<=set(expect):raise PatchError('expect must cover every changed field, including flag words')
        for field,value in expect.items():
            if field not in row['fields'] or number(value)!=row['fields'][field]:raise PatchError('Equipment precondition mismatch: '+field)
        values={}
        for field,value in fields.items():
            value=number(value);size=layout(row['table'],row['index'])[0]['fields'][field]['size']
            low,high=(-128,127) if field in SPEC['signed_fields'] else (0,(1<<(size*8))-1)
            if not low<=value<=high:raise PatchError('Equipment field out of semantic range: '+field)
            values[field]=value&((1<<(size*8))-1)
        for field,update in flag_edits.items():
            if set(update)-{'add','remove'} or not update:raise PatchError('Flag edit needs add/remove lists')
            add,remove=update.get('add',[]),update.get('remove',[])
            if not isinstance(add,list) or not isinstance(remove,list) or any(not isinstance(n,str) for n in add+remove):raise PatchError('Flag names must be lists of strings')
            if set(add)&set(remove) or len(set(add))!=len(add) or len(set(remove))!=len(remove):raise PatchError('Duplicate or contradictory flag operations')
            names=SPEC['flags'][field]
            if set(add+remove)-set(names):raise PatchError('Unknown flag name; unknown bits cannot be edited here')
            value=row['raw_fields'][field]
            for name in add:value|=1<<names[name]
            for name in remove:value&=~(1<<names[name])
            values[field]=value
        for field in values:
            claim=(row['table'],row['index'],field)
            if claim in claimed:raise PatchError('Repeated equipment field edit')
            claimed.add(claim)
        pending.append((row,values))
    reports=[]
    for row,values in pending:
        edit_record(rom,row['table'],row['index'],values)
        after=describe_equipment(rom,row['table'],row['index'])
        reports.append({'table':row['table'],'index':row['index'],'key':row['key'],'before':{k:row['fields'][k] for k in values},'after':{k:after['fields'][k] for k in values},'flags':after['flags']})
    return reports
