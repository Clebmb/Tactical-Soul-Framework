"""Read/write known native record fields; indices are zero-based table indices.

Byte widths are unsigned storage, not a promise about gameplay interpretation.
Code-pointer fields need verified Thumb entry points and ABI-compatible code.
"""
import json
from pathlib import Path
from .core import PatchError, number

LAYOUTS = json.loads((Path(__file__).resolve().parents[1]/"framework/tables.json").read_text())["tables"]

def layout(table, index):
    if table not in LAYOUTS:
        raise PatchError(f"Unknown native table: {table}")
    spec = LAYOUTS[table]
    index = number(index)
    if not 0 <= index < spec["count"]:
        raise PatchError(f"Index out of range for {table}: {index}")
    return spec, number(spec["address"])+index*spec["stride"]

def read_record(rom, table, index):
    spec, address = layout(table, index)
    return {name: rom.integer(address+field["offset"], field["size"])
            for name, field in spec["fields"].items()}

def edit_record(rom, table, index, values):
    spec, address = layout(table, index)
    if not values:
        raise PatchError("A table edit must specify at least one field")
    for name, value in values.items():
        if name not in spec["fields"]:
            raise PatchError(f"Unknown field {table}.{name}")
        field = spec["fields"][name]
        rom.write_integer(address+field["offset"], value, field["size"],
                          f"{table}[{index}].{name}")
