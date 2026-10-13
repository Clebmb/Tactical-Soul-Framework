"""Checked finite boot melody with original synthesized PCM; exact-host only."""
import copy,math,struct
from pathlib import Path
from .content import decode_pcm_wav,local
from .core import PatchError,number
from .audio import NOTE_LENGTHS

BOOT_ENTRY=0x0827CD40+26*8
BOOT_HEADER=0x0848E7B8
DEFAULT_ENVELOPE={'attack':255,'decay':240,'sustain':180,'release':200}

def plan_envelope(value):
    """Checked sampled ToneData bytes; release255 is excluded conservatively."""
    if not isinstance(value,dict) or set(value)!=set(DEFAULT_ENVELOPE):
        raise PatchError('envelope requires attack, decay, sustain and release')
    result={key:number(value[key]) for key in DEFAULT_ENVELOPE}
    if (not 1<=result['attack']<=255 or not 0<=result['decay']<=255
            or not 0<=result['sustain']<=255 or not 0<=result['release']<=254):
        raise PatchError('envelope requires attack1..255, decay/sustain0..255, release0..254')
    return result


def plan_boot_melody(value):
    if isinstance(value,dict) and 'tracks' in value:
        if (not {'tempo','volume','tracks'}<=set(value)
                or set(value)-{'tempo','volume','tracks','repeats','sample','instruments','envelope'}):
            raise PatchError('tracks replaces notes; shared tempo, volume and instruments required')
        tracks=value['tracks']
        if not isinstance(tracks,list) or not 1<=len(tracks)<=4:
            raise PatchError('melody requires1..4 simultaneous tracks')
        normalized=[];first=None
        # Reuse the single-track contract, including shared-bank selection checks.
        for track in tracks:
            if not isinstance(track,dict) or 'notes' not in track or set(track)-{'notes','volume'}:
                raise PatchError('track requires notes and optional volume')
            child={k:v for k,v in value.items() if k!='tracks'}
            child.update(track);plan=plan_boot_melody(child)
            if first is None:first=plan
            normalized.append({k:plan[k] for k in ('notes','volume','ticks','total_ticks')})
        if sum(len(t['notes']) for t in normalized)>128 or sum(t['total_ticks'] for t in normalized)>12288:
            raise PatchError('tracks exceed128 steps or12288 expanded aggregate ticks')
        # Validate the global volume even when every track overrides it.
        volume=number(value['volume'])
        if not 0<=volume<=100:raise PatchError('melody volume0..100 required')
        result={k:v for k,v in first.items() if k not in ('notes','ticks','total_ticks','volume')}
        result.update(volume=volume,tracks=normalized,ticks=max(t['ticks'] for t in normalized),
                      total_ticks=max(t['total_ticks'] for t in normalized),max_gated_notes=len(tracks))
        return result
    if (not isinstance(value,dict) or not {'tempo','volume','notes'}<=set(value)
            or set(value)-{'tempo','volume','notes','repeats','sample','instruments','envelope'}):
        raise PatchError('boot_melody requires tempo, volume and notes')
    tempo,volume=number(value['tempo']),number(value['volume'])
    if not 30<=tempo<=120 or not 0<=volume<=100:
        raise PatchError('melody tempo30..120 and volume0..100 required')
    notes=value['notes']
    if not isinstance(notes,list) or not 1<=len(notes)<=64:
        raise PatchError('melody requires 1..64 note/rest steps')
    result=[];ticks=0
    for note in notes:
        if isinstance(note,dict) and set(note)=={'rest'}:
            length=number(note['rest'])
            if length not in NOTE_LENGTHS:raise PatchError('rest requires registered tick length')
            ticks+=length;result.append({'rest':length});continue
        if (not isinstance(note,dict) or not {'key','velocity','ticks'}<=set(note)
                or set(note)-{'key','velocity','ticks','gate_ticks','instrument'}):
            raise PatchError('melody notes require key, velocity and ticks')
        key,velocity,length=(number(note[k]) for k in ('key','velocity','ticks'))
        if not 48<=key<=84 or not 1<=velocity<=100 or length not in NOTE_LENGTHS:
            raise PatchError('melody note outside key48..84, velocity1..100 or registered tick lengths')
        normalized={'key':key,'velocity':velocity,'ticks':length}
        if 'gate_ticks' in note:
            gate=number(note['gate_ticks'])
            if gate not in NOTE_LENGTHS or gate>length:
                raise PatchError('gate_ticks requires registered length no greater than ticks')
            normalized['gate_ticks']=gate
        if 'instrument' in note:normalized['instrument']=number(note['instrument'])
        ticks+=length;result.append(normalized)
    if not any('key' in step for step in result):raise PatchError('melody requires at least one note')
    if ticks>1536:raise PatchError('melody exceeds1536 ticks')
    repeats=number(value.get('repeats',1))
    if not 1<=repeats<=8 or ticks*repeats>6144:
        raise PatchError('melody repeats require1..8 passes and at most6144 total ticks')
    plan={'tempo':tempo,'volume':volume,'notes':result,'ticks':ticks,'repeats':repeats,'total_ticks':ticks*repeats}
    if 'envelope' in value:plan['envelope']=plan_envelope(value['envelope'])
    if 'sample' in value and 'instruments' in value:raise PatchError('sample and instruments are mutually exclusive')
    specs=value.get('instruments',[value['sample']] if 'sample' in value else [])
    if 'instruments' in value and (not isinstance(specs,list) or not 1<=len(specs)<=8):
        raise PatchError('instruments requires1..8 original WAV specifications')
    normalized_specs=[]
    for spec in specs:
        if (not isinstance(spec,dict) or not {'source','provenance','loop_start'}<=set(spec)
                or set(spec)-{'source','provenance','loop_start','envelope'}):
            raise PatchError('sample requires source, provenance and explicit loop_start')
        if not isinstance(spec['source'],str) or not spec['source'] or Path(spec['source']).is_absolute():
            raise PatchError('sample source must be a nonempty relative path')
        if not isinstance(spec['provenance'],str) or not spec['provenance'].strip():
            raise PatchError('sample provenance required')
        loop=None if spec['loop_start'] is None else number(spec['loop_start'])
        if loop is not None and not 0<=loop<32768:raise PatchError('sample loop index outside bounds')
        normalized=dict(spec,loop_start=loop)
        if 'envelope' in spec:normalized['envelope']=plan_envelope(spec['envelope'])
        normalized_specs.append(normalized)
    if 'sample' in value:plan['sample_source']=normalized_specs[0]
    if 'instruments' in value:plan['instruments']=normalized_specs
    for note in result:
        if 'instrument' in note and not 0<=note['instrument']<max(1,len(normalized_specs)):
            raise PatchError('note instrument outside declared bank')
    return plan

