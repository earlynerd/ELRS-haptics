"""Apply the user's completed pod-6 template to a single satellite instance."""
import json,sys,shutil
from pathlib import Path
import pcbnew as p
from kicad_edit import load,save,children,child,uq
HW=Path(__file__).resolve().parents[1]/'hardware';OUT=HW/'verification/routing-v08'
i=int(sys.argv[1]);assert 1<=i<=7
def reference(ref):
    prefix=ref[0];n=int(ref[1:]);d=i-6
    if prefix=='U':return f'U{n+d}'
    if prefix in ['M','F']:return f'{prefix}{n+d}'
    if prefix=='J':return f'J{n+(d if n>=200 else 4*d)}'
    if prefix=='C':return f'C{n+(10*d if n>=100 else 3*d)}'
    if prefix=='R':return f'R{n+(10*d if n>=100 else 2*d)}'
    raise AssertionError(ref)
specs=json.loads((HW/'verification/placement/placement.json').read_text())['pods'];spec=specs[i];ox,oy=spec['origin']
a=load(HW/'backups/user-placement-20260913/haptic-bracelet.kicad_pcb')
def inside(at):
    x,y=map(float,at[1:3]);return ox-.1<=x<=ox+17.1 and oy-.1<=y<=oy+35.1
for k,field in [('footprint','at'),('gr_line','start')]:
    for item in children(a,k):
        if not inside(child(item,field)):a.remove(item)
for k in ['segment','via','zone']:
    for item in children(a,k):a.remove(item)
dest=OUT/f'pod-{i}.kicad_pcb';save(dest,a)
shutil.copy2(HW/'haptic-bracelet.kicad_pro',dest.with_suffix('.kicad_pro'))
b=p.LoadBoard(str(dest));source=p.LoadBoard(str(OUT/'completed-template.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()};netmap={};delta=p.VECTOR2I(p.FromMM(ox-103),p.FromMM(oy-96))
for sf in source.GetFootprints():
    f=fps[reference(sf.GetReference())];f.SetPosition(sf.GetPosition()+delta);f.SetOrientation(sf.GetOrientation())
    pads={pad.GetNumber():pad for pad in f.Pads()}
    for sp in sf.Pads():
        name=sp.GetNetname();net=pads[sp.GetNumber()].GetNet()
        if name in netmap:assert net.GetNetname()==netmap[name].GetNetname()
        netmap[name]=net
if i==7:
    f=fps['R53'];f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(p.FromMM(ox+13),p.FromMM(oy+28.2)))
for original in list(source.GetTracks())+list(source.Zones()):
    item=original.Duplicate();item.SetParent(b);item.Move(delta);item.SetNet(netmap[original.GetNetname()]);b.Add(item)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dest),b)
print(i,len(list(b.GetTracks())))
