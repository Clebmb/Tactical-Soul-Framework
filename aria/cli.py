"""CLI for host-only builds, inspection and launching; standard library only."""
import argparse, copy, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from .core import RomImage, PatchError, number
from .sprites import SPRITES, inspect_sprite
from .sprite_rendering import preview_sprite
from .sprite_assets import install_sprite_assets, source_path as sprite_source_path
from .tables import read_record, edit_record, LAYOUTS
from .hooks import install_frame_hook
from .compiler import ensure_callback
from .level import apply_level_edits,audit_room
from .equipment import catalog,resolve,apply_equipment_edits
from .enemies import catalog as enemy_catalog,resolve as resolve_enemy,apply_enemy_edits
from .labels import apply_label_edits
from .encounters import audit_encounters
from .abilities import install_abilities
from .content import install_content
from .resources import catalog as resource_catalog, export_resource, apply_resource_edits, diff_resource
from .geometry import inspect_geometry,verify_roundtrip,apply_geometry_edits
from .rendering import render_layer,png_rgba
from .room_catalog import catalog_rooms
from .room_assets import install_room_assets
from .room_resources import audit_room_resources
from .rooms import Entity, Door, room_address, replace_entities, replace_doors, describe
ROOT = Path(__file__).resolve().parents[1]

def load_image(host):
    profile = json.loads((ROOT/"framework/aos-usa-r0.json").read_text())
    return RomImage(Path(host).read_bytes(), profile)

def local_file(folder, name):
    path = (folder/name).resolve()
    if not path.is_relative_to(folder.resolve()):
        raise PatchError("Payload paths must remain within the mod manifest folder")
    return path

def apply_manifest(rom, path, compile_requested=False):
    path=Path(path).resolve()
    mod=json.loads(path.read_text(encoding='utf-8'))
    if isinstance(mod,dict) and mod.get('kind')=='tsf-project':
        from .projects import compose_project
        bundle=compose_project(path);staged=copy.deepcopy(rom)
        result=apply_manifest_data(staged,bundle['manifest'],path.parent,compile_requested)
        staged.project_report=bundle['report']
        # Commit only after all domain writers and ledger checks succeed.
        rom.__dict__.clear();rom.__dict__.update(staged.__dict__)
        return result
    return apply_manifest_data(rom,mod,path.parent,compile_requested)


