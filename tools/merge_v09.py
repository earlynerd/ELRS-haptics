"""Merge only seven independently checked satellites; retain user main board."""
import hashlib,json
from pathlib import Path
from kicad_edit import load,save,children,child,uq
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/routing-v09'
master=HW/'haptic-bracelet.kicad_pcb'
hashes=json.loads((HW/'backups/before-clean-pod-clone/sha256.json').read_text())
for name,expected in hashes.items():
    assert hashlib.sha256((HW/name).read_bytes()).hexdigest()==expected,('User file changed during work',name)
def ref(f):return uq(next(x for x in children(f,'property') if uq(x[1])=='Reference')[2])
a=load(master);oldrefs={ref(f) for f in children(a,'footprint')};new=[];refs=set()
for i in range(1,8):
    report=json.loads((OUT/f'pod-{i}-drc.json').read_text())
    assert not report['violations'] and not report['unconnected_items'],i
    source=load(OUT/f'pod-{i}.kicad_pcb')
    for f in children(source,'footprint'):
        assert ref(f) not in refs;refs.add(ref(f))
    for k in ['footprint','segment','via','zone']:new.extend(children(source,k))
assert len(refs)==162
main=[]
for f in children(a,'footprint'):
    if ref(f) in refs:a.remove(f)
    else:main.append(f)
for kind,key in [('segment','start'),('via','at')]:
    for t in children(a,kind):
        if float(child(t,key)[1])>70:a.remove(t)
        else:main.append(t)
# All existing copper zones are satellite zones; assert before replacing.
for z in children(a,'zone'):
    pts=child(child(z,'polygon'),'pts')
    assert all(float(q[1])>70 for q in children(pts,'xy'))
    a.remove(z)
a.extend(new)
assert {ref(f) for f in children(a,'footprint')}==oldrefs
def uuids(tree):
    for x in tree:
        if isinstance(x,list):
            if x[0]=='uuid':yield uq(x[1])
            else:yield from uuids(x)
ids=list(uuids(a));assert len(ids)==len(set(ids)), 'Duplicated UUIDs'
save(OUT/'merged.kicad_pcb',a)
save(master,a)
(OUT/'merge.json').write_text(json.dumps({'source_sha256':hashes,'satellite_footprints':len(refs),'main_items_preserved':len(main),'merged_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'unique_uuids':len(ids)},indent=2)+'\n')
print('Merged seven satellites; main footprints/tracks unchanged; unique UUIDs',len(ids))
