"""Allowlist Tactical Soul Framework source/examples/runtimes; never zip private working data."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/"release";RELEASE.mkdir(exist_ok=True)
files=[ROOT/name for name in ("README.md","AGENTS.md","handoffprompt.md","BUILD.md","LICENSE","TacticalSoul.cmd","Dominance.cmd","Framework.cmd","scripts/aria_tool.py","scripts/package_framework.py","scripts/emulator.py","scripts/verify_framework.py","scripts/verify_rooms.py","scripts/verify_equipment.py","scripts/verify_enemies.py","scripts/verify_abilities.py","scripts/verify_content.py","scripts/import_indexed_png.py","scripts/preview_content.py","scripts/verify_resources.py","scripts/verify_geometry.py","scripts/verify_rendering.py","scripts/verify_room_catalog.py","scripts/verify_room_resources.py","scripts/verify_backgrounds.py","scripts/verify_background_rendering.py","scripts/verify_room_states.py","scripts/verify_world_graph.py","scripts/verify_connection_plans.py","scripts/verify_connection_traversal.py","scripts/verify_room5_search.py","scripts/verify_bridge_route.py","scripts/update_inventory.py","scripts/update_handoff.py","scripts/verify_terrain_support.py","scripts/verify_projects.py","scripts/verify_sprites.py","scripts/verify_sprite_assets.py","runtime/hook.bin","runtime/entry.bin")]
for folder in ("aria","native","framework","examples","tests","docs","src","runtime/python"):
    files.extend(p for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
for name in ("mGBA.exe","LICENSE.txt","portable.ini","README.html","CHANGES.txt"):
    files.append(ROOT/"runtime/emulator"/name)
files.extend(p for p in (ROOT/"runtime/emulator/licenses").rglob("*") if p.is_file())
archive=RELEASE/"Tactical-Soul-Framework-0.37.0.zip"
handoff=(ROOT/'handoffprompt.md').read_text(encoding='utf-8')
version=json.loads((ROOT/'framework/capabilities.json').read_text())['version']
status=handoff.split('<!-- STATUS START -->',1)[1].split('<!-- STATUS END -->',1)[0]
if version not in status or 'Verification actually run' not in status:raise ValueError('Refresh handoffprompt.md for the current release before packaging')
entries=[]
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as package:
    for file in sorted(set(files)):
        relative=file.relative_to(ROOT).as_posix()
        if file.suffix.lower() in (".gba",".sav",".png",".bmp") or relative.startswith(("tools/","local/","build/")):
            raise ValueError("Private/unapproved file in allowlist: "+relative)
        package.write(file,"TacticalSoul/"+relative)
        entries.append({"path":"TacticalSoul/"+relative,"size":file.stat().st_size})
report={"fileName":archive.name,"size":archive.stat().st_size,"sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"entries":entries,"distribution":"Original code/docs and licensed runtimes only. No commercial ROMs, extracted assets, saves or dev tools."}
(RELEASE/"package-inventory.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!="entries"},indent=2))
