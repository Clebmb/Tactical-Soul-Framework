"""One verified after-update Thumb callback, built from original project code.

Not a generic detour generator. The wrapper ABI is exact-version-specific.
Callbacks must be linked at callback_origin, return normally, and own their RAM.
"""
from pathlib import Path
from .core import PatchError, number
ROOT=Path(__file__).resolve().parents[1]

def install_frame_hook(rom, payload, linked_address):
    spec=rom.profile["frame_hook"]
    origin=number(spec["callback_origin"])
    if number(linked_address)!=origin:
        raise PatchError(f"Frame callback must be linked at {origin:#x}")
    address=rom.allocate("frame-callback",payload)
    if address!=origin:
        raise PatchError("Install the frame hook before other allocations")
    wrapper=(ROOT/spec["template_wrapper"]).read_bytes()
    old=number(spec["template_callback_thumb"]).to_bytes(4,"little")
    if len(wrapper)!=48 or wrapper.count(old)!=1:
        raise PatchError("Unexpected wrapper template; regenerate and review its ABI")
    wrapper=wrapper.replace(old,(origin|1).to_bytes(4,"little"))
    entry=(ROOT/spec["template_entry"]).read_bytes()
    if len(entry)!=8:
        raise PatchError("Unexpected entry trampoline size")
    entry_address=number(spec["entry"])
    offset=rom.offset(entry_address,8)
    rom.write(spec["wrapper"],wrapper,"after-update-wrapper")
    rom.write(entry_address,entry,"after-update-entry",rom.original[offset:offset+8])
    return address
