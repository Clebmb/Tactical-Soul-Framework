"""Checked in-place renames of native item/enemy labels.

Only the label bytes change: replacement text must be ASCII printable and
fit the original byte length; shorter names are space-padded and the
original terminator is preserved, so no pointer moves and no relocation.
Safe edits preserve IDs, stats, drops and unknown bytes. Longer names,
relocated strings and dialogue codecs remain unimplemented.
"""
from .core import PatchError, number
from .equipment import item_name, key_for
from .text import POINTERS, original_label

KINDS = {
    'item': {'base': 0x5B, 'count': 136},
    'enemy': {'base': 0x25D, 'count': 113},
}


def _read_label(rom, text_id, blob):
    """Parse a label from an explicit bytes object (original or patched data)."""
    offset = rom.offset(POINTERS + 4 * number(text_id), 4)
    pointer = int.from_bytes(blob[offset:offset + 4], 'little')
    start = rom.offset(pointer, 2)
    if blob[start:start + 2] != b'\x01\x00':
        raise PatchError('Unexpected native label header')
    chars = []
    for b in blob[start + 2:start + 130]:
        if b in (6, 10):
            return ''.join(chars)
        if not 32 <= b <= 126:
            raise PatchError('Unsupported character/control in English label')
        chars.append(chr(b))
    raise PatchError('Unterminated native label')


def label_span(rom, text_id):
    """Byte span (chars start, char length) of a parsed label, terminator excluded."""
    text_id = number(text_id)
    offset = rom.offset(POINTERS + 4 * text_id, 4)
    pointer = int.from_bytes(rom.original[offset:offset + 4], 'little')
    offset = rom.offset(pointer, 2)
    if rom.original[offset:offset + 2] != b'\x01\x00':
        raise PatchError('Unexpected native label header')
    chars = []
    for i, b in enumerate(rom.original[offset + 2:offset + 130]):
        if b in (6, 10):
            return pointer + 2, i, b
        if not 32 <= b <= 126:
            raise PatchError('Unsupported character/control in English label')
        chars.append(chr(b))
    raise PatchError('Unterminated native label')


def resolve_label(rom, kind, name=None, index=None):
    """Name one writable label by item/enemy name/key or numeric index."""
    if kind not in KINDS:
        raise PatchError("Label kind must be 'item' or 'enemy'")
    if (name is None) == (index is None):
        raise PatchError('Specify exactly one label name/key or index')
    base, count = KINDS[kind]['base'], KINDS[kind]['count']
    if index is not None:
        index = number(index)
        if not 0 <= index < count:
            raise PatchError('Label index outside kind range')
    else:
        if not isinstance(name, str):
            raise PatchError('Label name must be a string')
        matches = []
        for i in range(count):
            candidate = item_name(rom, i) if kind == 'item' else original_label(rom, base + i)
            if name.casefold() in (candidate.casefold(), key_for(candidate)):
                matches.append(i)
        if len(matches) != 1:
            raise PatchError('Label name/key must match exactly one record')
        index = matches[0]
    text_id = base + index
    current = original_label(rom, text_id)
    start, length, _ = label_span(rom, text_id)
    return {'kind': kind, 'index': index, 'text_id': text_id,
            'current': current, 'max_length': length, 'address': hex(start)}


def apply_label_edits(rom, edits):
    """Validate the entire batch before writing; in-place bytes only."""
    pending = []
    claimed = set()
    for edit in edits:
        if set(edit) - {'kind', 'item', 'enemy', 'index', 'expect', 'to'}:
            raise PatchError('Unknown label edit properties')
        name = edit.get('item', edit.get('enemy'))
        row = resolve_label(rom, edit.get('kind'), name, edit.get('index'))
        if 'item' in edit and row['kind'] != 'item':
            raise PatchError('item names only resolve item labels')
        if 'enemy' in edit and row['kind'] != 'enemy':
            raise PatchError('enemy names only resolve enemy labels')
        expect = edit.get('expect', row['current'])
        if expect != row['current']:
            raise PatchError('Label precondition mismatch: ' + row['current'])
        claim = (row['kind'], row['index'])
        if claim in claimed:
            raise PatchError('Repeated label edit')
        claimed.add(claim)
        new = edit.get('to')
        if not isinstance(new, str) or not 1 <= len(new) <= row['max_length']:
            raise PatchError('Replacement must fit the original label length')
        if any(not 32 <= ord(c) <= 126 for c in new):
            raise PatchError('Replacement must be printable ASCII')
        pending.append((row, new))
    report = []
    for row, new in pending:
        start = int(row['address'], 16)
        payload = (new + ' ' * (row['max_length'] - len(new))).encode('ascii')
        rom.write(start, payload, 'label-%s-%d' % (row['kind'], row['index']),
                  rom.read(start, len(payload)))
        after = _read_label(rom, row['text_id'], bytes(rom.data))
        report.append({'kind': row['kind'], 'index': row['index'],
                       'before': row['current'], 'after': after})
    return report
