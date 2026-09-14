"""Replicate a DRC-closed pod-1 layout using pad-derived net mappings."""
from pathlib import Path
import json,sys,shutil
import pcbnew as p
HW=Path(__file__).resolve().parents[1]/'hardware';OUT=HW/'verification/routing'
source=p.LoadBoard(str(OUT/'pod-1/pod-1-routed.kicad_pcb'))
report=json.loads((OUT/'pod-1/drc.json').read_text())
assert not report['violations'] and not report['unconnected_items']
specs=json.loads((HW/'verification/placement/placement.json').read_text())['pods']
def reference(ref,i):
    prefix=ref[0];number=int(ref[1:]);d=i-1
    if prefix=='U':return f'U{number+d}'
    if prefix in ['M','F']:return f'{prefix}{number+d}'
    if prefix=='J':return f'J{number+(d if number>=200 else 4*d)}'
    if prefix=='C':return f'C{number+(10*d if number>=100 else 3*d)}'
    if prefix=='R':return f'R{number+(10*d if number>=100 else 2*d)}'
    raise AssertionError(ref)
for i in map(int,sys.argv[1:]):
    dest=OUT/f'pod-{i}';b=p.LoadBoard(str(dest/f'pod-{i}.kicad_pcb'))
    removed=list(b.GetTracks())+list(b.Zones())
    for item in removed:b.Remove(item)
    fps={f.GetReference():f for f in b.GetFootprints()};netmap={}
    dx,dy=[a-c for a,c in zip(specs[i]['origin'],specs[1]['origin'])];delta=p.VECTOR2I(p.FromMM(dx),p.FromMM(dy))
    for sf in source.GetFootprints():
        f=fps[reference(sf.GetReference(),i)];f.SetPosition(sf.GetPosition()+delta);f.SetOrientation(sf.GetOrientation())
        pads={pad.GetNumber():pad for pad in f.Pads()}
        for sp in sf.Pads():
            target=pads[sp.GetNumber()].GetNet();name=sp.GetNetname()
            if name in netmap:assert target.GetNetname()==netmap[name].GetNetname()
            netmap[name]=target
    if i==7:
        fps['R53'].SetOrientationDegrees(0)
        fps['R53'].SetPosition(p.VECTOR2I(p.FromMM(specs[i]['origin'][0]+13),p.FromMM(specs[i]['origin'][1]+10.5)))
    for original in list(source.GetTracks())+list(source.Zones()):
        item=original.Duplicate();item.SetParent(b);item.Move(delta);item.SetNet(netmap[original.GetNetname()]);b.Add(item)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(dest/f'pod-{i}-routed.kicad_pcb'),b)
    shutil.copy2(HW/'haptic-bracelet.kicad_pro',dest/f'pod-{i}-routed.kicad_pro')
    print(i,len(list(b.GetTracks())))