def install_boot_melody(rom,value,folder=None):
    """Transactionally allocate sample, voice, track/header then repoint slot26."""
    plan=plan_boot_melody(value)
    if rom.profile['id']!='aos-usa-r0':raise PatchError('boot melody requires registered exact host')
    expected=BOOT_HEADER.to_bytes(4,'little')
    if rom.read(BOOT_ENTRY,4)!=expected or rom.original[rom.offset(BOOT_ENTRY,4):rom.offset(BOOT_ENTRY,4)+4]!=expected:
        raise PatchError('boot song pointer precondition mismatch')
    staged=copy.deepcopy(rom)
    specs=plan.get('instruments',[plan.get('sample_source')])
    samples=[];voices=bytearray();instrument_reports=[];total_pcm=0
    for index,spec in enumerate(specs):
        pcm=bytes(round(64*math.sin(2*math.pi*i/40))&255 for i in range(40))
        rate,loop,source_report=10512,0,{}
        if spec is not None:
            if folder is None:raise PatchError('imported sample requires manifest folder')
            path=local(Path(folder),spec['source'])
            if path.stat().st_size>131072:raise PatchError('WAV source exceeds128KiB')
            decoded=decode_pcm_wav(path.read_bytes());pcm=decoded['pcm'];rate=decoded['sample_rate'];loop=spec['loop_start']
            if loop is not None and loop>=len(pcm):raise PatchError('sample loop must index decoded PCM')
            source_report={k:v for k,v in decoded.items() if k!='pcm'}
        total_pcm+=len(pcm)
        if total_pcm>65536:raise PatchError('instrument bank exceeds65536 decoded PCM bytes')
        label='music:boot:sample'+(':'+str(index) if index else '')
        sample=staged.allocate(label,struct.pack('<HHIII',0,0x4000 if loop is not None else 0,rate*1024,loop or 0,len(pcm))+pcm,4)
        samples.append(sample)
        envelope=plan.get('envelope',DEFAULT_ENVELOPE)
        if spec is not None:envelope=spec.get('envelope',envelope)
        voices.extend(bytes([0,60,0,0])+struct.pack('<I',sample)+bytes(envelope[k] for k in DEFAULT_ENVELOPE))
        instrument_reports.append(dict(imported_sample=source_report,sample_rate=rate,loop_start=loop,sample=sample,pcm_samples=len(pcm),envelope=dict(envelope)))
    voice=staged.allocate('music:boot:voice',voices,4)
    track_addresses=[]
    track_plans=plan.get('tracks',[plan])
    for track_index,track_plan in enumerate(track_plans):
        track=bytearray([0xBC,0,0xBB,plan['tempo'],0xBD,0,0xBE,track_plan['volume'],0xBF,64])
        active_instrument=0
        for note in track_plan['notes'] * plan['repeats']:
            if 'rest' in note:
                track.append(0x81+NOTE_LENGTHS.index(note['rest']));continue
            selected=note.get('instrument',0)
            if selected!=active_instrument:
                track.extend((0xBD,selected));active_instrument=selected
            index=NOTE_LENGTHS.index(note['ticks'])
            gate=NOTE_LENGTHS.index(note.get('gate_ticks',note['ticks']))
            track.extend((0xD0+gate,note['key'],note['velocity'],0x81+index))
        track.append(0xB1)
        track_address=staged.allocate('music:boot:track'+(':'+str(track_index) if track_index else ''),track,4)
        track_addresses.append(track_address)
    header=staged.allocate('music:boot:header',bytes([len(track_addresses),0,0,0])+struct.pack('<I',voice)+b''.join(struct.pack('<I',address) for address in track_addresses),4)
    staged.write(BOOT_ENTRY,struct.pack('<I',header),'music:boot:pointer',expected)
    report=dict(plan,header=header,track=track_addresses[0],voice=voice,scope='finite bounded boot slot26 melody; no infinite loop or gameplay binding')
    report.update(instrument_reports[0])
    if 'instruments' in plan:report['instrument_bank']=instrument_reports
    if 'tracks' in plan:report['track_addresses']=track_addresses
    staged.music_report=report
    rom.__dict__.clear();rom.__dict__.update(staged.__dict__)
    return report
