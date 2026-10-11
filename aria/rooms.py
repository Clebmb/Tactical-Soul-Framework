"""Native room/entity/door serialization. Geometry/map editing is separate.

Moving native entities preserves their IDs and requires sorted loading order.
Adding an enemy does not automatically provision its sprite/palette resources.
Do not infer complete room safety from successful binary serialization.
"""
import struct
from dataclasses import dataclass, asdict
from .core import PatchError, number

@dataclass
class Entity:
    x: int
    y: int
    unique_id: int
    type: int
    subtype: int
    byte_8: int = 0
    var_a: int = 0
    var_b: int = 0

    def pack(self):
        if self.x == 32767:
            raise PatchError("Entity x=32767 is reserved for the list terminator")
        try:
            return struct.pack("<hhBBBBHH", self.x, self.y, self.unique_id,
                               self.type, self.subtype, self.byte_8, self.var_a, self.var_b)
        except struct.error as error:
            raise PatchError("Native entity field out of range") from error

@dataclass
class Door:
    destination: int
    x: int
    y: int
    dest_x_2: int = 0
    dest_y_2: int = 0
    dest_x: int = 0
    dest_y: int = 0
    unused: int = 0

    def pack(self):
        try:
            return struct.pack("<IBB5H", self.destination, self.x, self.y,
                               self.dest_x_2, self.dest_y_2, self.dest_x, self.dest_y, self.unused)
        except struct.error as error:
            raise PatchError("Native door field out of range") from error

def sector_span(rom, sector):
    """Bound the AoS room-pointer table; last sector ends at the area table.

    AoS has no null terminator. DSVEdit sector.rb establishes the final area
    boundary. Never read a thirteenth sector pointer from unrelated layer data.
    """
    sector = number(sector)
    if not 0 <= sector < 12:
        raise PatchError("Only normal sectors 0..11 supported")
    area = rom.integer(0x08001990)
    rom.offset(area, 12*4)
    table = rom.integer(area+sector*4)
    next_table = rom.integer(area+(sector+1)*4) if sector < 11 else area
    if table%4 or next_table%4 or not table < next_table <= area or (next_table-table)//4 > 256:
        raise PatchError("Invalid or oversized sector room-table boundary")
    rom.offset(table, next_table-table)
    return table, (next_table-table)//4


def room_address(rom, sector, index):
    sector, index = number(sector), number(index)
    table, count = sector_span(rom,sector)
    if not 0 <= index < count:
        raise PatchError("Room index outside sector table")
    pointer = rom.integer(table+index*4)
    rom.offset(pointer, 36)
    return pointer

def metadata(rom, pointer):
    return list(struct.unpack("<HH8I", rom.read(pointer, 36)))

def dimensions(rom, pointer):
    values = metadata(rom, pointer)
    layer_data = rom.integer(values[3]+8)
    if not layer_data:
        raise PatchError("No main layer geometry to determine entity loading order")
    return tuple(rom.read(layer_data, 2))

def entities(rom, pointer, limit=256):
    address = metadata(rom, pointer)[6]
    result = []
    for i in range(limit):
        row = struct.unpack("<hhBBBBHH", rom.read(address+i*12, 12))
        if row[0] == 32767:
            return result
        result.append(Entity(*row))
    raise PatchError("Entity terminator not found within bound")

def doors(rom, pointer):
    values = metadata(rom, pointer)
    count = values[8] & 0xFFFF
    if count > 256:
        raise PatchError("Unsupported door count")
    return [Door(*struct.unpack("<IBB5H", rom.read(values[7]+i*16, 16))) for i in range(count)]

def replace_entities(rom, pointer, rows, label):
    if len(rows) > 255:
        raise PatchError("Native entity IDs are bytes; at most 255 entries supported")
    if len({e.unique_id for e in rows}) != len(rows):
        raise PatchError("Duplicate native entity unique_id")
    width, height = dimensions(rom, pointer)
    rows = sorted(rows, key=lambda e: (e.type == 0, e.y if height > width else e.x))
    payload = b"".join(e.pack() for e in rows)+struct.pack("<6H", 32767, 0, 0, 0, 0, 0)
    address = rom.allocate(label+"-entities", payload)
    rom.write_integer(pointer+20, address, 4, label+"-entity-pointer")
    return address

def replace_doors(rom, pointer, rows, label):
    # Door array replacement does not rebuild world-map/save metadata.
    for door in rows:
        rom.offset(door.destination, 36)
    if len(rows) > 256:
        raise PatchError("Too many doors")
    address = rom.allocate(label+"-doors", b"".join(d.pack() for d in rows)) if rows else 0
    rom.write_integer(pointer+24, address, 4, label+"-door-pointer")
    old = rom.integer(pointer+28)
    rom.write_integer(pointer+28, (old & 0xFFFF0000)|len(rows), 4, label+"-door-count")
    return address

def describe(rom, sector, index):
    pointer = room_address(rom, sector, index)
    return {"sector":sector,"index":index,"address":hex(pointer),
            "dimensions":dimensions(rom,pointer),"metadata":metadata(rom,pointer),
            "entities":[asdict(e) for e in entities(rom,pointer)],
            "doors":[asdict(d) for d in doors(rom,pointer)]}
