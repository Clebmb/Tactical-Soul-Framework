"""Small local libretro test driver. Never downloads or distributes game data."""
import ctypes as C
import hashlib
from dataclasses import dataclass
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]

class MemoryDescriptor(C.Structure):
    _fields_ = [('flags',C.c_uint64),('ptr',C.c_void_p),('offset',C.c_size_t),('start',C.c_size_t),('select',C.c_size_t),('disconnect',C.c_size_t),('len',C.c_size_t),('addrspace',C.c_char_p)]
class MemoryMap(C.Structure):
    _fields_ = [('descriptors',C.POINTER(MemoryDescriptor)),('num_descriptors',C.c_uint)]

@dataclass(frozen=True)
class NativeCheckpoint:
    """Private in-memory core state; valid only in its capturing emulator."""
    owner: object
    rom_sha256: str
    payload: bytes

class Emulator:
    def __init__(self, rom):
        self.lib = C.CDLL(str(ROOT / 'tools/libretro/mgba_libretro.dll'))
        self._checkpoint_owner = object()
        self._closed = False
        self.keys = set()
        self.image = None
        self.pixel_format = 0
        self.maps=[]
        self.directory = str(ROOT / 'local').encode()
        (ROOT / 'local').mkdir(exist_ok=True)
        def env(cmd, ptr):
            cmd &= 0xFFFF
            if cmd == 10:
                self.pixel_format = C.cast(ptr, C.POINTER(C.c_uint))[0]
                return True
            if cmd in (9, 31):
                C.cast(ptr, C.POINTER(C.c_char_p))[0] = self.directory
                return True
            if cmd == 15:  # no core-variable overrides
                return False
            if cmd == 17:
                C.cast(ptr, C.POINTER(C.c_bool))[0] = False
                return True
            if cmd == 36:
                mmap=C.cast(ptr,C.POINTER(MemoryMap)).contents
                self.maps=[(d.start,d.len,d.ptr,d.offset) for d in mmap.descriptors[:mmap.num_descriptors]]
                return True
            if cmd in (18, 35):
                return True
            return False
        def video(ptr, w, h, pitch):
            if not ptr:
                return
            raw = C.string_at(ptr, pitch*h)
            if self.pixel_format == 1:
                self.image = Image.frombytes('RGB', (w,h), raw, 'raw', 'BGRX', pitch)
            else:
                self.image = Image.frombytes('RGB', (w,h), raw, 'raw', 'BGR;16', pitch)
        self.callbacks = [ENV(env), VIDEO(video), AUDIO(lambda a,b: None), BATCH(lambda p,n:n), POLL(lambda:None), INPUT(lambda p,d,i,k: int(k in self.keys))]
        for name, cb in zip(('environment','video_refresh','audio_sample','audio_sample_batch','input_poll','input_state'), self.callbacks):
            getattr(self.lib, 'retro_set_'+name)(cb)
        self.lib.retro_get_memory_data.restype = C.c_void_p
        self.lib.retro_get_memory_size.restype = C.c_size_t
        self.lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        self.lib.retro_load_game.restype = C.c_bool
        self.lib.retro_init()
        rom = Path(rom).resolve()
        self.rom_data = C.create_string_buffer(rom.read_bytes())
        self.rom_sha256 = hashlib.sha256(self.rom_data.raw[:-1]).hexdigest()
        self.info = GameInfo(str(rom).encode(), C.cast(self.rom_data,C.c_void_p), len(self.rom_data)-1, None)
        if not self.lib.retro_load_game(C.byref(self.info)):
            raise RuntimeError('mGBA could not load ROM')
        self.ram = self.lib.retro_get_memory_data(2)
        if not self.ram:
            raise RuntimeError('No system RAM exposed')
    def read(self, address, size=4):
        return int.from_bytes(self.bytes(address,size),'little')
    def bytes(self,address,size):
        for start,length,ptr,offset in self.maps:
            if start<=address and address+size<=start+length and ptr:
                return C.string_at(ptr+offset+address-start,size)
        if 0x02000000<=address<0x02040000:
            return C.string_at(self.ram+address-0x02000000,size)
        raise ValueError(hex(address))
    def write(self, address, value, size=4):
        for start,length,ptr,offset in self.maps:
            if start<=address and address+size<=start+length and ptr:
                C.memmove(ptr+offset+address-start,value.to_bytes(size,'little'),size)
                return
        raise ValueError(hex(address))
    def run(self, frames, keys=()):
        self.keys=set(keys)
        for _ in range(frames): self.lib.retro_run()
    def snap(self, name):
        path=ROOT/'local'/name
        self.image.save(path)
        return path
    def capture_state(self):
        """Capture bounded native state for replay forks; never write a file."""
        if self._closed:raise RuntimeError('Emulator is closed')
        self.lib.retro_serialize_size.restype=C.c_size_t
        self.lib.retro_serialize.argtypes=[C.c_void_p,C.c_size_t]
        self.lib.retro_serialize.restype=C.c_bool
        size=self.lib.retro_serialize_size()
        if not 0<size<=16*1024*1024:raise RuntimeError('Unsupported native checkpoint size')
        payload=C.create_string_buffer(size)
        if not self.lib.retro_serialize(payload,size):raise RuntimeError('Native checkpoint capture failed')
        return NativeCheckpoint(self._checkpoint_owner,self.rom_sha256,payload.raw)
    def restore_state(self, checkpoint):
        """Restore only this instance's state; the next run refreshes video."""
        if self._closed:raise RuntimeError('Emulator is closed')
        if not isinstance(checkpoint,NativeCheckpoint) or checkpoint.owner is not self._checkpoint_owner or checkpoint.rom_sha256!=self.rom_sha256:
            raise RuntimeError('Checkpoint belongs to another emulator or ROM')
        self.lib.retro_serialize_size.restype=C.c_size_t
        size=self.lib.retro_serialize_size()
        if not 0<size<=16*1024*1024 or len(checkpoint.payload)!=size:
            raise RuntimeError('Native checkpoint size mismatch')
        self.lib.retro_unserialize.argtypes=[C.c_void_p,C.c_size_t]
        self.lib.retro_unserialize.restype=C.c_bool
        payload=C.create_string_buffer(checkpoint.payload,len(checkpoint.payload))
        if not self.lib.retro_unserialize(payload,size):raise RuntimeError('Native checkpoint restore failed')
        self.keys=set();self.image=None
    def close(self):
        self._closed=True
        self.lib.retro_unload_game()
        self.lib.retro_deinit()

if __name__ == '__main__':
    import sys
    e=Emulator(sys.argv[1] if len(sys.argv)>1 else ROOT/'CastlevaniaAoS.gba')
    e.run(240)
    print('State:', e.read(0x02000010,1), 'Screenshot:', e.snap('baseline.png'))
    e.close()
