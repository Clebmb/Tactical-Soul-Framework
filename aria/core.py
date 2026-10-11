"""Verified ROM image, strict patch ledger, and aligned free-space allocation.

All addresses accepted here are virtual GBA ROM addresses (0x08000000 base).
Ranges are half-open. Every mutation is logged and checked for overlap before
output is written. Original bytes remain immutable in ``original``.
"""
import hashlib
from pathlib import Path

class PatchError(ValueError):
    """Invalid version, bounds, expected bytes, or conflicting mutation."""

def number(value):
    if isinstance(value, bool):
        raise PatchError("Booleans are not numeric addresses/values")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise PatchError("Expected an integer or 0x-prefixed string")

class RomImage:
    def __init__(self, original, profile):
        self.original = bytes(original)
        self.profile = profile
        self.base = number(profile["rom_base"])
        if len(self.original) != profile["size"]:
            raise PatchError("Unsupported ROM size")
        if hashlib.sha256(self.original).hexdigest() != profile["sha256"]:
            raise PatchError("Unsupported ROM SHA-256; use the exact documented original")
        self.data = bytearray(self.original)
        self.ledger = []
        self.allocations = {}
        self.cursors = [number(r["start"]) for r in profile["allocation_ranges"]]

    def offset(self, address, size=1):
        address = number(address)
        offset = address-self.base
        if size < 0 or offset < 0 or offset+size > len(self.data):
            raise PatchError(f"ROM address out of bounds: {address:#x}, {size} bytes")
        return offset

    def read(self, address, size):
        offset = self.offset(address, size)
        return bytes(self.data[offset:offset+size])

    def integer(self, address, size=4):
        return int.from_bytes(self.read(address, size), "little")

    def write(self, address, payload, label, expected=None):
        address = number(address)
        payload = bytes(payload)
        if not payload:
            raise PatchError("Empty patches are not meaningful")
        offset = self.offset(address, len(payload))
        end = address+len(payload)
        for previous in self.ledger:
            if address < previous["end"] and previous["address"] < end:
                raise PatchError(f"Patch conflict: {label} overlaps {previous['label']}")
        before = bytes(self.data[offset:offset+len(payload)])
        if expected is not None and before != bytes(expected):
            raise PatchError(f"Expected bytes mismatch: {label} at {address:#x}")
        self.data[offset:offset+len(payload)] = payload
        self.ledger.append({"label": label, "address": address, "end": end,
                            "size": len(payload), "before_sha256": hashlib.sha256(before).hexdigest(),
                            "after_sha256": hashlib.sha256(payload).hexdigest()})

    def allocate(self, name, payload, alignment=4):
        if name in self.allocations:
            raise PatchError(f"Duplicate allocation name: {name}")
        if alignment < 1 or alignment & (alignment-1):
            raise PatchError("Alignment must be a positive power of two")
        payload = bytes(payload)
        if not payload:
            raise PatchError("Cannot allocate an empty payload")
        for i, region in enumerate(self.profile["allocation_ranges"]):
            address = (self.cursors[i]+alignment-1) & ~(alignment-1)
            limit = number(region["end"])
            while address+len(payload) <= limit:
                conflicts = [p for p in self.ledger if address < p["end"] and p["address"] < address+len(payload)]
                if conflicts:
                    address = (max(p["end"] for p in conflicts)+alignment-1) & ~(alignment-1)
                    continue
                self.write(address, payload, "allocation:"+name)
                self.cursors[i] = address+len(payload)
                self.allocations[name] = address
                return address
        raise PatchError(f"Out of declared free space: {name}")

    def write_integer(self, address, value, size, label, expected=None):
        try:
            payload = number(value).to_bytes(size, "little")
        except (OverflowError, ValueError) as error:
            raise PatchError(f"Value does not fit {size} bytes: {label}") from error
        self.write(address, payload, label, expected)

    def output(self, path, input_path=None):
        path = Path(path).resolve()
        if input_path is not None and path == Path(input_path).resolve():
            raise PatchError("Output must not overwrite the original ROM")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.data)
        return {"profile": self.profile["id"], "input_sha256": self.profile["sha256"],
                "output_sha256": hashlib.sha256(self.data).hexdigest(),
                "size": len(self.data), "patches": self.ledger, "allocations": self.allocations}
