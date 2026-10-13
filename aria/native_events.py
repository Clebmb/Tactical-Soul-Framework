"""Read-only registered native observations; no grants or native enforcement."""
from .core import PatchError


FIELDS = {
    'state': (0x02000010, 1),
    'substate': (0x02000064, 1),
    'room_address': (0x02000088, 4),
    'global_flags': (0x0200042C, 4),
    'player_state': (0x020004EE, 1),
}


def observe_native_events(read):
    """Sample a reader(address, byte_count); callers must pause the native core.

    Bit zero is observed during a statue prompt and used by the ability guard.
    Other producers and meanings are unknown. This is not a persistent flag ABI.
    Reads are sequential, not an atomic snapshot of a running emulator.
    """
    values = {}
    for name, (address, size) in FIELDS.items():
        value = read(address, size)
        if type(value) is not int or not 0 <= value < (1 << (8 * size)):
            raise PatchError('Invalid native observation: ' + name)
        values[name] = value
    return {'schema_version': 1, 'context': values,
            'modal_lock_bit': bool(values['global_flags'] & 1),
            'address': 0x0200042C, 'mask': 1,
            'lifetime': 'transient', 'persistent_progression_binding': False}


def observe_progression_flags(read):
    """Observe the first red-soul ownership nibble in settled USA-r0 gameplay.

    Exact-host validation and a paused core are caller responsibilities. Only
    this slot has native acquisition/save/continue evidence. No grant ABI,
    automatic policy linkage, or lifetime monotonicity is implied.
    """
    context = observe_native_events(read)['context']
    if (context['state'] != 4 or context['substate'] != 1
            or not 0x08000000 <= context['room_address'] < 0x08800000
            or context['room_address'] % 4):
        raise PatchError('Progression observations require settled supported gameplay')
    raw = read(0x0201331C, 1)
    if type(raw) is not int or not 0 <= raw <= 255:
        raise PatchError('Invalid first red-soul ownership byte')
    count = raw & 15
    return {'schema_version': 1, 'context': context,
            'flags': {'first_red_soul_owned': count > 0},
            'first_red_soul': {'address': 0x0201331C, 'mask': 15,
                               'raw_byte': raw, 'count': count,
                               'name': 'Winged Skeleton', 'record_table': 'red_souls',
                               'record_index': 1, 'text_id': 0xE3},
            'scope': 'read-only ownership observation; no native grants or gate enforcement'}
