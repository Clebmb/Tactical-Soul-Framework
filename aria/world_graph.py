"""Static base-slot door graph and before/after routing observations."""
import hashlib
from .core import PatchError
from .rooms import sector_span,room_address,doors
from .room_catalog import room_id


def audit_world_graph(rom):
    nodes=[];edges=[];diagnostics=[];by_address={}
    for sector in range(12):
        try:_,count=sector_span(rom,sector)
        except PatchError as error:
            diagnostics.append({'code':'sector_unavailable','sector':sector,'message':str(error)});continue
        for index in range(count):
            try:
                address=room_address(rom,sector,index);ident=room_id(rom.profile['id'],sector,index)
                nodes.append({'id':ident,'sector':sector,'room':index,'address':address})
                by_address.setdefault(address,[]).append(ident)
            except PatchError as error:diagnostics.append({'code':'room_unavailable','sector':sector,'room':index,'message':str(error)})
    for node in nodes:
        try:rows=doors(rom,node['address'])
        except PatchError as error:
            diagnostics.append({'code':'doors_unavailable','id':node['id'],'message':str(error)});continue
        for index,door in enumerate(rows):
            targets=by_address.get(door.destination,[])
            edges.append({'id':node['id']+f':door:{index:03d}','source':node['id'],'door':index,
                          'source_address':node['address'],'destination_address':door.destination,
                          'targets':targets,'destination_status':'resolved' if len(targets)==1 else 'aliased' if targets else 'outside_base_catalog',
                          'boundary':[door.x,door.y],'spawn':[door.dest_x,door.dest_y],
                          'secondary_spawn':[door.dest_x_2,door.dest_y_2]})
    pairs={(e['source_address'],e['destination_address']) for e in edges}
    incoming={node['id']:[] for node in nodes};outgoing={node['id']:[] for node in nodes}
    for edge in edges:
        edge['direct_return_observed']=(edge['destination_address'],edge['source_address']) in pairs
        outgoing[edge['source']].append(edge['id'])
        for target in edge['targets']:incoming[target].append(edge['id'])
    for node in nodes:node.update({'incoming_edges':incoming[node['id']],'outgoing_edges':outgoing[node['id']]})
    return {'schema_version':1,'profile':rom.profile['id'],'image_sha256':hashlib.sha256(rom.data).hexdigest(),
            'nodes':nodes,'edges':edges,'diagnostics':diagnostics,'enumeration_complete':not diagnostics,
            'summary':{'rooms':len(nodes),'doors':len(edges),'unresolved_destinations':sum(not e['targets'] for e in edges),
                       'edges_without_observed_direct_return':sum(not e['direct_return_observed'] for e in edges)},
            'scope':'static normal base-slot doors only; no event gates, alternate states, landing, progression or save certification'}


def compare_world_graphs(before,after):
    """Report changed door endpoints and surviving incoming links to their sources."""
    if before['profile']!=after['profile']:raise PatchError('Cannot compare graphs from different profiles')
    old={e['id']:e for e in before['edges']};new={e['id']:e for e in after['edges']};changes=[]
    fields=('destination_address','targets','boundary','spawn','secondary_spawn')
    for ident in sorted(set(old)|set(new)):
        a=old.get(ident);b=new.get(ident)
        if a is not None and b is not None and all(a[k]==b[k] for k in fields):continue
        # A surviving incoming edge whose original direct return was the
        # changed source can become stranded. Report loss, never auto-rewire.
        displaced=[]
        if a:
            for incoming in before['edges']:
                if incoming['source_address']!=a['destination_address'] or incoming['destination_address']!=a['source_address']:continue
                now=new.get(incoming['id'])
                if now and now['destination_address']==incoming['destination_address'] and not now['direct_return_observed']:
                    displaced.append(incoming['id'])
        changes.append({'edge':ident,'before':a,'after':b,'surviving_incoming_edges_without_return':sorted(displaced)})
    return {'schema_version':1,'before_sha256':before['image_sha256'],'after_sha256':after['image_sha256'],
            'changed_edges':changes,'scope':'static routing delta; observed missing return is a review finding, not proof of a softlock'}