def apply_manifest_data(rom,mod,folder,compile_requested=False):
    """Apply an ordinary manifest using an explicit confined payload folder."""
    allowed = {"schema_version", "id", "description", "table_edits", "patches", "blobs", "entity_lists", "door_lists", "frame_hook", "room_edits", "equipment_edits", "enemy_edits", "enemy_encounters", "abilities", "content", "resource_edits", "geometry_edits", "room_assets", "sprite_assets", "label_edits"}
    if set(mod)-allowed:
        raise PatchError("Unknown mod properties: "+", ".join(sorted(set(mod)-allowed)))
    if mod.get("schema_version") != 1 or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", mod.get("id", "")):
        raise PatchError("Require schema_version 1 and a safe lowercase mod id")
    if ("room_edits" in mod or "enemy_encounters" in mod) and any(mod.get(k) for k in ("patches","entity_lists","door_lists")):
        raise PatchError("room_edits/enemy_encounters cannot combine with raw patches or full entity/door lists")
    if "room_assets" in mod and mod.get("patches"):raise PatchError("Room assets cannot combine with raw patches")
    if "geometry_edits" in mod and mod.get("patches"):raise PatchError("Geometry edits cannot combine with raw patches")
    if 'sprite_assets' in mod and mod.get('patches'):raise PatchError('Sprite assets cannot combine with raw patches')
    if "abilities" in mod and "frame_hook" in mod:raise PatchError("abilities owns the frame hook; use its dispatcher for combined features")
    if "abilities" in mod:
        rom.ability_report=install_abilities(rom,mod["abilities"],folder,compile_requested)
    if "frame_hook" in mod:
        hook=mod["frame_hook"]
        ensure_callback(folder,hook,compile_requested)
        if ("file" in hook)==("hex" in hook):
            raise PatchError("Frame hook requires exactly one of file/hex")
        payload=local_file(folder,hook["file"]).read_bytes() if "file" in hook else bytes.fromhex(hook["hex"])
        install_frame_hook(rom,payload,hook["linked_address"])
    if "content" in mod:
        rom.content_report=install_content(rom,mod["content"],folder)
    if "resource_edits" in mod:
        rom.resource_report=apply_resource_edits(rom,mod["resource_edits"])
    if "sprite_assets" in mod:
        rom.sprite_asset_report=install_sprite_assets(rom,mod['sprite_assets'],folder)
    for blob in mod.get("blobs", []):
        if ("hex" in blob) == ("file" in blob):
            raise PatchError("Each blob requires exactly one of hex/file")
        payload = bytes.fromhex(blob["hex"]) if "hex" in blob else local_file(folder, blob["file"]).read_bytes()
        rom.allocate(blob["id"], payload, number(blob.get("alignment", 4)))
    for edit in mod.get("table_edits", []):
        edit_record(rom, edit["table"], edit["index"], edit["fields"])
    if "enemy_edits" in mod:
        rom.enemy_report=apply_enemy_edits(rom,mod["enemy_edits"])
    if "equipment_edits" in mod:
        rom.equipment_report=apply_equipment_edits(rom,mod["equipment_edits"])
    if "label_edits" in mod:
        rom.label_report=apply_label_edits(rom,mod["label_edits"])
    for entry in mod.get("entity_lists", []):
        sector,index = number(entry["sector"]),number(entry["room"])
        rows = [Entity(**{k:number(v) for k,v in row.items()}) for row in entry["entities"]]
        replace_entities(rom, room_address(rom,sector,index), rows, f"room-{sector}-{index}")
    for entry in mod.get("door_lists", []):
        sector,index = number(entry["sector"]),number(entry["room"])
        rows = [Door(**{k:number(v) for k,v in row.items()}) for row in entry["doors"]]
        replace_doors(rom, room_address(rom,sector,index), rows, f"room-{sector}-{index}")
    if "room_edits" in mod or "enemy_encounters" in mod:
        rom.level_report=apply_level_edits(rom,mod.get("room_edits",{}),mod.get("enemy_encounters",[]))
    if "room_assets" in mod:
        rom.room_asset_report=install_room_assets(rom,mod["room_assets"],folder)
    if "geometry_edits" in mod:
        rom.geometry_report=apply_geometry_edits(rom,mod["geometry_edits"])
    for i, patch in enumerate(mod.get("patches", [])):
        if ("hex" in patch) == ("pointer_to" in patch):
            raise PatchError("Each patch requires exactly one of hex/pointer_to")
        if "expected" not in patch:
            raise PatchError("Raw patches require explicit expected original bytes")
        expected = bytes.fromhex(patch["expected"])
        if "pointer_to" in patch:
            if patch["pointer_to"] not in rom.allocations:
                raise PatchError("Unknown allocated pointer target")
            target = rom.allocations[patch["pointer_to"]]+number(patch.get("addend",0))
            if patch.get("thumb",False):
                target |= 1
            payload = target.to_bytes(4,"little")
        else:
            payload = bytes.fromhex(patch["hex"])
        if len(expected) != len(payload):
            raise PatchError("Expected and replacement lengths must match")
        rom.write(patch["address"], payload, patch.get("label", f"raw-patch-{i}"), expected)
    return mod

