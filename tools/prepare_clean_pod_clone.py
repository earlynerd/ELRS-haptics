import json,hashlib,shutil
from kicad_edit import HW,load,save,children,child
out=HW/'verification/routing-v09';out.mkdir(exist_ok=True)
backup=HW/'backups/before-clean-pod-clone';backup.mkdir(exist_ok=False)
hashes={}
for name in ['haptic-bracelet.kicad_pcb','haptic-bracelet.kicad_pro']:
    shutil.copy2(HW/name,backup/name);hashes[name]=hashlib.sha256((HW/name).read_bytes()).hexdigest()
(backup/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
a=load(HW/'haptic-bracelet.kicad_pcb')
def inside(at):
    x,y=map(float,at[1:3]);return 102.9<x<120.1 and 95.9<y<131.1
for k,field in [('footprint','at'),('gr_line','start'),('segment','start'),('via','at')]:
    for item in children(a,k):
        if not inside(child(item,field)):a.remove(item)
for z in children(a,'zone'):
    if not all(inside(pt) for pt in children(child(child(z,'polygon'),'pts'),'xy')):a.remove(z)
save(out/'completed-template.kicad_pcb',a)
(out/'fp-lib-table').write_text((HW/'fp-lib-table').read_text().replace('${KIPRJMOD}',HW.as_posix()))
shutil.copy2(HW/'haptic-bracelet.kicad_pro',out/'completed-template.kicad_pro')
# Reuse bounded replication and merge with new provenance; do not overwrite old evidence.
root=HW.parent
for source,target in [('replicate_v08.py','replicate_v09.py'),('merge_v08.py','merge_v09.py')]:
    text=(root/'tools'/source).read_text().replace('routing-v08','routing-v09').replace('user-placement-20260913','before-clean-pod-clone')
    (root/'tools'/target).write_text(text)
print('Backed up current master; extracted current pod 6')
