"""Narrow named soul authoring backed by native menu/use evidence."""
from .core import PatchError, number
from .tables import layout, read_record


def plan_soul_edits(edits):
    """Validate the one registered cost edit before any ROM mutation."""
    if not isinstance(edits, list) or len(edits) != 1:
        raise PatchError('Soul edits require exactly one registered edit')
    edit = edits[0]
    if (not isinstance(edit, dict) or set(edit) != {'soul', 'expect', 'fields'}
            or edit['soul'] != 'winged-skeleton'
            or not isinstance(edit['expect'], dict) or set(edit['expect']) != {'mana_cost'}
            or not isinstance(edit['fields'], dict) or set(edit['fields']) != {'mana_cost'}):
        raise PatchError('Only winged-skeleton mana_cost with an explicit expectation is registered')
    expected, value = number(edit['expect']['mana_cost']), number(edit['fields']['mana_cost'])
    if not 0 <= expected <= 65535 or not 1 <= value <= 999:
        raise PatchError('Soul mana cost outside supported bounds (new cost 1..999)')
    return {'soul': 'winged-skeleton', 'table': 'red_souls', 'index': 1,
            'expected_mana_cost': expected, 'mana_cost': value}


def apply_soul_edits(rom, edits):
    plan = plan_soul_edits(edits)
    if rom.profile['id'] != 'aos-usa-r0':
        raise PatchError('Soul authoring requires the registered exact host')
    spec, address = layout('red_souls', 1)
    original_offset = rom.offset(address, spec['stride'])
    original = rom.original[original_offset:original_offset + spec['stride']]
    current = rom.read(address, spec['stride'])
    if current[:6] != original[:6] or current[8:] != original[8:]:
        raise PatchError('Registered soul identity/other fields changed')
    if int.from_bytes(original[6:8], 'little') != 12:
        raise PatchError('Registered soul original cost mismatch')
    if read_record(rom, 'red_souls', 1)['mana_cost'] != plan['expected_mana_cost']:
        raise PatchError('Soul mana cost precondition mismatch')
    rom.write(address + 6, plan['mana_cost'].to_bytes(2, 'little'),
              'soul:winged-skeleton:mana_cost', current[6:8])
    return [plan]
