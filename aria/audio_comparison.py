"""Bounded offline diagnostics; correlation is not native fidelity approval."""
import math

def rms_windows(samples, sample_rate, *, window_seconds=0.02):
    """Return complete RMS windows on a shared seconds grid; drop partial tail."""
    if not isinstance(samples,(list,tuple)) or len(samples)>1000000:
        raise ValueError('samples require a list/tuple of at most one million values')
    for value in (sample_rate,window_seconds):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
            raise ValueError('rate/window must be finite positive numbers')
    step=sample_rate*window_seconds
    if not math.isfinite(step) or step<1 or not 0.001<=window_seconds<=1:
        raise ValueError('window must be 1ms..1s and contain at least one sample')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1000000000 for v in samples):
        raise ValueError('sample values must be finite numbers within signed one billion')
    count=int(len(samples)/step)
    if count>20000:raise ValueError('RMS window budget exceeds 20000')
    result=[]
    for i in range(count):
        start,end=int(i*step),int((i+1)*step)
        result.append(math.sqrt(sum(v*v for v in samples[start:end])/(end-start)))
    return tuple(result)

def align_envelopes(reference, observed, *, max_offset_bins):
    """Best nonnegative full-window Pearson alignment, earliest offset on ties.

    Inputs must share a time grid. No time stretching, negative offsets or
    confidence threshold is implied; callers assess ambiguity and drift.
    """
    if type(max_offset_bins) is not int or not 0<=max_offset_bins<=20000:
        raise ValueError('max offset must be an integer in 0..20000')
    for values in (reference,observed):
        if not isinstance(values,(tuple,list)) or not 3<=len(values)<=20000 or any(
                isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1000000000 for v in values):
            raise ValueError('envelopes require 3..20000 finite nonnegative levels')
    if len(observed)>len(reference):raise ValueError('observed envelope exceeds reference')
    last=min(max_offset_bins,len(reference)-len(observed))
    if (last+1)*len(observed)>2000000:raise ValueError('alignment exceeds two million comparisons')
    mean=sum(observed)/len(observed);centered=[v-mean for v in observed]
    energy=sum(v*v for v in centered)
    if energy==0:raise ValueError('observed envelope has no variation')
    scores=[]
    for offset in range(last+1):
        window=reference[offset:offset+len(observed)];average=sum(window)/len(window)
        variance=sum((v-average)**2 for v in window)
        if variance==0:continue
        score=sum((v-average)*w for v,w in zip(window,centered))/math.sqrt(variance*energy)
        scores.append((max(-1.0,min(1.0,score)),offset))
    if not scores:raise ValueError('reference windows have no variation')
    scores.sort(key=lambda item:(-item[0],item[1]))
    best,offset=scores[0]
    return {'offset_bins':offset,'correlation':best,'candidate_count':len(scores),
            'runner_up_correlation':scores[1][0] if len(scores)>1 else None}
