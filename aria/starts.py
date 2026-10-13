"""Checked USA-r0 new-game constants; not a campaign/save compiler.

Offsets: DSVEdit constants/aos_constants.rb NEW_GAME_STARTING_*.
Existing native fixture: scripts/verify_background_rendering.py.
Only registry-verified room/landing pairs are authorized here; each
registration needs native landing evidence, and save rooms additionally
need statue-save/fresh-continue evidence.
"""
from .core import PatchError
from .content import integer
from .rooms import room_address, dimensions

# Room (sector, room) to exact verified landing (x, y) in pixels.
VERIFIED_STARTS = {(0, 31): (128, 141), (0, 14): (128, 160)}


def install_new_game_start(rom, spec):
    if not isinstance(spec, dict) or set(spec) != {'sector', 'room', 'position'}:
        raise PatchError('new_game_start requires sector, room, position')
    sector = integer(spec['sector'], 0, 255)
    room = integer(spec['room'], 0, 255)
    if (sector, room) not in VERIFIED_STARTS:
        raise PatchError('Only registry-verified start rooms are supported')
    position = spec['position']
    if not isinstance(position, list) or len(position) != 2:
        raise PatchError('Start position requires two pixel coordinates')
    x, y = [integer(v, 0, 65535) for v in position]
    w, h = dimensions(rom, room_address(rom, sector, room))
    if not (0 <= x < w*256 and 0 <= y < h*256):
        raise PatchError('Start position outside room')
    # Keep each registration exact until further native landing evidence.
    if (x, y) != VERIFIED_STARTS[(sector, room)]:
        raise PatchError('Only the verified landing for this start room is supported')
    writes = [(0x084F0D8C, bytes([sector, room]), bytes.fromhex('0000')),
              (0x084F0D8E, bytes(4), bytes.fromhex('20000002')),
              (0x084F0D92, x.to_bytes(2, 'little') + y.to_bytes(2, 'little'),
               bytes.fromhex('78008d00'))]
    for address, data, expected in writes:
        if rom.read(address, len(expected)) != expected:
            raise PatchError('New-game start preimage mismatch')
    for address, data, expected in writes:
        rom.write(address, data, 'new-game-start', expected)
    return {'sector': sector, 'room': room, 'position': [x, y],
            'scope': 'new games only; existing saves unchanged'}
