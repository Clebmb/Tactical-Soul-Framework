"""Compare explicit observed route samples with an authored progression policy."""
import hashlib
import json
from .campaign_progression import plan_progression
from .core import PatchError


def compare_progression_trace(graph, spec, trace):
    """Read-only, bounded comparison; caller supplies trustworthy observations.

    Samples are settled checkpoints. `via` identifies the single door crossed
    since the previous sample, or None for another checkpoint in the same room.
    Start after any acquisition not modeled as a room-entry grant. This does not
    authenticate native execution, infer missed crossings or certify gate code.
    """
    # Reuse the policy validator without running a potentially large search.
    validated = plan_progression(graph, spec, max_states=1, max_transitions=1)
    if (not isinstance(trace, dict)
            or set(trace) != {'schema_version', 'profile', 'image_sha256', 'samples'}
            or type(trace['schema_version']) is not int or trace['schema_version'] != 1):
        raise PatchError('Progression trace requires schema 1 and exact fields')
    if trace['profile'] != graph['profile'] or trace['image_sha256'] != graph['image_sha256']:
        raise PatchError('Progression trace profile/image mismatch')
    samples = trace['samples']
    if not isinstance(samples, list) or not 1 <= len(samples) <= 4096:
        raise PatchError('Progression trace requires 1..4096 samples')
    rooms = {node['id'] for node in graph['nodes']}
    excluded = {item['edge'] for item in validated['excluded_edges']}
    edges = {edge['id']: edge for edge in graph['edges'] if edge['id'] not in excluded}
    declared = set(spec['flags'])
    for sample in samples:
        if (not isinstance(sample, dict) or set(sample) != {'room', 'flags', 'via'}
                or not isinstance(sample['room'], str) or sample['room'] not in rooms
                or not isinstance(sample['flags'], dict) or set(sample['flags']) != declared
                or any(type(value) is not bool for value in sample['flags'].values())
                or (sample['via'] is not None and
                    (not isinstance(sample['via'], str) or sample['via'] not in edges))):
            raise PatchError('Invalid progression trace sample or unsupported door')
    if samples[0]['via'] is not None:
        raise PatchError('First progression sample cannot have an incoming door')
    violations = []
    expected = set(spec.get('initial_flags', []))
    previous = None
    progress = 0
    itinerary = spec.get('itinerary', [])
    visited = set()
    for index, sample in enumerate(samples):
        room, via = sample['room'], sample['via']
        actual = {flag for flag, owned in sample['flags'].items() if owned}
        arrival = index == 0 or via is not None
        def violation(code, **details):
            violations.append({'sample': index, 'code': code, **details})
        if previous is None:
            if room != spec['start']:
                violation('start_room_mismatch', expected=spec['start'], observed=room)
        elif via is None:
            if room != previous['room']:
                violation('room_change_without_door')
        else:
            edge = edges[via]
            if edge['source'] != previous['room'] or edge['targets'] != [room]:
                violation('door_endpoint_mismatch', edge=via)
            missing = [flag for flag in spec.get('edge_requirements', {}).get(via, [])
                       if not previous['flags'][flag]]
            if missing:
                violation('door_requirement_not_observed', edge=via, missing_flags=sorted(set(missing)))
        if arrival:
            expected.update(spec.get('room_grants', {}).get(room, []))
            if progress < len(itinerary) and room == itinerary[progress]:
                progress += 1
        if actual != expected:
            violation('flag_state_mismatch', missing_flags=sorted(expected - actual),
                      unexpected_flags=sorted(actual - expected))
        visited.add(room)
        previous = sample
    return {'schema_version': 1, 'profile': graph['profile'], 'image_sha256': graph['image_sha256'],
            'policy_sha256': validated['policy_sha256'], 'sample_count': len(samples),
            'trace_sha256': hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(),
            'matches_policy': not violations, 'violations': violations,
            'required_rooms_observed': all(room in visited for room in spec['required_rooms']),
            'itinerary_observed': progress == len(itinerary) if 'itinerary' in spec else None,
            'waypoints_observed': progress, 'graph_complete_for_audit': validated['graph_complete_for_audit'],
            'scope': 'comparison of supplied checkpoints only; no native authenticity or gate-enforcement certification'}
