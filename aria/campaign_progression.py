"""Authored monotone progression policies; no native event bindings or writes."""
from collections import deque
import hashlib
import json
import re

from .campaign_audit import audit_campaign
from .core import PatchError


def plan_progression(graph, spec, *, max_states=20000, max_transitions=200000):
    """Explore (room, acquired flags, itinerary progress) with shortest witnesses.

    Grants occur automatically on room entry, including start. Door requirements
    are AND conditions. Flags never clear or consume. All semantics are authored
    declarations, not inferred game events. Budget exhaustion yields a partial
    report and never certifies a missing route.
    """
    required_fields = {'schema_version', 'profile', 'image_sha256', 'start', 'flags', 'required_rooms'}
    optional = {'initial_flags', 'room_grants', 'edge_requirements', 'itinerary'}
    if not isinstance(spec, dict) or not required_fields <= set(spec) or set(spec) - required_fields - optional:
        raise PatchError('Progression policy has missing or unknown fields')
    if type(spec['schema_version']) is not int or spec['schema_version'] != 1:
        raise PatchError('Progression policy requires schema 1')
    if spec['profile'] != graph['profile'] or spec['image_sha256'] != graph['image_sha256']:
        raise PatchError('Progression policy profile/image hash mismatch')
    for value, bound in ((max_states, 100000), (max_transitions, 1000000)):
        if type(value) is not int or not 1 <= value <= bound:
            raise PatchError('Progression search budget outside supported bounds')
    flags = spec['flags']
    if (not isinstance(flags, list) or len(flags) > 16
            or any(not isinstance(flag, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', flag) for flag in flags)
            or len(set(flags)) != len(flags)):
        raise PatchError('Policy flags require at most 16 unique lowercase names')
    bits = {flag: 1 << index for index, flag in enumerate(flags)}

    def mask(names):
        if not isinstance(names, list) or any(not isinstance(name, str) or name not in bits for name in names):
            raise PatchError('Policy references an undeclared flag')
        return sum(bits[name] for name in set(names))

    baseline = audit_campaign(graph, spec['start'], spec['required_rooms'])
    rooms = {node['id'] for node in graph['nodes']}
    itinerary = spec.get('itinerary', [])
    if (not isinstance(itinerary, list) or len(itinerary) > 64
            or any(not isinstance(room, str) or room not in rooms for room in itinerary)):
        raise PatchError('Itinerary requires at most 64 known room IDs')
    excluded = {edge['edge'] for edge in baseline['excluded_edges']}
    edges = {edge['id']: edge for edge in graph['edges'] if edge['id'] not in excluded}

    def rules(field, identifiers):
        mapping = spec.get(field, {})
        if not isinstance(mapping, dict) or any(name not in identifiers for name in mapping):
            raise PatchError('Unknown or unsupported target in ' + field)
        return {name: mask(values) for name, values in mapping.items()}

    grants = rules('room_grants', rooms)
    gates = rules('edge_requirements', edges)
    initial = mask(spec.get('initial_flags', [])) | grants.get(spec['start'], 0)
    adjacency = {room: [] for room in rooms}
    for ident in sorted(edges):
        edge = edges[ident]
        adjacency[edge['source']].append((edge['targets'][0], ident))
    def advance(room, progress):
        # One waypoint per arrival, including initial occupancy. Repeated rooms
        # require another door crossing into that room (a self-loop qualifies).
        return progress + int(progress < len(itinerary) and room == itinerary[progress])

    start = (spec['start'], initial, advance(spec['start'], 0))
    parents = {start: None}
    queue = deque([start])
    first = {spec['start']: start}
    blocked, traversable = {}, set()
    transitions = 0
    limit = None
    itinerary_goal = start if start[2] == len(itinerary) else None
    while queue and limit is None:
        state = queue.popleft()
        room, owned, progress = state
        for destination, ident in adjacency[room]:
            if transitions >= max_transitions:
                limit = 'max_transitions'
                break
            transitions += 1
            missing = gates.get(ident, 0) & ~owned
            if missing:
                blocked[ident] = blocked.get(ident, 0) | missing
                continue
            traversable.add(ident)
            target = (destination, owned | grants.get(destination, 0), advance(destination, progress))
            if target in parents:
                continue
            if len(parents) >= max_states:
                limit = 'max_states'
                break
            parents[target] = (state, ident)
            if itinerary_goal is None and target[2] == len(itinerary):
                itinerary_goal = target
            first.setdefault(destination, target)
            queue.append(target)

    def names(value):
        return [flag for flag in flags if value & bits[flag]]

    def witness_state(state):
        arrival = state[1]
        path = []
        while parents[state] is not None:
            state, ident = parents[state]
            path.append(ident)
        return list(reversed(path)), names(arrival)

    def witness(room):
        state = first.get(room)
        if state is None:
            return {'room': room, 'status': 'not_reached_before_limit' if limit else 'not_observed',
                    'door_path': None, 'flags_on_arrival': None}
        path, arrival = witness_state(state)
        return {'room': room, 'status': 'observed', 'door_path': path,
                'flags_on_arrival': arrival}

    itinerary_result = None
    if 'itinerary' in spec:
        path, arrival = witness_state(itinerary_goal) if itinerary_goal is not None else (None, None)
        itinerary_result = {'rooms': list(itinerary),
                            'status': 'observed' if itinerary_goal is not None else
                                      ('not_reached_before_limit' if limit else 'not_observed'),
                            'door_path': path, 'flags_on_arrival': arrival,
                            'waypoints_observed': max(state[2] for state in parents)}

    return {'schema_version': 1, 'profile': graph['profile'], 'image_sha256': graph['image_sha256'],
            'policy_sha256': hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(),
            'start': spec['start'], 'search_complete': limit is None, 'limit_reached': limit,
            'graph_complete_for_audit': baseline['graph_complete_for_audit'],
            'states_explored': len(parents), 'transitions_examined': transitions,
            'reachable_rooms': sorted(first), 'rooms_not_observed': sorted(rooms - set(first)),
            'required_routes': [witness(room) for room in dict.fromkeys(spec['required_rooms'])],
            'all_required_paths_observed': all(room in first for room in spec['required_rooms']),
            'itinerary_route': itinerary_result,
            'gate_observations': [{'edge': ident, 'missing_flags_observed': names(blocked[ident]),
                                   'traversable_in_some_state': ident in traversable} for ident in sorted(blocked)],
            'excluded_edges': baseline['excluded_edges'], 'source_diagnostics': baseline['source_diagnostics'],
            'scope': 'authored monotone room-entry flags and AND door gates only; no native event enforcement, collision, landing, save or progression certification'}
