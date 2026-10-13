"""Static campaign reachability over existing world-graph observations."""
from collections import deque

from .core import PatchError


def audit_campaign(graph, start, required=()):
    """Report observed routes/returns using unambiguous base-slot edges only.

    Room arguments are stable graph node IDs. Required rooms are independent
    destinations from start, not an ordered itinerary. No ROM IO or mutation.
    Missing routes are observations in this graph, not gameplay softlock proof.
    """
    if graph.get('schema_version') != 1:
        raise PatchError('Campaign audit requires world-graph schema 1')
    nodes, edges = graph['nodes'], graph['edges']
    if len(nodes) > 4096 or len(edges) > 32768:
        raise PatchError('Campaign graph exceeds audit bounds')
    identifiers = [node['id'] for node in nodes]
    if len(set(identifiers)) != len(identifiers):
        raise PatchError('Duplicate campaign room IDs')
    known = set(identifiers)
    if start not in known:
        raise PatchError('Campaign start is outside graph')
    if not isinstance(required, (list, tuple)) or len(required) > 256:
        raise PatchError('Required rooms must be a list/tuple of at most 256 IDs')
    if any(room not in known for room in required):
        raise PatchError('Required campaign room is outside graph')
    if len({edge['id'] for edge in edges}) != len(edges):
        raise PatchError('Duplicate campaign door IDs')
    forward = {room: [] for room in known}
    reverse = {room: [] for room in known}
    excluded = []
    for edge in sorted(edges, key=lambda edge: edge['id']):
        if edge['source'] not in known:
            raise PatchError('Campaign edge source is outside graph')
        targets = edge['targets']
        if (edge['destination_status'] != 'resolved' or len(targets) != 1
                or targets[0] not in known):
            excluded.append({'edge': edge['id'], 'source': edge['source'],
                             'status': edge['destination_status'], 'targets': list(targets)})
            continue
        destination = targets[0]
        forward[edge['source']].append((destination, edge['id']))
        reverse[destination].append((edge['source'], edge['id']))

    def traverse(adjacency):
        parents = {start: None}
        queue = deque([start])
        while queue:
            room = queue.popleft()
            for neighbor, edge in adjacency[room]:
                if neighbor not in parents:
                    parents[neighbor] = (room, edge)
                    queue.append(neighbor)
        return parents

    outward, inward = traverse(forward), traverse(reverse)

    def path(parents, target, returning=False):
        if target not in parents:
            return None
        route = []
        while target != start:
            target, edge = parents[target]
            route.append(edge)
        return route if returning else list(reversed(route))

    requirements = [{'room': room, 'outward_edges': path(outward, room),
                     'return_edges': path(inward, room, returning=True)}
                    for room in dict.fromkeys(required)]
    reachable = set(outward)
    return {'schema_version': 1, 'profile': graph['profile'],
            'image_sha256': graph['image_sha256'], 'start': start,
            'reachable_rooms': sorted(reachable),
            'unreachable_rooms': sorted(known - reachable),
            'reachable_without_observed_return': sorted(reachable - set(inward)),
            'required_routes': requirements, 'excluded_edges': excluded,
            'source_diagnostics': list(graph.get('diagnostics', [])),
            'graph_complete_for_audit': bool(graph.get('enumeration_complete')) and not excluded,
            'all_required_outward_paths_observed': all(r['outward_edges'] is not None for r in requirements),
            'all_required_roundtrips_observed': all(r['outward_edges'] is not None and r['return_edges'] is not None for r in requirements),
            'summary': {'rooms': len(nodes), 'reachable': len(reachable),
                        'unreachable': len(known - reachable),
                        'reachable_without_observed_return': len(reachable - set(inward)),
                        'excluded_edges': len(excluded)},
            'scope': 'static unambiguous base-slot doors; no event/ability/collision gates, alternate states, landing or save/progression certification'}
