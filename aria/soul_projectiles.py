"""Read-only Winged Skeleton cast/projectile observation helpers.

No ROM writes, no soul grants, no projectile/SFX authoring. This module
supports one bounded investigation toward
``docs/CUSTOM-PROJECTILE-ABILITIES.md``: what (if anything) appears in the
established enemy-actor window when the verified Winged Skeleton cast route
(Up+B, ``scripts/verify_soul_menu.py``) spends MP.

Boundaries:

- ``describe_winged_skeleton`` reads the static ``red_souls[1]`` record only.
  Field widths do not establish native call signatures or projectile semantics.
- ``snapshot_actor_window`` reads the 224-slot window at ``0x020004E4`` with
  stride ``0x84`` established by ``scripts/scan_soul_spawn.py``. A soul
  projectile may live outside this window; absence here is not proof of
  absence everywhere.
- ``count_pointer_occurrences`` is a bounded static byte search for the soul
  ``code`` pointer. Hits are candidates for further work, not proven consumers.
- ``compare_audio_windows`` compares two PCM byte strings (peak/RMS/equality).
  A mixed/BGM difference is not SFX attribution; see ``docs/MUSIC-LIFECYCLE.md``.
"""

from .core import PatchError

TABLE = 'red_souls'
INDEX = 1
EXPECTED_MANA_COST = 12

ACTOR_BASE = 0x020004E4
ACTOR_STRIDE = 0x84
ACTOR_SLOTS = 224
SLOT_WORDS = ACTOR_STRIDE // 4
SLOT_WORD8_OFFSET = 32

MAX_POINTER_HITS = 500


def describe_winged_skeleton(rom):
    """Read the static Winged Skeleton soul record; no mutation."""
    from .tables import read_record
    if rom.profile['id'] != 'aos-usa-r0':
        raise PatchError('Soul projectile observation requires the registered exact host')
    record = read_record(rom, TABLE, INDEX)
    code = record['code']
    return {
        'table': TABLE,
        'index': INDEX,
        'code': code,
        'code_hex': hex(code),
        'code_is_thumb': bool(code & 1),
        'use_animation': record['use_animation'],
        'mana_cost': record['mana_cost'],
        'max_at_once': record['max_at_once'],
        'damage_multiplier': record['damage_multiplier'],
        'effects': record['effects'],
        'var_a': record['var_a'],
        'pointer_bytes_hex': code.to_bytes(4, 'little').hex(),
        'scope': 'static record only; no spawn/render/collision/SFX proof',
    }


def snapshot_actor_window(read):
    """Snapshot nonzero 4-byte actor codes keyed by slot index.

    ``read`` is a callable ``(address, size) -> int`` such as
    ``Emulator.read`` on a paused core. Raises PatchError on invalid values.
    """
    snapshot = {}
    for slot in range(ACTOR_SLOTS):
        value = read(ACTOR_BASE + slot * ACTOR_STRIDE, 4)
        if type(value) is not int or not 0 <= value < (1 << 32):
            raise PatchError('Invalid actor code at slot %d' % slot)
        if value:
            snapshot[slot] = value
    return snapshot


def slot_base(slot):
    """Return the RAM base address of an actor slot; validates range."""
    if type(slot) is not int or not 0 <= slot < ACTOR_SLOTS:
        raise PatchError('Actor slot must be 0..%d' % (ACTOR_SLOTS - 1))
    return ACTOR_BASE + slot * ACTOR_STRIDE


def read_slot_word(read, slot, index):
    """Read one little-endian u32 word from an actor slot record."""
    if type(index) is not int or not 0 <= index < SLOT_WORDS:
        raise PatchError('Actor record word must be 0..%d' % (SLOT_WORDS - 1))
    value = read(slot_base(slot) + 4 * index, 4)
    if type(value) is not int or not 0 <= value < (1 << 32):
        raise PatchError('Invalid actor record word at slot %d word %d' % (slot, index))
    return value


def read_slot_record(read, slot):
    """Read all 33 u32 words of one actor slot record as a list."""
    return [read_slot_word(read, slot, index) for index in range(SLOT_WORDS)]


