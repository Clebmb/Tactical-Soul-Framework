"""Existing-room editing with map/save diagnostics; no geometry compiler.

Only sparse moves of existing non-script entities and paired existing doors are
supported. Native resources and entity identity are preserved. Static checks
cannot prove floor collision, event progression, or safe landing at a spawn.
"""
from dataclasses import replace
from .core import PatchError,number
from .rooms import room_address,metadata,dimensions,entities,doors,replace_entities,replace_doors
MAP=0x08116650
MAP_WIDTH,MAP_HEIGHT=64,47
MOVABLE={1,3,4,5,6}

def reference(rom,value):
    if set(value)!={"sector","room"}:raise PatchError("Room reference requires only sector and room")
    sector,index=number(value["sector"]),number(value["room"])
    return sector,index,room_address(rom,sector,index)

def audit_room(rom,sector,index):
    pointer=room_address(rom,sector,index)
    values=metadata(rom,pointer);width,height=dimensions(rom,pointer)
    map_x,map_y=(values[9]>>16)&127,(values[9]>>23)&127
    errors=[];warnings=[];tiles=[]
    if not width or not height:errors.append("zero main-layer dimensions")
    if map_x+width>MAP_WIDTH or map_y+height>MAP_HEIGHT:errors.append("room footprint extends outside castle map")
    else:
        for y in range(map_y,map_y+height):
            for x in range(map_x,map_x+width):
                value=rom.integer(MAP+(y*MAP_WIDTH+x)*2,2)
                owner=None if value==65535 else [(value>>6)&15,value&63]
                tiles.append({"x":x,"y":y,"owner":owner,"save":value!=65535 and bool(value&0x8000)})
        mismatches=[t for t in tiles if t["owner"]!=[sector,index]]
        if mismatches:warnings.append(f"{len(mismatches)} footprint tiles are blank or owned by another room; may be native overlap/special geometry")
    rows=entities(rom,pointer)
    if len({e.unique_id for e in rows})!=len(rows):errors.append("duplicate entity identity")
    save=any(e.type==2 and e.subtype==28 for e in rows)
    if save and not any(t["save"] and t["owner"]==[sector,index] for t in tiles):errors.append("save statue lacks an owned map save marker")
    links=[]
    for i,door in enumerate(doors(rom,pointer)):
        try:
            w,h=dimensions(rom,door.destination)
            if not 0<=door.dest_x<w*256 or not 0<=door.dest_y<h*256:errors.append(f"door {i}: destination spawn outside target dimensions")
            returns=any(d.destination==pointer for d in doors(rom,door.destination))
            if not returns:warnings.append(f"door {i}: target has no direct return door")
            links.append({"index":i,"destination":hex(door.destination),"direct_return":returns})
        except (PatchError,ValueError) as error:errors.append(f"door {i}: unreadable target: {error}")
    return {"sector":sector,"room":index,"address":hex(pointer),"dimensions":[width,height],"map_origin":[map_x,map_y],"save_room":save,"map_tiles":tiles,"doors":links,"errors":errors,"warnings":warnings,"scope":"static structural checks, not collision or gameplay certification"}

def side(door,width,height):
    if door.x==255 and 0<=door.y<height:return "left"
    if door.x==width and 0<=door.y<height:return "right"
    if door.y==255 and 0<=door.x<width:return "up"
    if door.y==height and 0<=door.x<width:return "down"
    raise PatchError("Door is not on a supported room boundary")