def find_emulator(explicit=None):
    candidates = [Path(explicit)] if explicit else [
        ROOT/"runtime/emulator/mGBA.exe", ROOT/"tools/mGBA-0.10.5-win64/mGBA.exe"]
    for path in candidates:
        if path.is_file():return path.resolve()
    raise PatchError("mGBA not found; use --emulator or install the bundled runtime layout")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Tactical Soul Framework: verified original -> separate mod ROM")
    sub = parser.add_subparsers(dest="command",required=True)
    sprite=sub.add_parser('inspect-sprite',help='Read registered sprite frames, hitboxes and animation records')
    sprite.add_argument('sprite',choices=sorted(SPRITES))
    sprite.add_argument('--mod',type=Path)
    sprite.add_argument('--host',type=Path,default=Path(os.environ.get('TSF_HOST_ROM',os.environ.get('ARIA_HOST_ROM',str(ROOT/'CastlevaniaAoS.gba')))))
    sprite_preview=sub.add_parser('preview-sprite',help='Render one registered static sprite frame to a private PNG')
    sprite_preview.add_argument('sprite',choices=sorted(SPRITES))
    sprite_preview.add_argument('--frame',type=lambda s:int(s,0),default=0)
    sprite_preview.add_argument('--mod',type=Path)
    sprite_preview.add_argument('--palette-bank',type=lambda s:int(s,0))
    sprite_preview.add_argument('--out',type=Path,required=True)
    sprite_preview.add_argument('--host',type=Path,default=Path(os.environ.get('TSF_HOST_ROM',os.environ.get('ARIA_HOST_ROM',str(ROOT/'CastlevaniaAoS.gba')))))
    project=sub.add_parser("plan-project",help="Compose and stage a project without writing a ROM")
    project.add_argument("project",type=Path)
    project.add_argument("--host",type=Path,default=ROOT/"CastlevaniaAoS.gba")
    project.add_argument("--out",type=Path)
    for name in ("build","play"):
        command=sub.add_parser(name)
        command.add_argument("mod",type=Path)
        command.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
        command.add_argument("--out",type=Path)
        command.add_argument("--compile",action="store_true",help="Recompile declared native callback with local Zig")
        if name=="play":command.add_argument("--emulator",type=Path)
    for name in ("audit-room","export-room"):
        command=sub.add_parser(name)
        command.add_argument("sector",type=lambda s:int(s,0))
        command.add_argument("index",type=lambda s:int(s,0))
        command.add_argument("--host",type=Path,default=ROOT/"CastlevaniaAoS.gba")
        command.add_argument("--mod",type=Path,help="Apply manifest in memory before inspecting")
        if name=="export-room":command.add_argument("--out",type=Path,required=True)
    equipment=sub.add_parser("equipment",help="Named weapon/body/accessory catalog and signed fields")
    equipment.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    equipment.add_argument("--table",choices=("weapons","armor"))
    equipment.add_argument("--item")
    equipment.add_argument("--index",type=lambda s:int(s,0))
    equipment.add_argument("--query")
    equipment.add_argument("--mod",type=Path)
    equipment.add_argument("--out",type=Path,help="Export local catalog JSON")
    enemies=sub.add_parser("enemies",help="Named enemy catalog, stats and drops")
    enemies.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    enemies.add_argument("--enemy")
    enemies.add_argument("--index",type=lambda s:int(s,0))
    enemies.add_argument("--query")
    enemies.add_argument("--mod",type=Path)
    enemies.add_argument("--out",type=Path)
    encounters=sub.add_parser("encounters",help="Audit native enemy placements and resource evidence")
    encounters.add_argument("sector",type=lambda s:int(s,0))
    encounters.add_argument("index",type=lambda s:int(s,0))
    encounters.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    encounters.add_argument("--mod",type=Path)
    for name in ("content-catalog","export-content","diff-content"):
        command=sub.add_parser(name)
        command.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
        if name!="diff-content":command.add_argument("--mod",type=Path)
        if name in ("export-content","diff-content"):
            command.add_argument("resource")
            command.add_argument("--out",type=Path,required=True)
        if name=="diff-content":
            command.add_argument("--source",type=Path,required=True)
            command.add_argument("--provenance",required=True)
            command.add_argument("--id",required=True)
    for name in ("inspect-geometry","export-geometry","inspect-background","export-background","preview-background","preview-room","audit-resources"):
        command=sub.add_parser(name)
        command.add_argument("sector",type=lambda s:int(s,0));command.add_argument("index",type=lambda s:int(s,0))
        if name!="audit-resources":command.add_argument("--layer",type=int,default=0)
        command.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
        command.add_argument("--mod",type=Path)
        if name=="audit-resources":
            command.add_argument("--include-consumers",action="store_true")
            command.add_argument("--out",type=Path)
        if name in ("export-geometry","export-background","preview-background","preview-room"):command.add_argument("--out",type=Path,required=True)
    plan=sub.add_parser("plan-connections",help="Stage checked door proposals without emitting a ROM")
    plan.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba"))))
    plan.add_argument("--mod",type=Path);plan.add_argument("--spec",type=Path,required=True);plan.add_argument("--out",type=Path)
    terrain=sub.add_parser("plan-terrain",help="Stage rectangle paints as checked geometry edits without emitting a ROM")
    terrain.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba"))))
    terrain.add_argument("--mod",type=Path);terrain.add_argument("--spec",type=Path,required=True);terrain.add_argument("--out",type=Path)
    graph=sub.add_parser("world-graph",help="Static base-room door graph and mod routing delta")
    graph.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    graph.add_argument("--mod",type=Path);graph.add_argument("--out",type=Path)
    states=sub.add_parser("room-states",help="Read-only bounded alternate-state chain and resource loads")
    states.add_argument("sector",type=lambda s:int(s,0));states.add_argument("index",type=lambda s:int(s,0))
    states.add_argument("--max-states",type=int,default=32)
    states.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    states.add_argument("--mod",type=Path);states.add_argument("--out",type=Path)
    support=sub.add_parser("terrain-support",help="Read-only paginated terrain candidates and brush dependency diagnostics")
    support.add_argument("--host",type=Path,default=ROOT/"CastlevaniaAoS.gba")
    support.add_argument("--mod",type=Path);support.add_argument("--sector",type=lambda s:int(s,0))
    support.add_argument("--offset",type=int,default=0);support.add_argument("--limit",type=int,default=32);support.add_argument("--out",type=Path)
    rooms=sub.add_parser("room-catalog",help="Paginated base-state rooms with independent layer diagnostics")
    rooms.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    rooms.add_argument("--mod",type=Path)
    rooms.add_argument("--sector",type=lambda s:int(s,0))
    rooms.add_argument("--offset",type=int,default=0)
    rooms.add_argument("--limit",type=int,default=32)
    rooms.add_argument("--check-rendering",action="store_true")
    rooms.add_argument("--out",type=Path)
    inspect=sub.add_parser("inspect")
    inspect.add_argument("--host",type=Path,default=Path(os.environ.get("TSF_HOST_ROM",os.environ.get("ARIA_HOST_ROM",str(ROOT/"CastlevaniaAoS.gba")))))
    inspect.add_argument("--mod",type=Path)
    inspect.add_argument("--table",choices=sorted(LAYOUTS))
    inspect.add_argument("--index",type=lambda s:int(s,0),default=0)
    inspect.add_argument("--room",nargs=2,type=lambda s:int(s,0),metavar=("SECTOR","INDEX"))
    try:
        args=parser.parse_args(argv)
        rom=load_image(args.host)
        sprite_inputs=[]
        if args.command in ('inspect-sprite','preview-sprite') and args.mod:
            preview_mod=apply_manifest(rom,args.mod)
            sprite_inputs=[args.mod.resolve()]
            def collect_preview_inputs(value):
                if isinstance(value,dict):
                    for key,item in value.items():
                        if key in ('source','file','graphics_source','palette_source','runtime_source') and isinstance(item,str):
                            sprite_inputs.append((args.mod.resolve().parent/item).resolve())
                        collect_preview_inputs(item)
                elif isinstance(value,list):
                    for item in value:collect_preview_inputs(item)
            collect_preview_inputs(preview_mod)
            if hasattr(rom,'project_report'):
                sprite_inputs.extend((args.mod.resolve().parent/item['path']).resolve()
                    for item in rom.project_report['modules']+rom.project_report['assets'])
        if args.command=='preview-sprite':
            output=args.out.resolve()
            if output.suffix.lower()!='.png' or not output.is_relative_to((ROOT/'local').resolve()) or output==args.host.resolve():
                raise PatchError('Sprite previews require a private .png under local/ and must preserve the host')
            if output in sprite_inputs:raise PatchError('Sprite preview would overwrite a manifest/module/source input')
            result=preview_sprite(rom,args.sprite,args.frame,args.palette_bank)
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_bytes(png_rgba(result['width'],result['height'],result['pixels']))
            print(json.dumps(result['report'],indent=2))
            return 0
        if args.command=='inspect-sprite':
            print(json.dumps(inspect_sprite(rom,SPRITES[args.sprite]),indent=2))
            return 0
        if args.command in ("inspect","audit-room","export-room","equipment","enemies","encounters","content-catalog","export-content","inspect-geometry","export-geometry","preview-room","room-catalog","audit-resources","inspect-background","export-background","preview-background","room-states") and args.mod:
            apply_manifest(rom,args.mod)
        if args.command=="plan-project":
            if args.out:
                inputs=[args.host,args.project]
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private project plans require a .json under local/ and must preserve inputs')
            # Require an actual project; ordinary manifests retain existing APIs.
            document=json.loads(args.project.read_text(encoding='utf-8'))
            if not isinstance(document,dict) or document.get('kind')!='tsf-project':raise PatchError('plan-project requires kind tsf-project')
            staged=copy.deepcopy(rom);mod=apply_manifest(staged,args.project)
            result={'schema_version':1,'status':'staged_not_gameplay_certified','input_sha256':hashlib.sha256(rom.data).hexdigest(),
                    'proposed_image_sha256':hashlib.sha256(staged.data).hexdigest(),'project':staged.project_report,
                    'patch_count':len(staged.ledger),'allocations':staged.allocations}
            encoded=json.dumps(result,indent=2)
            if args.out:
                # Preserve every source input, including modules/assets under local/.
                root=args.project.resolve().parent
                sources=[root/item['path'] for item in result['project']['modules']+result['project']['assets']]
                if args.out.resolve() in [p.resolve() for p in sources]:raise PatchError('Project plan would overwrite a source input')
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded,encoding='utf-8');print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="terrain-support":
            from .terrain_support import catalog_terrain_support
            if args.out:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private terrain support reports require a .json under local/ and must preserve inputs')
            if args.mod:apply_manifest(rom,args.mod)
            result=catalog_terrain_support(rom,args.sector,args.offset,args.limit)
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded,encoding='utf-8');print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command in ("plan-connections","plan-terrain"):
            from .connection_plans import plan_connections
            from .terrain_plans import plan_terrain
            if args.out:
                inputs=[args.host,args.spec]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private plans require a .json under local/ and must preserve inputs')
            if args.mod:apply_manifest(rom,args.mod)
            planner=plan_connections if args.command=="plan-connections" else plan_terrain
            result=planner(rom,json.loads(args.spec.read_text(encoding='utf-8')))
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded,encoding='utf-8');print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="world-graph":
            from .world_graph import audit_world_graph,compare_world_graphs
            if args.out:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private world graphs require a .json under local/ and must preserve inputs')
            baseline=audit_world_graph(rom)
            if args.mod:
                apply_manifest(rom,args.mod)
                current=audit_world_graph(rom)
                result={'schema_version':1,'graph':current,'changes':compare_world_graphs(baseline,current)}
            else:result={'schema_version':1,'graph':baseline,'changes':None}
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded);print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="room-states":
            from .room_states import inspect_room_states
            if args.out:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private state reports require a .json under local/ and must preserve inputs')
            result=inspect_room_states(rom,args.sector,args.index,args.max_states)
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded);print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="preview-background":
            from .backgrounds import render_background
            outputs=[args.out,args.out.with_suffix('.json')]
            inputs=[args.host]+([args.mod] if args.mod else [])
            if args.out.suffix.lower()!='.png' or any(p.resolve() in [x.resolve() for x in inputs] or not p.resolve().is_relative_to((ROOT/'local').resolve()) for p in outputs):
                raise PatchError('Private background previews require a .png under local/ and must preserve inputs')
            result=render_background(rom,args.sector,args.index,args.layer)
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_bytes(png_rgba(result['width'],result['height'],result['rgba']))
            outputs[1].write_text(json.dumps(result['report'],indent=2))
            print(json.dumps({'image':str(args.out.resolve()),'report':str(outputs[1].resolve())},indent=2));return 0
        if args.command in ("inspect-background","export-background"):
            from .backgrounds import inspect_background,verify_background_roundtrip
            full=args.command=="export-background"
            if full:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Private background exports require a .json under local/ and must preserve inputs')
            result=inspect_background(rom,args.sector,args.index,args.layer,full=full)
            if full:
                verify_background_roundtrip(result)
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2));print(str(args.out.resolve()))
            else:print(json.dumps(result,indent=2))
            return 0
        if args.command=="audit-resources":
            if args.out:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Resource audits require a .json under local/ and must preserve inputs')
            result=audit_room_resources(rom,args.sector,args.index,args.include_consumers)
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded);print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="room-catalog":
            if args.out:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.suffix.lower()!='.json' or args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/'local').resolve()):
                    raise PatchError('Room catalogs require a .json under local/ and must preserve inputs')
            result=catalog_rooms(rom,args.sector,args.offset,args.limit,args.check_rendering)
            encoded=json.dumps(result,indent=2)
            if args.out:
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded);print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="preview-room":
            outputs=[args.out,args.out.with_suffix('.atlas.png'),args.out.with_suffix('.json')]
            inputs=[args.host]+([args.mod] if args.mod else [])
            resolved=[p.resolve() for p in outputs]
            if args.out.suffix.lower()!='.png' or len(set(resolved))!=3 or any(p in [x.resolve() for x in inputs] or not p.is_relative_to((ROOT/'local').resolve()) for p in resolved):
                raise PatchError('Private room previews require a .png under local/ and must preserve inputs')
            result=render_layer(rom,args.sector,args.index,args.layer)
            image=png_rgba(result['width'],result['height'],result['rgba'])
            atlas=png_rgba(result['atlas_width'],result['atlas_height'],result['atlas_rgba'])
            outputs[0].parent.mkdir(parents=True,exist_ok=True)
            outputs[0].write_bytes(image);outputs[1].write_bytes(atlas)
            outputs[2].write_text(json.dumps(result['report'],indent=2))
            print(json.dumps({'image':str(resolved[0]),'atlas':str(resolved[1]),'report':str(resolved[2])},indent=2));return 0
        if args.command in ("inspect-geometry","export-geometry"):
            full=args.command=="export-geometry"
            result=inspect_geometry(rom,args.sector,args.index,args.layer,full=full)
            if full:
                inputs=[args.host]+([args.mod] if args.mod else [])
                if args.out.resolve() in [p.resolve() for p in inputs] or not args.out.resolve().is_relative_to((ROOT/"local").resolve()):raise PatchError("Private geometry exports must stay under local/ and preserve inputs")
                verify_roundtrip(result)
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2));print(str(args.out.resolve()))
            else:print(json.dumps(result,indent=2))
            return 0
        if args.command=="content-catalog":
            print(json.dumps(resource_catalog(rom),indent=2));return 0
        if args.command in ("export-content","diff-content"):
            inputs=[args.host]+([args.mod] if getattr(args,"mod",None) else [])
            if args.out.resolve() in [p.resolve() for p in inputs]:raise PatchError("Content output must not overwrite host or manifest")
            if not args.out.resolve().is_relative_to((ROOT/"local").resolve()):raise PatchError("Native content exports/diffs must stay under local/; they can contain private game artwork")
            if args.command=="diff-content":
                if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}",args.id):raise PatchError("Diff requires a safe lowercase mod id")
                if args.out.resolve()==args.source.resolve():raise PatchError("Diff output must not overwrite authored source")
                result={"schema_version":1,"id":args.id,"resource_edits":[diff_resource(rom,args.resource,json.loads(args.source.read_text()),args.provenance)]}
            else:result=export_resource(rom,args.resource)
            args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result))
            print(str(args.out.resolve()));return 0
        if args.command=="encounters":
            result=audit_encounters(rom,args.sector,args.index)
            print(json.dumps(result,indent=2));return int(bool(result['errors']))
        if args.command=="enemies":
            if args.enemy is not None or args.index is not None:
                if args.query:raise PatchError("Choose enemy lookup or query")
                result=resolve_enemy(rom,args.enemy,args.index)
            else:result=enemy_catalog(rom,args.query)
            encoded=json.dumps(result,indent=2)
            if args.out:
                if args.out.resolve()==args.host.resolve():raise PatchError("Export must not overwrite original")
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded)
                print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="equipment":
            if args.item is not None or args.index is not None:
                if not args.table:raise PatchError("Equipment lookup requires --table")
                if args.query:raise PatchError("Choose lookup or query")
                result=resolve(rom,args.table,args.item,args.index)
            else:result=catalog(rom,args.table,args.query)
            encoded=json.dumps(result,indent=2)
            if args.out:
                if args.out.resolve()==args.host.resolve():raise PatchError("Export must not overwrite original")
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(encoded)
                print(str(args.out.resolve()))
            else:print(encoded)
            return 0
        if args.command=="audit-room":
            result=audit_room(rom,args.sector,args.index)
            print(json.dumps(result,indent=2));return int(bool(result["errors"]))
        if args.command=="export-room":
            if args.out.resolve()==args.host.resolve():raise PatchError("Export must not overwrite original")
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(json.dumps(describe(rom,args.sector,args.index),indent=2))
            print(str(args.out.resolve()));return 0
        if args.command=="inspect":
            if args.table and args.room:raise PatchError("Choose table inspection or room inspection")
            result=read_record(rom,args.table,args.index) if args.table else describe(rom,*args.room) if args.room else {"profile":rom.profile,"native_tables":list(LAYOUTS)}
            if not args.table and not args.room and hasattr(rom,"ability_report"):result["abilities"]=rom.ability_report
            if hasattr(rom,"content_report"):result["content"]=rom.content_report
            if hasattr(rom,"resource_report"):result["resource_edits"]=rom.resource_report
            if hasattr(rom,"geometry_report"):result["geometry_edits"]=rom.geometry_report
            if hasattr(rom,"room_asset_report"):result["room_assets"]=rom.room_asset_report
            if hasattr(rom,'sprite_asset_report'):result['sprite_assets']=rom.sprite_asset_report
            print(json.dumps(result,indent=2));return 0
        mod=apply_manifest(rom,args.mod,args.compile)
        out=args.out or ROOT/"build/mods"/mod["id"]/(mod["id"]+".gba")
        if hasattr(rom,"project_report"):
            root=args.mod.resolve().parent
            inputs=[args.host.resolve(),args.mod.resolve()]+[(root/item['path']).resolve() for item in rom.project_report['modules']+rom.project_report['assets']]
            if out.resolve() in inputs or out.with_suffix('.manifest.json').resolve() in inputs:raise PatchError('Project output/report would overwrite a source input')
        if hasattr(rom,'sprite_asset_report'):
            inputs=[args.mod.resolve()]
            for entry in mod.get('sprite_assets',[]):
                inputs.extend(sprite_source_path(args.mod.resolve().parent,entry[k]) for k in ('source','palette_source') if k in entry)
            if out.resolve() in inputs or out.with_suffix('.manifest.json').resolve() in inputs:
                raise PatchError('Sprite output/report would overwrite source inputs')
        report=rom.output(out,args.host)
        if hasattr(rom,"level_report"):report["room_audits"]=rom.level_report
        if hasattr(rom,"equipment_report"):report["equipment_edits"]=rom.equipment_report
        if hasattr(rom,"enemy_report"):report["enemy_edits"]=rom.enemy_report
        if hasattr(rom,"label_report"):report["label_edits"]=rom.label_report
        if hasattr(rom,"ability_report"):report["abilities"]=rom.ability_report
        if hasattr(rom,"content_report"):report["content"]=rom.content_report
        if hasattr(rom,"resource_report"):report["resource_edits"]=rom.resource_report
        if hasattr(rom,"geometry_report"):report["geometry_edits"]=rom.geometry_report
        if hasattr(rom,"room_asset_report"):report["room_assets"]=rom.room_asset_report
        if hasattr(rom,'sprite_asset_report'):report['sprite_assets']=rom.sprite_asset_report
        if hasattr(rom,"project_report"):report["project"]=rom.project_report
        report.update({"mod":mod["id"],"manifest_sha256":__import__("hashlib").sha256(args.mod.read_bytes()).hexdigest(),"output":str(out.resolve()),"status":"built_not_gameplay_certified"})
        report_path=out.with_suffix(".manifest.json")
        if report_path.resolve()==args.host.resolve():raise PatchError("Report path would overwrite original")
        report_path.write_text(json.dumps(report,indent=2))
        print(json.dumps({"mod":mod["id"],"output":str(out.resolve()),"sha256":report["output_sha256"],"patch_count":len(rom.ledger),"report":str(report_path.resolve())},indent=2))
        if args.command=="play":
            emulator=find_emulator(args.emulator)
            subprocess.Popen([str(emulator),str(out.resolve())],cwd=emulator.parent)
        return 0
    except (PatchError,OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as error:
        print("Aria build failed: "+str(error),file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