def diff_records(before, after):
    """Diff two slot-record word lists; returns changed index facts.

    Each entry holds ``index``, ``before``/``after`` hex, signed ``delta`` and
    ``delta_hex``. Word semantics are unknown; a changing word is a tracking
    candidate, not a proven position or velocity field.
    """
    for name, record in (('before', before), ('after', after)):
        if (not isinstance(record, list) or len(record) != SLOT_WORDS
                or any(type(word) is not int or not 0 <= word < (1 << 32) for word in record)):
            raise PatchError('Record diff requires two %d-word u32 lists: ' % SLOT_WORDS + name)
    changes = []
    for index, (old, new) in enumerate(zip(before, after)):
        if old != new:
            delta = new - old
            if delta >= 1 << 31:
                delta -= 1 << 32
            changes.append({'index': index, 'before_hex': hex(old), 'after_hex': hex(new),
                            'delta': delta, 'delta_hex': hex(delta & 0xFFFFFFFF)})
    return changes


def fit_word_series(values, step_frames=1):
    """Fit a per-sample u32 word series; returns delta/motion facts.

    Deltas are signed 32-bit per step. ``monotonic`` means every delta shares
    one nonzero sign; ``constant`` means all deltas are equal and nonzero. A
    constant fit describes steady motion at an unproven scale, not a certified
    position or velocity semantic.
    """
    if (not isinstance(values, list) or len(values) < 2
            or any(type(value) is not int or not 0 <= value < (1 << 32) for value in values)):
        raise PatchError('Series fit requires a list of at least two u32 words')
    if type(step_frames) is not int or step_frames < 1:
        raise PatchError('Series fit requires a positive integer frame step')
    deltas = []
    for old, new in zip(values, values[1:]):
        delta = new - old
        if delta >= 1 << 31:
            delta -= 1 << 32
        elif delta < -(1 << 31):
            delta += 1 << 32
        deltas.append(delta)
    nonzero = [delta for delta in deltas if delta]
    monotonic = bool(nonzero) and (all(delta > 0 for delta in nonzero)
                                   or all(delta < 0 for delta in nonzero))
    return {
        'samples': len(values),
        'step_frames': step_frames,
        'first_hex': hex(values[0]),
        'last_hex': hex(values[-1]),
        'displacement': sum(deltas),
        'displacement_hex': hex(sum(deltas) & 0xFFFFFFFF),
        'deltas': deltas,
        'monotonic': monotonic,
        'constant': bool(nonzero) and all(delta == nonzero[0] for delta in deltas),
        'mean_delta': sum(deltas) / len(deltas),
        'min_delta': min(deltas),
        'max_delta': max(deltas),
        'scope': 'steady-motion description at unproven scale; not a velocity certification',
    }


def diff_bytes(before, after):
    """Diff two equal-length byte strings; returns changed offsets and runs.

    ``ranges`` collapses adjacent changed offsets into ``{start, length}``
    runs. A difference names changed bytes, not proven ownership or meaning.
    """
    for name, blob in (('before', before), ('after', after)):
        if not isinstance(blob, (bytes, bytearray)) or not blob:
            raise PatchError('Byte diff requires nonempty byte strings: ' + name)
    if len(before) != len(after):
        raise PatchError('Byte diff requires equal lengths')
    changed = [index for index, (old, new) in enumerate(zip(before, after)) if old != new]
    ranges = []
    for index in changed:
        if ranges and index == ranges[-1]['start'] + ranges[-1]['length']:
            ranges[-1]['length'] += 1
        else:
            ranges.append({'start': index, 'length': 1})
    return {'count': len(changed), 'changed': changed, 'ranges': ranges,
            'scope': 'changed-byte facts only; not ownership proof'}


