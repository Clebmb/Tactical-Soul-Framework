"""Checked fixed-layout artwork replacement for registered native sprite pages.

Each resource is deliberately scoped to its evidenced consumers: the
background-bats page is global to its users. New resources are registered
only with a tracer-named consumer set plus fully enumerated sharing
evidence (see docs/ENEMY-BINDING.md). This is not a room-specific import,
new actor allocator or animation writer.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path
from .core import PatchError
from .content import tiles, palette
from .compression import read_aria, rebuild_aria
from .sprite_rendering import resolve_sprite_resources

PAGE_SHA256='6f854783fd52be168b512c169451fa8b38ab96cbd8f3d788df7091706a8d3f3c'
PALETTE_SHA256='a7cc42d2dd4da92f764c24b7bd57d97718ada87709706cdfc33d4c3d8297df54'
WRAPPER=0x081CBE5C
PALETTE_DATA=0x08209EEC
SOURCE=0x085FBF20

REGISTRY={
    'background-bats': dict(page_sha=PAGE_SHA256,palette_sha=PALETTE_SHA256,
        wrapper=WRAPPER,wrapper_bytes='0104100420bf5f08',palette_data=PALETTE_DATA,
        compressed_source=SOURCE,encoding='aria-lz',width=128,height=32,
        scope='all_registered_consumers',
        literals=((0x0804F1A0,WRAPPER),(0x0804F540,WRAPPER),
                  (0x0804F1A4,0x08209EE8),(0x0804F544,0x08209EE8),
                  (0x0804F1A8,0x0820FE44),(0x0804F5B4,0x0820FE44))),
}

def source_path(folder,name):
    if not isinstance(name,str) or not name or Path(name).is_absolute():
        raise PatchError('Sprite sources must be relative JSON paths')
    path=(Path(folder)/name).resolve()
    if not path.is_relative_to(Path(folder).resolve()) or path.suffix.lower()!='.json':
        raise PatchError('Sprite sources must be JSON within the manifest folder')
    return path

def _json(path):
    if path.stat().st_size>512*1024:raise PatchError('Sprite source exceeds 512 KiB')
    return json.loads(path.read_text(encoding='utf-8'))

def install_sprite_assets(rom,entries,folder):
    """Stage the complete sprite batch; commit only after successful validation.

    Exactly one registered resource per manifest. LZ pages relocate a rebuilt
    stream (original stream bytes stay untouched; only the wrapper pointer
    changes). Raw pages are replaced in place at the identical size with an
    exact preimage. Palette replacement is in place for the same consumer set.
    Requires the resource's explicit scope, original hashes and provenance.
    """
    if not isinstance(entries,list) or len(entries)!=1:
        raise PatchError('sprite_assets requires exactly one registered replacement')
    entry=entries[0]
    required={'resource','scope','source','expected_page_sha256','provenance'}
    optional={'palette_source','expected_palette_sha256'}
    if not isinstance(entry,dict) or not required<=entry.keys() or entry.keys()-(required|optional):
        raise PatchError('Unknown/missing sprite asset properties')
    if entry['resource'] not in REGISTRY:raise PatchError('Unregistered sprite asset target')
    registration=REGISTRY[entry['resource']]
    if entry['scope']!=registration['scope']:
        raise PatchError('Sprite replacement requires %s scope' % registration['scope'])
    if entry['expected_page_sha256']!=registration['page_sha']:raise PatchError('Sprite expected page hash mismatch')
    if not isinstance(entry['provenance'],str) or not entry['provenance'].strip():
        raise PatchError('Sprite assets require provenance')
    if ('palette_source' in entry)!=('expected_palette_sha256' in entry):
        raise PatchError('Sprite palette source and expected hash must occur together')
    if 'palette_source' in entry and entry['expected_palette_sha256']!=registration['palette_sha']:
        raise PatchError('Sprite expected palette hash mismatch')
    source=source_path(folder,entry['source']);document=_json(source)
    if not isinstance(document,dict) or document.get('width')!=registration['width'] or document.get('height')!=registration['height']:
        raise PatchError('Registered sprite artwork must remain %dx%d' % (registration['width'],registration['height']))
    payload=tiles(document)
    palette_bytes=None
    if 'palette_source' in entry:
        colors=_json(source_path(folder,entry['palette_source']))
        if not isinstance(colors,list) or len(colors)!=16:raise PatchError('Sprite palette requires exactly 16 RGB colors')
        palette_bytes=palette(colors)
    staged=copy.deepcopy(rom)
    if staged.read(registration['wrapper'],len(bytes.fromhex(registration['wrapper_bytes'])))!=bytes.fromhex(registration['wrapper_bytes']):
        raise PatchError('Sprite graphics wrapper/pointer changed')
    # Exact literal bindings observed in this host. These checks establish static
    # registration integrity, not recovered function signatures or every caller.
    # Single-entry resources have no code literals: the indexed table holds the
    # only references, so wrapper/hash guards plus native evidence carry the proof.
    for address,value in registration['literals']:
        if staged.integer(address)!=value:raise PatchError('Registered sprite consumer literal changed')
    resources=resolve_sprite_resources(staged,entry['resource'])
    if hashlib.sha256(resources['pages'][0]).hexdigest()!=registration['page_sha']:
        raise PatchError('Registered current sprite page hash mismatch')
    if hashlib.sha256(staged.read(registration['palette_data'],32)).hexdigest()!=registration['palette_sha']:
        raise PatchError('Registered current sprite palette hash mismatch')
    page_address=registration['wrapper']+4
    if registration['encoding']=='aria-lz':
        resource=read_aria(staged,registration['compressed_source']);resource['data_hex']=payload.hex()
        compressed=rebuild_aria(resource,preserve=False)
        address=staged.allocate('sprite:%s:page' % entry['resource'],compressed,4)
        staged.write(page_address,struct.pack('<I',address),'sprite:%s:binding' % entry['resource'],
                     struct.pack('<I',registration['compressed_source']))
    elif registration['encoding']=='raw':
        page=resources['pages'][0]
        if len(payload)!=len(page):raise PatchError('Raw sprite page replacement must preserve size')
        staged.write(page_address,payload,'sprite:%s:page' % entry['resource'],page)
        compressed=payload;address=None
    else:raise PatchError('Unsupported sprite page encoding')
    if palette_bytes is not None:
        staged.write(registration['palette_data'],palette_bytes,'sprite:%s:palette' % entry['resource'],
                     rom.read(registration['palette_data'],32))
    report=[dict(resource=entry['resource'],scope=entry['scope'],provenance=entry['provenance'],
                 source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                 page_sha256=hashlib.sha256(payload).hexdigest(),compressed_bytes=len(compressed),
                 wrapper_address=registration['wrapper'],allocated_address=address,palette_replaced=palette_bytes is not None,
                 palette_sha256=hashlib.sha256(palette_bytes if palette_bytes is not None else staged.read(registration['palette_data'],32)).hexdigest(),
                 status='registered_art_replacement',
                 limitations=['Only evidenced consumers of this page/palette are affected','Existing frames/animation/AI unchanged','No new OBJ/VRAM ownership or actor slots'])]
    rom.__dict__.clear();rom.__dict__.update(staged.__dict__)
    return report
