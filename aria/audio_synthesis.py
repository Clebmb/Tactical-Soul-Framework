"""Source-derived MP2k sampled ADSR model; not an Aria-native certification.

See docs/AUDIO-RECON.md for provenance and omissions. No ROM IO or writes.
"""

import math
from bisect import bisect_right
from .audio import ticks_to_seconds


def gate_tied_events(events, *, final_tick):
    """Convert a bounded scheduled track's ties/releases to finite note gates.

    Diagnostic policy: release stops the newest still-active matching key,
    including finite notes; unclosed ties stop at end/loop or final_tick.
    Controllers retain execution order. This does not model native channel
    stealing or the difference between a hard track stop and an ADSR release.
    Input must be an indexed sequence of at most 20,000 scheduler events.
    """
    if type(final_tick) is not int or not 0 <= final_tick <= 1_000_000_000:
        raise ValueError("final tick must be an integer in 0..1000000000")
    if not isinstance(events, (tuple, list)) or len(events) > 20000:
        raise ValueError("events must be a bounded list or tuple")
    output, active = [], {}
    previous = 0
    for tick, event in events:
        if type(tick) is not int or not previous <= tick <= final_tick:
            raise ValueError("event ticks must be ordered within final tick")
        previous = tick
        kind = event[0]
        if kind in ('note', 'tie'):
            key, velocity, voice = event[1:4]
            length = event[4] if kind == 'note' else final_tick - tick
            if type(length) is not int or length < 0:
                raise ValueError("note length must be nonnegative")
            active.setdefault(key, []).append(len(output))
            output.append((tick, ('note', key, velocity, voice, length)))
        elif kind == 'release':
            candidates = active.get(event[1], [])
            while candidates:
                index = candidates.pop()
                start, note = output[index]
                if start + note[4] <= tick:
                    continue
                output[index] = (start, note[:4] + (tick - start,))
                break
        elif kind in ('end', 'loop'):
            for candidates in active.values():
                for index in candidates:
                    start, note = output[index]
                    output[index] = (start, note[:4] + (min(note[4], tick - start),))
            active.clear()
            output.append((tick, event))
        else:
            output.append((tick, event))
    return tuple(output)


def sampled_envelope(attack, decay, sustain, release, *, gate_frames, frames):
    """Return bounded integer levels (0..255), one per mixer update.

    Attack adds a byte, decay/release multiply then shift right eight,
    and sustain clamps decay. Frame zero applies the first attack step.
    Release starts at gate_frames, including during attack/decay. A zero
    gate cancels before startup. Caller supplies the mixer-update clock;
    musical ticks are not frames. Pseudo echo, sample exhaustion, channel
    stealing, PSG envelopes and hardware timing are outside this model.
    """
    for value in (attack, decay, sustain, release):
        if type(value) is not int or not 0 <= value <= 255:
            raise ValueError("ADSR values must be integer bytes")
    for value in (gate_frames, frames):
        if type(value) is not int or not 0 <= value <= 1_000_000:
            raise ValueError("frame counts must be integers in 0..1000000")
    level = 0
    phase = "attack"
    result = []
    for frame in range(frames):
        if frame >= gate_frames:
            level = (level * release) >> 8
        elif phase == "attack":
            level = min(255, level + attack)
            if level == 255:
                phase = "decay"
        elif phase == "decay":
            level = max(sustain, (level * decay) >> 8)
            if level == sustain:
                phase = "sustain"
        result.append(level)
    return tuple(result)