def classify_transition(before, during, after):
    """Classify actor-code sets across a kill-like transition.

    Inputs are sets (or lists) of code-hex strings sampled before, during and
    after the transition. Returns ``victim`` (gone after), ``transient``
    (only during) and ``new_persistent`` (during and after, absent before).
    Classes describe timing, not proven death/burst/pickup semantics.
    """
    for name, sample in (('before', before), ('during', during), ('after', after)):
        if not isinstance(sample, (set, list)) or any(type(code) is not str for code in sample):
            raise PatchError('Transition classification requires code-hex sets: ' + name)
    before, during, after = set(before), set(during), set(after)
    return {'victim': sorted(before - after),
            'transient': sorted(during - before - after),
            'new_persistent': sorted((during & after) - before),
            'scope': 'timing classes only; not death/burst/pickup proof'}


def scan_decreases(before_records, after_records, min_drop=1, max_drop=999):
    """Find (slot, word) entries that fell by a bounded amount between scans.

    Inputs map slot index to 33-word u32 record lists. A repeated identical
    drop across two hits is an HP candidate; a single drop is only a lead.
    """
    if type(min_drop) is not int or type(max_drop) is not int or not 1 <= min_drop <= max_drop:
        raise PatchError('HP scan requires a positive drop range')
    for name, records in (('before', before_records), ('after', after_records)):
        if (not isinstance(records, dict) or not records
                or any(type(slot) is not int or not isinstance(record, list)
                       or len(record) != SLOT_WORDS
                       or any(type(word) is not int or not 0 <= word < (1 << 32)
                              for word in record) for slot, record in records.items())):
            raise PatchError('HP scan requires slot-to-record maps: ' + name)
    leads = []
    for slot in sorted(set(before_records) & set(after_records)):
        for index, (old, new) in enumerate(zip(before_records[slot], after_records[slot])):
            if old > new and min_drop <= old - new <= max_drop:
                leads.append({'slot': slot, 'index': index, 'before': old,
                              'after': new, 'drop': old - new})
    return {'leads': leads,
            'scope': 'bounded-drop leads only; repetition plus kill proof required'}


