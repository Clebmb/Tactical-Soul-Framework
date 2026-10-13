"""Refresh the living handoff status while preserving its durable instructions."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('progress','validation','next','limitations'):parser.add_argument('--'+name,required=True)
 args=parser.parse_args();path=ROOT/'handoff.md';source=path.read_text(encoding='utf-8')
 start='<!-- STATUS START -->';end='<!-- STATUS END -->'
 if source.count(start)!=1 or source.count(end)!=1:raise ValueError('Handoff status markers must be unique')
 a=source.index(start)+len(start);b=source.index(end)
 if b<a:raise ValueError('Handoff status markers are reversed')
 capability=json.loads((ROOT/'framework/capabilities.json').read_text());roadmap=json.loads((ROOT/'framework/roadmap.json').read_text())
 stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
 status='\nUpdated (UTC): '+stamp+'\n\nCurrent framework: **'+capability['version']+'**. Estimated completion: **'+str(roadmap['estimated_complete_percent'])+'%** ('+str(round(sum(d['earned_estimate'] for d in roadmap['domains']),1))+'/100 weighted maturity points).\n\n'
 for label,value in [('Completed this turn',args.progress),('Verification actually run',args.validation),('Next concrete work',args.next),('Remaining limits / unfinished work',args.limitations)]:status+='**'+label+':** '+value+'\n\n'
 path.write_text(source[:a]+status+source[b:],encoding='utf-8')
 print('Updated handoff.md for '+capability['version'])
if __name__=='__main__':main()
