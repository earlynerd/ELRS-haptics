"""Bounded cleanup of the user's second pod-6 routing pass."""
import copy,json,hashlib,shutil
from kicad_edit import HW,load,save,children,child,uq

out=HW/'verification/pod6-six-mil-cleanup';out.mkdir(exist_ok=True)
backup=HW/'backups/before-pod6-six-mil-cleanup';backup.mkdir(exist_ok=False)
source=HW/'haptic-bracelet.kicad_pcb'
hashes={}
for name in ['haptic-bracelet.kicad_pcb','haptic-bracelet.kicad_pro']:
    shutil.copy2(HW/name,backup/name)
    hashes[name]=hashlib.sha256((HW/name).read_bytes()).hexdigest()
(backup/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
a=load(source)
dup=next(t for t in children(a,'segment') if uq(child(t,'uuid')[1])=='cf3b3cd7-cf14-4478-b20d-ec7eaeb1991e')
cover=next(t for t in children(a,'segment') if uq(child(t,'uuid')[1])=='ca1401dd-3294-4273-a140-81ac7b8f5085')
assert child(dup,'net')==child(cover,'net') and child(dup,'layer')==child(cover,'layer')
assert child(dup,'start')==child(cover,'start')
assert child(dup,'start')[2]==child(dup,'end')[2]==child(cover,'end')[2]
assert float(child(dup,'end')[1])<float(child(cover,'end')[1])
assert float(child(dup,'width')[1])<float(child(cover,'width')[1])
a.remove(dup);changes=[]
for t in children(a,'segment'):
    x,y=map(float,child(t,'start')[1:3])
    if 103<x<120 and 96<y<131 and float(child(t,'width')[1])<.1524:
        changes.append({'uuid':uq(child(t,'uuid')[1]),'net':uq(child(t,'net')[1]),'old_width':float(child(t,'width')[1]),'new_width':.1524})
        child(t,'width')[1]='0.1524'
assert len(changes)==13
save(out/'candidate.kicad_pcb',a)
isolated=copy.deepcopy(a)
def inside(at):
    x,y=map(float,at[1:3]);return 102.9<x<120.1 and 95.9<y<131.1
for k,field in [('footprint','at'),('gr_line','start'),('segment','start'),('via','at')]:
    for item in children(isolated,k):
        if not inside(child(item,field)):isolated.remove(item)
for z in children(isolated,'zone'):
    if not all(inside(pt) for pt in children(child(child(z,'polygon'),'pts'),'xy')):isolated.remove(z)
save(out/'pod-6.kicad_pcb',isolated)
shutil.copy2(HW/'haptic-bracelet.kicad_pro',out/'pod-6.kicad_pro')
(out/'fp-lib-table').write_text((HW/'fp-lib-table').read_text().replace('${KIPRJMOD}',HW.as_posix()))
(out/'changes.json').write_text(json.dumps({'source_hashes':hashes,'removed_duplicate_uuid':uq(child(dup,'uuid')[1]),'covering_segment_uuid':uq(child(cover,'uuid')[1]),'width_changes':changes},indent=2)+'\n')
print('Candidate: removed one fully covered duplicate; widened',len(changes),'segments')
