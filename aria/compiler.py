"""Optional original callback compilation. Player builds use verified binaries.

Zig is development-only. Metadata detects edits to C/linker/binary so code
changes cannot silently run an old callback. It is not a compiler authenticity
or signing system. Declared local dependencies are tracked; arbitrary undeclared
includes still require explicit dependency declarations.
"""
import hashlib,json,subprocess
from pathlib import Path
from .core import PatchError
ROOT=Path(__file__).resolve().parents[1]

def ensure_callback(folder, spec, compile_requested=False):
    if "source" not in spec:
        if compile_requested:raise PatchError("--compile requires frame_hook source and linker")
        return
    names=[spec["source"],spec["linker"],spec["file"]]+spec.get("dependencies",[])
    if len(set(names))!=len(names):raise PatchError("Duplicate callback dependency/output path")
    paths=[(folder/name).resolve() for name in names]
    metadata=(folder/spec.get("fingerprint","runtime.build.json")).resolve()
    if any(not p.is_relative_to(folder.resolve()) for p in paths+[metadata]):
        raise PatchError("Callback source/output paths must remain in the manifest folder")
    if compile_requested:
        zig=ROOT/"tools/zig/zig-x86_64-windows-0.15.2/zig.exe"
        if not zig.is_file():raise PatchError("Install Zig 0.15.2 at the documented tools path to compile")
        build=ROOT/"build/compiler";build.mkdir(parents=True,exist_ok=True)
        elf=build/(hashlib.sha256(str(folder).encode()).hexdigest()[:12]+".elf")
        subprocess.run([str(zig),"cc","-target","thumb-freestanding-eabi","-mcpu=arm7tdmi","-mthumb","-Os","-ffreestanding","-fno-builtin","-fno-stack-protector","-nostdlib","-Wl,-T,"+str(paths[1]),"-Wl,-e,tick",str(paths[0]),"-o",str(elf)],check=True,cwd=ROOT)
        subprocess.run([str(zig),"objcopy","-O","binary",str(elf),str(paths[2])],check=True,cwd=ROOT)
        metadata.write_text(json.dumps({name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in zip(names,paths)},indent=2))
    if not metadata.is_file():raise PatchError("Missing callback build fingerprint; run with --compile")
    recorded=json.loads(metadata.read_text())
    for name,path in zip(names,paths):
        if not path.is_file() or recorded.get(name)!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise PatchError("Callback source/linker/binary changed; run build/play with --compile")
