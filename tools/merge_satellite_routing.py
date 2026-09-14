"""Merge only locally DRC-closed satellite boards into the native placement panel."""
import json,collections
import pcbnew as p
from kicad_edit import *
OUT=HW/'verification/routing';PCB=HW/'haptic-bracelet.kicad_pcb'
assert not (OUT/'merged.json').exists(),'Already merged; preserve subsequent native edits.'
a=load(PCB)
record=json.loads((HW/'verification/placement/placement.json').read_text())
satrefs={r for r,v in record['components'].items() if v['pod']!=0}
for fp in children(a,'footprint'):
    ref=next(uq(v[2]) for v in children(fp,'property') if uq(v[1])=='Reference')
    if ref in satrefs:a.remove(fp)
for s in children(a,'segment'):
    # Main board currently has only its B2-C2 reset link.
    if float(child(s,'start')[1])>60:a.remove(s)
for i in range(1,8):
    drc=json.loads((OUT/f'pod-{i}/drc.json').read_text())
    assert not drc['violations'] and not drc['unconnected_items'],i
    pod=load(OUT/f'pod-{i}/pod-{i}-routed.kicad_pcb')
    for key in ['footprint','segment','via','zone']:a.extend(children(pod,key))
uuids=[]
def visit(node):
    if node[0]=='uuid':uuids.append(uq(node[1]))
    for c in node:
        if isinstance(c,list):visit(c)
visit(a)
assert len(uuids)==len(set(uuids)),[k for k,v in collections.Counter(uuids).items() if v>1]
save(PCB,a)
b=p.LoadBoard(str(PCB));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(PCB),b)
report={'revision':'0.7','locally_routed_pods':list(range(1,8)),'main_pod_routing':'Pending except direct driver reset link','copper_layers':b.GetCopperLayerCount(),'tracks_and_vias':len(list(b.GetTracks())),'zones':len(list(b.Zones()))}
(OUT/'merged.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
