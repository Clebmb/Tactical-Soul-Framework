"""Nonmutating connection proposals using the existing checked level writer."""
import copy,hashlib
from .core import PatchError
from .level import apply_level_edits
from .world_graph import audit_world_graph,compare_world_graphs


def plan_connections(rom,spec):
    """Stage existing-door pairs on a deep copy; return review evidence only."""
    if not isinstance(spec,dict) or set(spec)!={'schema_version','expected_image_sha256','connections'}:
        raise PatchError('Connection plan requires schema_version, expected_image_sha256 and connections')
    if type(spec['schema_version']) is not int or spec['schema_version']!=1:raise PatchError('Unsupported connection plan schema')
    if not isinstance(spec['connections'],list) or not 1<=len(spec['connections'])<=32:
        raise PatchError('Connection plan requires 1..32 pairs')
    digest=hashlib.sha256(rom.data).hexdigest()
    if spec['expected_image_sha256']!=digest:raise PatchError('Connection plan image preimage mismatch')
    staged=copy.deepcopy(rom);before=audit_world_graph(staged)
    if not before['enumeration_complete']:raise PatchError('Connection planning requires a complete baseline graph')
    ledger_start=len(staged.ledger)
    reports=apply_level_edits(staged,{'connections':copy.deepcopy(spec['connections'])})
    after=audit_world_graph(staged)
    if not after['enumeration_complete']:raise PatchError('Proposed graph is incomplete')
    old_missing={e['id'] for e in before['edges'] if not e['direct_return_observed']}
    new_missing={e['id'] for e in after['edges'] if not e['direct_return_observed']}
    old_unresolved={e['id'] for e in before['edges'] if not e['targets']}
    new_unresolved={e['id'] for e in after['edges'] if not e['targets']}
    if new_missing-old_missing:raise PatchError('Proposal introduces additional edges without observed direct returns')
    if new_unresolved-old_unresolved:raise PatchError('Proposal introduces unresolved destinations')
    delta=compare_world_graphs(before,after)
    if not delta['changed_edges']:raise PatchError('Connection proposal has no routing changes')
    return {'schema_version':1,'status':'static_proposal_not_gameplay_verified',
            'input_sha256':digest,'proposed_image_sha256':hashlib.sha256(staged.data).hexdigest(),
            'connections':copy.deepcopy(spec['connections']),'room_reports':reports,
            'before_summary':before['summary'],'after_summary':after['summary'],'changes':delta,
            'restored_observed_return_edges':sorted(old_missing-new_missing),
            'staged_writes':staged.ledger[ledger_start:],
            'scope':'isolated checked existing-door planning only; no ROM output, landing, progression or native traversal certification'}
