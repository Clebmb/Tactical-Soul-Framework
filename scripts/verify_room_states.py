"""Private base-slot state/load survey; not event-selection certification."""
import sys,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aria.cli import load_image
from aria.rooms import sector_span
from aria.room_states import inspect_room_states
r=load_image(ROOT/'CastlevaniaAoS.gba');before=bytes(r.data);counts=Counter();loads=Counter();findings=[]
for sector in range(12):
    _,n=sector_span(r,sector)
    for index in range(n):
        a=inspect_room_states(r,sector,index)
        assert a['chain_complete'],a['diagnostics']
        counts['base_slots']+=1;counts['state_observations']+=len(a['states'])
        for state in a['states']:
            counts['nonzero_next_links']+=bool(state['next_state_address'])
            for kind,load in state['loads'].items():
                loads[kind+':'+load['status']]+=1
                if load['status']!='resolved':findings.append({'sector':sector,'room':index,'ordinal':state['ordinal'],'kind':kind,**load})
assert counts['base_slots']==counts['state_observations']==343 and counts['nonzero_next_links']==0
assert bytes(r.data)==before and not r.ledger and not r.allocations
report={'passed':['343 base-slot chains terminate','all original next-state pointers are zero','original/ledger/allocations unchanged'],
        'counts':dict(counts),'load_status_counts':dict(loads),'findings':findings,
        'limitations':['alternate chains exercised synthetically only','event flag selection and native state transitions unverified','empty loads not assigned guessed prior resources']}
folder=ROOT/'local';folder.mkdir(exist_ok=True);(folder/'room-state-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
