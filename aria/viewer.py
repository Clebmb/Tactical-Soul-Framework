"""Headless room-viewer view models (no GUI).

Contracts for a future graphical viewer: pure viewport math plus a room
view model (visible cells, entity/door markers, cropped layer pixels,
static audit notes) that also works from an editor document's manifest
state via clean builds. Pixel positions are native values; door cells
are metatile units. Nothing here certifies collision or gameplay.
"""
import copy
import hashlib

from .core import PatchError, number
from .level import audit_room, side
from .rendering import render_layer
from .rooms import dimensions, doors, entities, room_address

CELL_PX = 32
VIEWPORT = (240, 160)


def visible_range(room_cells, camera_px, viewport_px, cell_px=CELL_PX):
    """Inclusive visible cell range for one axis, clamped to the room."""
    room_cells = number(room_cells)
    camera_px = number(camera_px)
    viewport_px = number(viewport_px)
    cell_px = number(cell_px)
    if room_cells <= 0 or cell_px <= 0 or viewport_px <= 0 or camera_px < 0:
        raise PatchError('visible_range needs positive room/cell/viewport and nonnegative camera')
    if camera_px >= room_cells * cell_px:
        return {'first': 0, 'last': -1, 'count': 0}
    first = camera_px // cell_px
    last = min(room_cells - 1, (camera_px + viewport_px - 1) // cell_px)
    return {'first': first, 'last': last, 'count': last - first + 1}


def markers_in_view(markers, camera, viewport):
    """Filter {x,y} point markers to a camera/viewport rectangle."""
    if (not isinstance(camera, (list, tuple)) or not isinstance(viewport, (list, tuple)) or
            len(camera) != 2 or len(viewport) != 2):
        raise PatchError('camera and viewport must be (x, y) pairs')
    if any(not isinstance(v, int) or v < 0 for v in list(camera) + list(viewport)):
        raise PatchError('camera/viewport values must be nonnegative ints')
    if viewport[0] <= 0 or viewport[1] <= 0:
        raise PatchError('viewport dimensions must be positive')
    return [copy.deepcopy(m) for m in markers
            if camera[0] <= m['x'] < camera[0] + viewport[0]
            and camera[1] <= m['y'] < camera[1] + viewport[1]]


def crop_rgba(rgba, width, height, camera, viewport):
    """Crop a W*H*4 RGBA buffer to the camera/viewport overlap."""
    if (not isinstance(rgba, (bytes, bytearray)) or len(rgba) != width * height * 4 or
            width <= 0 or height <= 0):
        raise PatchError('Invalid RGBA buffer or dimensions')
    if (not isinstance(camera, (list, tuple)) or not isinstance(viewport, (list, tuple)) or
            len(camera) != 2 or len(viewport) != 2):
        raise PatchError('camera and viewport must be (x, y) pairs')
    if any(not isinstance(v, int) or v < 0 for v in list(camera) + list(viewport)):
        raise PatchError('camera/viewport values must be nonnegative ints')
    if viewport[0] <= 0 or viewport[1] <= 0:
        raise PatchError('viewport dimensions must be positive')
    actual_w = max(0, min(width - camera[0], viewport[0])) if camera[0] < width else 0
    actual_h = max(0, min(height - camera[1], viewport[1])) if camera[1] < height else 0
    out = bytearray(actual_w * actual_h * 4)
    for row in range(actual_h):
        src = ((camera[1] + row) * width + camera[0]) * 4
        out[row * actual_w * 4:(row + 1) * actual_w * 4] = rgba[src:src + actual_w * 4]
    return bytes(out), actual_w, actual_h


def _markers(rom, pointer, width_cells, height_cells):
    entity_markers = [{'id': e.unique_id, 'x': e.x, 'y': e.y,
                       'type': e.type, 'subtype': e.subtype}
                      for e in entities(rom, pointer)]
    door_markers = []
    for i, door in enumerate(doors(rom, pointer)):
        try:
            position = side(door, width_cells, height_cells)
        except PatchError:
            position = 'interior'
        door_markers.append({'index': i, 'x': door.x, 'y': door.y,
                             'side': position, 'destination': hex(door.destination)})
    return entity_markers, door_markers


def view_of_image(image, sector, index, layer, camera, viewport, renderer=render_layer):
    """View model for an already-built image (pure composition helper)."""
    sector, index, layer = number(sector), number(index), number(layer)
    if (not isinstance(camera, (list, tuple)) or not isinstance(viewport, (list, tuple)) or
            len(camera) != 2 or len(viewport) != 2):
        raise PatchError('camera and viewport must be (x, y) pairs')
    camera = (number(camera[0]), number(camera[1]))
    viewport = (number(viewport[0]), number(viewport[1]))
    pointer = room_address(image, sector, index)
    width_cells, height_cells = dimensions(image, pointer)
    if not width_cells or not height_cells:
        raise PatchError('Room has zero main-layer dimensions')
    pictured = renderer(image, sector, index, layer)
    if (not isinstance(pictured, dict) or
            not isinstance(pictured.get('rgba'), (bytes, bytearray)) or
            len(pictured['rgba']) != pictured['width'] * pictured['height'] * 4):
        raise PatchError('Renderer must return width/height/rgba (W*H*4 bytes)')
    cropped, actual_w, actual_h = crop_rgba(
        pictured['rgba'], pictured['width'], pictured['height'], camera, viewport)
    entity_markers, door_markers = _markers(image, pointer, width_cells, height_cells)
    audit = audit_room(image, sector, index)
    return {
        'sector': sector, 'index': index, 'layer': layer,
        'address': hex(pointer),
        'dimensions_cells': [width_cells, height_cells],
        'dimensions_px': [width_cells * CELL_PX, height_cells * CELL_PX],
        'camera': list(camera), 'viewport': list(viewport),
        'visible_cells': {
            'x': visible_range(width_cells, camera[0], viewport[0]),
            'y': visible_range(height_cells, camera[1], viewport[1])},
        'entity_markers': markers_in_view(entity_markers, camera, viewport),
        'entity_count_total': len(entity_markers),
        'door_markers': door_markers,
        'door_count_total': len(door_markers),
        'viewport_rgba': cropped, 'viewport_size': [actual_w, actual_h],
        'image_sha256': hashlib.sha256(pictured['rgba']).hexdigest(),
        'audit_errors': list(audit['errors']), 'audit_warnings': list(audit['warnings']),
        'scope': 'static viewer model; markers are native positions, not gameplay certification',
    }


def room_view(rom, sector, index, layer=0, camera=(0, 0), viewport=VIEWPORT):
    """View model for a room in an open image."""
    return view_of_image(rom, sector, index, layer, camera, viewport)


def document_view(state_or_doc, room, fresh_image, manifest_applier,
                  renderer=render_layer, folder=None):
    """View model for a document's manifest state via two clean builds.

    room is {'sector','index','layer'} plus optional 'camera'/'viewport'.
    Both builds must render identical viewport pixels and markers.
    """
    from .editor_docs import EditorDocument, fingerprint
    state = state_or_doc.current() if isinstance(state_or_doc, EditorDocument) else state_or_doc
    fingerprint(state)
    if (not isinstance(room, dict) or set(room) - {'sector', 'index', 'layer', 'camera', 'viewport'}
            or not {'sector', 'index'} <= set(room)):
        raise PatchError("room must hold sector/index plus optional layer/camera/viewport")
    if not callable(fresh_image) or not callable(manifest_applier):
        raise PatchError('document_view needs fresh_image and manifest_applier callables')
    camera = tuple(room.get('camera', (0, 0)))
    viewport = tuple(room.get('viewport', VIEWPORT))
    views = []
    for _ in range(2):
        try:
            image = fresh_image()
        except Exception as exc:
            raise PatchError('Clean image factory failed: %s' % exc)
        manifest_applier(image, copy.deepcopy(state), folder)
        views.append(view_of_image(image, room['sector'], room['index'],
                                   room.get('layer', 0), camera, viewport, renderer))
    if (views[0]['viewport_rgba'] != views[1]['viewport_rgba'] or
            views[0]['entity_markers'] != views[1]['entity_markers'] or
            views[0]['door_markers'] != views[1]['door_markers']):
        raise PatchError('Document view is not deterministic from a clean image')
    return views[0]
