"""Compile bounded rectangle paints into checked, existing-metatile edits.

This headless authoring primitive emits reviewable geometry edits and stages
them on a clone. It never writes an output ROM or changes the caller's image.
"""
import copy,hashlib
from .core import PatchError
from .content import integer
from .geometry import inspect_geometry,apply_geometry_edits

def plan_terrain(rom,spec):
    required={'schema_version','expected_image_sha256','room','layer','expected_layout_sha256','rectangles'}
    if not isinstance(spec,dict) or set(spec)!=required:raise PatchError('Invalid terrain plan fields')
    if type(spec['schema_version']) is not int or spec['schema_version']!=1:raise PatchError('Unsupported terrain plan schema')
    digest=hashlib.sha256(rom.data).hexdigest()
    if spec['expected_image_sha256']!=digest:raise PatchError('Terrain plan image preimage mismatch')
    ref=spec['room']
    if not isinstance(ref,dict) or set(ref)!={'sector','room'}:raise PatchError('Invalid terrain room reference')
    sector=integer(ref['sector'],0,11);index=integer(ref['room'],0,255);layer=integer(spec['layer'],0,2)
    bundle=inspect_geometry(rom,sector,index,layer,full=True)
    if bundle['layout_sha256']!=spec['expected_layout_sha256']:raise PatchError('Terrain plan layout preimage mismatch')
    rectangles=spec['rectangles']
    if not isinstance(rectangles,list) or not 1<=len(rectangles)<=64:raise PatchError('Terrain plan requires 1..64 rectangles')
    width,height=bundle['width_cells'],bundle['height_cells'];seen=set();cells=[]
    for rect in rectangles:
        if not isinstance(rect,dict) or set(rect)!={'x','y','width','height','value'}:raise PatchError('Invalid paint rectangle')
        x=integer(rect['x'],0,width-1);y=integer(rect['y'],0,height-1)
        w=integer(rect['width'],1,width);h=integer(rect['height'],1,height)
        value=integer(rect['value'],0,65535)
        if x+w>width or y+h>height:raise PatchError('Paint rectangle outside layout')
        if (value&0x3FFF)>=bundle['metatiles_including_blank']:raise PatchError('Paint references missing metatile')
        for cy in range(y,y+h):
            for cx in range(x,x+w):
                pos=cy*width+cx
                if pos in seen:raise PatchError('Paint rectangles overlap')
                seen.add(pos);old=bundle['cells'][pos]
                if old!=value:cells.append({'x':cx,'y':cy,'expect':old,'value':value})
    if not cells:raise PatchError('Terrain paint changes no cells')
    entry={'room':{'sector':sector,'room':index},'layer':layer,'expected_layout_sha256':bundle['layout_sha256'],'cells':cells}
    staged=copy.deepcopy(rom);report=apply_geometry_edits(staged,[entry])
    return {'schema_version':1,'status':'static_terrain_proposal','input_sha256':digest,
            'proposed_image_sha256':hashlib.sha256(staged.data).hexdigest(),'geometry_edit':entry,
            'painted_cells':len(seen),'changed_cells':len(cells),'room_reports':report,
            'scope':'registered type-2 main layers; existing metatiles; dimensions unchanged; native collision and traversal not certified'}