def apply_level_edits(rom,spec,enemy_encounters=()):
    if set(spec)-{"moves","connections"}:raise PatchError("Unknown room_edits properties")
    map_before=rom.read(MAP,MAP_WIDTH*MAP_HEIGHT*2)
    lines_before=rom.read(0x08117DD0,MAP_WIDTH*MAP_HEIGHT//2)
    changes={};touched={};before={}
    def room(ref):
        s,i,p=reference(rom,ref);key=(s,i)
        if key not in touched:
            touched[key]=p;before[key]=audit_room(rom,s,i)
            changes[key]={"entities":None,"doors":None}
        return key,p
    for move in spec.get("moves",[]):
        if set(move)!={"room","entity_id","from","to"}:raise PatchError("Move requires room, entity_id, from, to")
        key,p=room(move["room"])
        if changes[key]["entities"] is None:changes[key]["entities"]=entities(rom,p)
        rows=changes[key]["entities"];identity=number(move["entity_id"])
        matches=[j for j,e in enumerate(rows) if e.unique_id==identity]
        if len(matches)!=1:raise PatchError("Move requires one existing entity with that ID")
        j=matches[0];entity=rows[j]
        if entity.type not in MOVABLE:raise PatchError("Script/save/warp/special entities cannot be moved by this API")
        old=[number(v) for v in move["from"]];new=[number(v) for v in move["to"]]
        if old!=[entity.x,entity.y]:raise PatchError("Entity coordinate precondition mismatch")
        w,h=dimensions(rom,p)
        if len(new)!=2 or not 0<=new[0]<w*256 or not 0<=new[1]<h*256:raise PatchError("Entity position outside native room dimensions")
        rows[j]=replace(entity,x=new[0],y=new[1])
    # Share staged arrays with room moves: one relocation per touched room.
    from .encounters import plan_encounter,audit_encounters
    encounter_changes={}
    for edit in enemy_encounters:
        key,p=room(edit['room'])
        if changes[key]['entities'] is None:changes[key]['entities']=entities(rom,p)
        entry=plan_encounter(rom,p,changes[key]['entities'],edit)
        encounter_changes.setdefault(key,[]).append(entry)
    used=set()
    for connection in spec.get("connections",[]):
        if set(connection)!={"a","b"}:raise PatchError("Connection requires a and b endpoints")
        endpoints=[]
        for label in ("a","b"):
            end=connection[label]
            if set(end)!={"room","door","spawn"}:raise PatchError("Endpoint requires room, door, spawn")
            key,p=room(end["room"]);index=number(end["door"])
            if changes[key]["doors"] is None:changes[key]["doors"]=doors(rom,p)
            rows=changes[key]["doors"]
            if not 0<=index<len(rows):raise PatchError("Door index outside existing array")
            if (key,index) in used:raise PatchError("Door endpoint used more than once")
            used.add((key,index));spawn=[number(v) for v in end["spawn"]];w,h=dimensions(rom,p)
            if len(spawn)!=2 or not 0<=spawn[0]<w*256 or not 0<=spawn[1]<h*256:raise PatchError("Spawn outside endpoint room")
            endpoints.append((key,p,index,spawn,side(rows[index],w,h)))
        a,b=endpoints
        if a[1]==b[1]:raise PatchError("Self-room connections are not supported")
        if {"left":"right","right":"left","up":"down","down":"up"}[a[4]]!=b[4]:raise PatchError("Door sides must oppose")
        for source,target in ((a,b),(b,a)):
            key,p,index,spawn,direction=source
            old=changes[key]["doors"][index]
            changes[key]["doors"][index]=replace(old,destination=target[1],dest_x_2=0,dest_y_2=0,dest_x=target[3][0],dest_y=target[3][1])
    # Reject incompatible combinations with legacy full-list mutations through
    # the shared patch ledger. Metadata/map/geometry stay byte-identical.
    for key,change in changes.items():
        p=touched[key];label=f"level-{key[0]}-{key[1]}"
        if change["entities"] is not None:replace_entities(rom,p,change["entities"],label)
        if change["doors"] is not None:replace_doors(rom,p,change["doors"],label)
    if rom.read(MAP,MAP_WIDTH*MAP_HEIGHT*2)!=map_before or rom.read(0x08117DD0,MAP_WIDTH*MAP_HEIGHT//2)!=lines_before:
        raise PatchError("Existing-room edits unexpectedly changed castle map data")
    result=[]
    for key in touched:
        report=audit_room(rom,*key)
        new_errors=set(report["errors"])-set(before[key]["errors"])
        if new_errors:raise PatchError("New room audit errors: "+"; ".join(sorted(new_errors)))
        if key in encounter_changes:
            encounter_audit=audit_encounters(rom,*key)
            if encounter_audit['errors']:raise PatchError('Encounter audit errors: '+'; '.join(encounter_audit['errors']))
            report['encounter_changes']=encounter_changes[key]
            report['encounter_audit']=encounter_audit
        report["baseline_errors"]=before[key]["errors"]
        report["map_metadata_unchanged"]=True
        result.append(report)
    return result