OAM_ENTRY_SIZE = 8
OAM_ENTRIES = 128
OBJ_TILE_BASE = 0x06010000
SHAPE_SIZES = {
    (0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
    (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
    (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64),
}


def decode_oam_entry(block):
    """Decode 8 OAM bytes per the GBA hardware format (GBATEK OBJ attributes).

    Returns y/x, tile number, 16-color palette bank, pixel size, color depth
    and disable/affine flags. Hardware facts only: which game actor owns an
    entry stays open.
    """
    import struct
    if not isinstance(block, (bytes, bytearray)) or len(block) != OAM_ENTRY_SIZE:
        raise PatchError('OAM decode requires exactly 8 bytes')
    attr0, attr1, attr2, _fill = struct.unpack('<4H', bytes(block))
    shape, size = (attr0 >> 14) & 3, (attr1 >> 14) & 3
    pixels = SHAPE_SIZES.get((shape, size))
    if pixels is None:
        raise PatchError('OAM entry has prohibited shape %d' % shape)
    colors256 = bool(attr0 & 0x2000)
    return {'y': attr0 & 0xFF, 'x': attr1 & 0x1FF,
            'tile': attr2 & 0x3FF, 'priority': (attr2 >> 10) & 3,
            'palette': 0 if colors256 else (attr2 >> 12) & 15,
            'colors256': colors256, 'size_pixels': list(pixels),
            'disabled': not (attr0 & 0x100) and bool(attr0 & 0x200),
            'affine': bool(attr0 & 0x100),
            'scope': 'hardware decode only; entry ownership open'}


def slot_world_x(read, slot):
    """Calibrated actor world-x: record word 8 low halfword over 256.

    Established in docs/ENEMY-BINDING.md (v0.44) on a zombie 254->93 approach.
    World-y has no calibrated mapping here; do not guess one.
    """
    return (read_slot_word(read, slot, 8) & 0xFFFF) / 256.0


def compare_cast_twins(first, second):
    """Compare two per-code cast summaries ``{code: {first, last, slots}}``.

    Returns equality facts plus a bounded diff list; a match names repeatable
    spawn timing, not rendering, damage or SFX proof.
    """
    for name, summary in (('first', first), ('second', second)):
        if not isinstance(summary, dict):
            raise PatchError('Twin comparison requires dict summaries: ' + name)
        for code, row in summary.items():
            if (not isinstance(row, dict) or set(row) != {'first', 'last', 'slots'}
                    or type(row['first']) is not int or type(row['last']) is not int
                    or not isinstance(row['slots'], list)):
                raise PatchError('Twin summary row must hold first/last/slots: ' + str(code))
    diffs = []
    if set(first) != set(second):
        diffs.append('novel code sets differ: %s vs %s' % (sorted(first), sorted(second)))
    for code in sorted(set(first) & set(second)):
        if first[code]['first'] != second[code]['first'] or first[code]['last'] != second[code]['last']:
            diffs.append('timing differs for %s: %s vs %s'
                         % (code, (first[code]['first'], first[code]['last']),
                            (second[code]['first'], second[code]['last'])))
        if sorted(first[code]['slots']) != sorted(second[code]['slots']):
            diffs.append('slots differ for %s: %s vs %s'
                         % (code, sorted(first[code]['slots']), sorted(second[code]['slots'])))
    return {
        'novel_equal': set(first) == set(second),
        'timing_equal': all(first[c]['first'] == second[c]['first']
                            and first[c]['last'] == second[c]['last']
                            for c in set(first) & set(second)),
        'slots_equal': all(sorted(first[c]['slots']) == sorted(second[c]['slots'])
                           for c in set(first) & set(second)),
        'identical': not diffs,
        'diffs': diffs,
        'scope': 'spawn timing/slot repeatability only; not render/damage/SFX proof',
    }


def code_to_slots(snapshot):
    """Invert a slot->code snapshot into code_hex -> sorted slot list."""
    inverted = {}
    for slot, code in snapshot.items():
        inverted.setdefault(hex(code), []).append(slot)
    return {code: sorted(slots) for code, slots in inverted.items()}


def novel_codes(baseline, current):
    """Return sorted code_hex values present in current but absent in baseline."""
    before = {hex(code) for code in baseline.values()}
    after = {hex(code): code for code in current.values()}
    return sorted(code for code in after if code not in before)


def count_pointer_occurrences(data, pointer, limit=MAX_POINTER_HITS):
    """Bounded static search for a little-endian pointer in ROM bytes.

    Returns file offsets where the 4-byte pattern occurs, capped at ``limit``.
    Hits are search candidates, not proven consumers.
    """
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise PatchError('Pointer search requires nonempty ROM bytes')
    if type(pointer) is not int or not 0 <= pointer < (1 << 32):
        raise PatchError('Pointer search requires a 32-bit code value')
    if type(limit) is not int or not 1 <= limit <= MAX_POINTER_HITS:
        raise PatchError('Pointer search limit must be 1..%d' % MAX_POINTER_HITS)
    pattern = pointer.to_bytes(4, 'little')
    hits, offset = [], 0
    while True:
        index = data.find(pattern, offset)
        if index < 0:
            break
        hits.append(index)
        if len(hits) >= limit:
            break
        offset = index + 1
    return hits


def compare_audio_windows(first, second):
    """Compare two raw PCM byte strings; returns peak/RMS/equality facts."""
    import math
    import struct
    for name, blob in (('first', first), ('second', second)):
        if not isinstance(blob, (bytes, bytearray)) or not blob or len(blob) % 2:
            raise PatchError('Audio comparison requires nonempty even-length PCM: ' + name)
    first_samples = struct.unpack('<' + 'h' * (len(first) // 2), bytes(first))
    second_samples = struct.unpack('<' + 'h' * (len(second) // 2), bytes(second))
    peak = lambda samples: max(abs(value) for value in samples)
    rms = lambda samples: math.sqrt(sum(value * value for value in samples) / len(samples))
    return {
        'first_bytes': len(first),
        'second_bytes': len(second),
        'equal': bytes(first) == bytes(second),
        'first_peak': peak(first_samples),
        'second_peak': peak(second_samples),
        'first_rms': rms(first_samples),
        'second_rms': rms(second_samples),
        'scope': 'mixed-output comparison only; not SFX attribution',
    }
