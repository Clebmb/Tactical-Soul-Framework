"""Named exact-profile native resources, lossless export and sparse authoring.

No addresses are inferred from asset filenames. Registered payloads remain in
place; their native headers are checked and never rewritten by this module.
"""
import hashlib
from .core import PatchError, number
from .content import integer, palette, tiles


def descriptor(rom, name):
    registry = rom.profile.get("content_resources", {})
    if name not in registry:
        raise PatchError("Unknown native content resource: " + str(name))
    d = registry[name]
    address, size = number(d["address"]), number(d["size"])
    start = rom.offset(address, size)
    original = rom.original[start:start + size]
    if hashlib.sha256(original).hexdigest() != d["original_sha256"]:
        raise PatchError("Resource profile preimage drift: " + name)
    header = bytes.fromhex(d["header_hex"])
    if rom.read(d["header_address"], len(header)) != header:
        raise PatchError("Native resource header changed: " + name)
    if d["format"] == "tiles4":
        if number(d["width"]) * number(d["height"]) // 2 != size:
            raise PatchError("Resource tile dimensions do not match payload")
    elif d["format"] != "palette_rgb8" or size % 2:
        raise PatchError("Unsupported registered resource format")
    return d


def catalog(rom):
    rows = []
    for name in rom.profile.get("content_resources", {}):
        d = descriptor(rom, name)
        rows.append(dict(d, id=name,
            current_sha256=hashlib.sha256(rom.read(d["address"], d["size"])).hexdigest(),
            unit="8x8 tile" if d["format"] == "tiles4" else "RGB555 color",
            units=d["size"] // (32 if d["format"] == "tiles4" else 2)))
    return rows


def decode_tiles(data, width, height):
    if width % 8 or height % 8 or len(data) != width * height // 2:
        raise PatchError("Invalid native tile dimensions/length")
    pixels = [0] * (width * height)
    pos = 0
    for ty in range(0, height, 8):
        for tx in range(0, width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    b = data[pos]; pos += 1
                    i = (ty + y) * width + tx + x
                    pixels[i:i + 2] = [b & 15, b >> 4]
    return {"width": width, "height": height, "pixels": pixels}


def export_resource(rom, name):
    d = descriptor(rom, name)
    data = rom.read(d["address"], d["size"])
    if d["format"] == "tiles4":
        return decode_tiles(data, d["width"], d["height"])
    colors = []
    for i in range(0, len(data), 2):
        value = int.from_bytes(data[i:i + 2], "little")
        if value & 0x8000:
            raise PatchError("RGB export cannot preserve palette bit 15")
        colors.append([(value & 31) << 3, ((value >> 5) & 31) << 3,
                       ((value >> 10) & 31) << 3])
    return colors


def replace_named(rom, name, kind, encoding, payload, label):
    d = descriptor(rom, name)
    if kind != d["format"] or encoding != "raw" or len(payload) != d["size"]:
        raise PatchError("Named resource requires its exact raw format and size")
    address = number(d["address"])
    start = rom.offset(address, len(payload))
    rom.write(address, payload, label, rom.original[start:start + len(payload)])
    return address


def apply_resource_edits(rom, entries):
    if not isinstance(entries, list) or not entries:
        raise PatchError("resource_edits must be a nonempty list")
    plans, reports, resources = [], [], set()
    for entry in entries:
        required = {"resource", "expected_sha256", "provenance"}
        if not isinstance(entry, dict) or set(entry) - (required | {"tiles", "colors"}) or not required <= set(entry):
            raise PatchError("Unknown/missing resource edit properties")
        name = entry["resource"]
        if not isinstance(name, str) or name in resources:
            raise PatchError("Use one edit batch per named resource")
        resources.add(name)
        d = descriptor(rom, name)
        if entry["expected_sha256"] != d["original_sha256"]:
            raise PatchError("Resource edit original hash mismatch")
        if not isinstance(entry["provenance"], str) or not entry["provenance"].strip():
            raise PatchError("Resource edits require provenance")
        key = "tiles" if d["format"] == "tiles4" else "colors"
        other = "colors" if key == "tiles" else "tiles"
        rows = entry.get(key)
        if other in entry or not isinstance(rows, list) or not rows:
            raise PatchError("Resource requires nonempty " + key + " edits only")
        seen = set(); unit = 32 if key == "tiles" else 2
        for row in rows:
            fields = {"index", "pixels" if key == "tiles" else "rgb"}
            if not isinstance(row, dict) or set(row) != fields:
                raise PatchError("Invalid sparse resource row")
            index = integer(row["index"], 0, d["size"] // unit - 1)
            if index in seen:
                raise PatchError("Duplicate sparse resource index")
            seen.add(index)
            payload = tiles({"width": 8, "height": 8, "pixels": row["pixels"]}) if key == "tiles" else palette([row["rgb"]])
            address = number(d["address"]) + index * unit
            start = rom.offset(address, unit)
            plans.append((address, payload, "resource:" + name + ":" + str(index), rom.original[start:start + unit]))
        reports.append({"resource": name, "format": d["format"],
                        "indices": sorted(seen), "units_changed": len(seen),
                        "bytes_claimed": len(seen) * unit,
                        "provenance": entry["provenance"]})
    # The shared ledger still rejects conflicts with all other manifest layers.
    for address, payload, label, expected in plans:
        rom.write(address, payload, label, expected)
    return reports


def diff_resource(rom, name, authored, provenance):
    """Create a sparse entry against immutable original, not a modded preview."""
    d = descriptor(rom, name)
    if not isinstance(provenance, str) or not provenance.strip():
        raise PatchError("Diff requires asset provenance")
    key = "tiles" if d["format"] == "tiles4" else "colors"
    if key == "tiles":
        if not isinstance(authored, dict) or authored.get("width") != d["width"] or authored.get("height") != d["height"]:
            raise PatchError("Authored sheet dimensions must match native resource")
        data = tiles(authored); unit = 32
    else:
        data = palette(authored); unit = 2
    if len(data) != d["size"]:
        raise PatchError("Authored resource size mismatch")
    start = rom.offset(d["address"], d["size"])
    original = rom.original[start:start + d["size"]]
    rows = []
    for i in range(0, len(data), unit):
        chunk = data[i:i + unit]
        if chunk == original[i:i + unit]:
            continue
        row = {"index": i // unit}
        if key == "tiles":
            row["pixels"] = decode_tiles(chunk, 8, 8)["pixels"]
        else:
            value = int.from_bytes(chunk, "little")
            row["rgb"] = [(value & 31) << 3, ((value >> 5) & 31) << 3, ((value >> 10) & 31) << 3]
        rows.append(row)
    if not rows:
        raise PatchError("No encoded changes; RGB changes below 5-bit precision may disappear")
    return {"resource": name, "expected_sha256": d["original_sha256"],
            "provenance": provenance, key: rows}