def render_sample(pcm, source_rate, *, output_rate, frames, loop_start=None,
                  envelope=None, envelope_rate=60):
    """Linearly resample signed 8-bit PCM, returning immutable float levels.

    PCM uses GBA signed bytes, not WAV's unsigned encoding. Loop start is a
    sample index; interpolation wraps the loop seam. One-shots hold the last
    sample to its next source boundary, then emit silence. Optional envelope
    contains 0..255 levels indexed by mixer updates, holding each update;
    exhausted envelope emits silence. This diagnostic renderer does not model
    native mixer quantization, channel allocation or hardware filtering.
    """
    if not isinstance(pcm, bytes) or not pcm:
        raise ValueError("PCM must be nonempty immutable bytes")
    for value in (source_rate, output_rate, envelope_rate):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0):
            raise ValueError("rates must be finite positive numbers")
    if type(frames) is not int or not 0 <= frames <= 1_000_000:
        raise ValueError("frames must be an integer in 0..1000000")
    if loop_start is not None and (type(loop_start) is not int
                                  or not 0 <= loop_start < len(pcm)):
        raise ValueError("loop start must index PCM")
    if envelope is not None:
        if not isinstance(envelope, (tuple, list)) or any(
                type(v) is not int or not 0 <= v <= 255 for v in envelope):
            raise ValueError("envelope must contain byte levels")
    step = source_rate / output_rate
    envelope_step = envelope_rate / output_rate
    if not math.isfinite(step * frames) or not math.isfinite(envelope_step * frames):
        raise ValueError("source position exceeds finite range")
    size = len(pcm)

    def signed(index):
        value = pcm[index]
        return value if value < 128 else value - 256

    result = []
    for frame in range(frames):
        position = frame * step
        if position >= size:
            if loop_start is None:
                result.append(0.0)
                continue
            position = loop_start + (position - size) % (size - loop_start)
        index = int(position)
        following = index + 1
        if following == size:
            following = index if loop_start is None else loop_start
        value = signed(index) + (signed(following) - signed(index)) * (position - index)
        if envelope is not None:
            update = int(frame * envelope_step)
            value *= envelope[update] / 255 if update < len(envelope) else 0
        result.append(value)
    return tuple(result)


class TempoMap:
    """Shared diagnostic clock compiled from bounded track schedules.

    Same-tick tempo commands execute by track index then event order; the last
    wins. Tempo zero is rejected, rather than silently ignored. Uses the
    existing reference tick clock, not certified Aria driver timing.
    """
    __slots__ = ('_segments', '_ticks', '_frame_scale')

    def __init__(self, schedules, *, initial_tempo=75, frame_rate=60):
        if (isinstance(frame_rate, bool) or not isinstance(frame_rate, (int, float))
                or not math.isfinite(frame_rate) or not 1 <= frame_rate <= 1000):
            raise ValueError('frame rate must be finite in 1..1000 Hz')
        self._frame_scale = 60 / frame_rate
        if type(initial_tempo) is not int or not 1 <= initial_tempo <= 255:
            raise ValueError('initial tempo must be an integer in 1..255')
        if not isinstance(schedules, (tuple, list)) or len(schedules) > 16:
            raise ValueError('schedules must contain at most 16 tracks')
        changes = []
        total = 0
        for track, schedule in enumerate(schedules):
            if not isinstance(schedule, (tuple, list)):
                raise ValueError('each schedule must be a list or tuple')
            total += len(schedule)
            if total > 20000:
                raise ValueError('tempo map exceeds 20000 events')
            previous = 0
            for order, item in enumerate(schedule):
                if not isinstance(item, (tuple, list)) or len(item) != 2:
                    raise ValueError('expected tick/event pairs')
                tick, event = item
                if type(tick) is not int or not previous <= tick <= 1000000000:
                    raise ValueError('track ticks must be ordered in 0..1000000000')
                previous = tick
                if not isinstance(event, (tuple, list)) or not event:
                    raise ValueError('expected nonempty event tuples')
                if event[0] == 'tempo':
                    if len(event) != 2 or type(event[1]) is not int or not 1 <= event[1] <= 255:
                        raise ValueError('tempo must be an integer in 1..255')
                    changes.append((tick, track, order, event[1]))
        segments = [(0, 0.0, initial_tempo)]
        for tick, _, _, tempo in sorted(changes):
            previous, seconds, old_tempo = segments[-1]
            segment = (tick, seconds + ticks_to_seconds(tick - previous, old_tempo) * self._frame_scale, tempo)
            if tick == previous:
                segments[-1] = segment
            else:
                segments.append(segment)
        self._segments = tuple(segments)
        self._ticks = tuple(s[0] for s in segments)

    def seconds_at(self, tick):
        """Integrate to a nonnegative bounded integer tick, with extrapolation."""
        if type(tick) is not int or not 0 <= tick <= 1000000000:
            raise ValueError('tick must be an integer in 0..1000000000')
        start, seconds, tempo = self._segments[bisect_right(self._ticks, tick) - 1]
        return seconds + ticks_to_seconds(tick - start, tempo) * self._frame_scale

    def duration(self, start_tick, end_tick):
        """Elapsed seconds across tempo changes; endpoints are absolute ticks."""
        start = self.seconds_at(start_tick)
        end = self.seconds_at(end_tick)
        if end_tick < start_tick:
            raise ValueError('end tick precedes start tick')
        return end - start
