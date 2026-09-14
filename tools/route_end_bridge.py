"""Place the end-pod-only return link clear of the replicated copper, then export."""
from pathlib import Path
import json,math,re
import pcbnew as p
from plane_fanout import point_rect,line_rect,xy,fanout
HW=Path(__file__).resolve().parents[1]/'hardware';D=HW/'verification/routing/pod-7'
b=p.LoadBoard(str(D/'pod-7-bridge-input.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};f=fps['R53']
others=[pad for fp in b.GetFootprints() if fp!=f for pad in fp.Pads()]
def box(item):
    bb=item.GetBoundingBox();return p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())
occupied=[]
for fp in b.GetFootprints():
    if fp.GetReference()=='R53':continue
    for g in fp.GraphicalItems():
        if g.GetLayer()==p.F_CrtYd:occupied.append(box(g))
def overlaps(a,z):return a[0]<z[2] and a[2]>z[0] and a[1]<z[3] and a[3]>z[1]
ox,oy=131,96;candidates=[]
for x in [v*.25 for v in range(6,63)]:
    for y in [v*.25 for v in range(6,136)]:
        bb=(ox+x-.96,oy+y-.5,ox+x+.96,oy+y+.5)
        if bb[0]<ox+.3 or bb[2]>ox+16.7:continue
        if overlaps(bb,(135-.25,106-.25,142+.25,121+.25)) or overlaps(bb,(142.1,116.5,147.7,122.4)):continue
        if any(overlaps(bb,z) for z in occupied):continue
        f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(p.FromMM(ox+x),p.FromMM(oy+y)))
        bad=False
        for pad in f.Pads():
            pb=box(pad)
            for t in b.GetTracks():
                if t.GetNetname()==pad.GetNetname():continue
                if isinstance(t,p.PCB_VIA):
                    if point_rect(xy(t.GetPosition()),pb)<p.ToMM(t.GetWidth(p.F_Cu))/2+.16:bad=True;break
                elif t.GetLayer()==p.F_Cu and line_rect(xy(t.GetStart()),xy(t.GetEnd()),pb,p.ToMM(t.GetWidth())/2+.16):bad=True;break
            if bad:break
        if not bad:candidates.append(((x-13)**2+(y-14)**2,x,y))
assert candidates
spec=json.loads((HW/'verification/placement/placement.json').read_text())['pods'][7]
discarded=[]
for _,x,y in sorted(candidates):
    f.SetPosition(p.VECTOR2I(p.FromMM(ox+x),p.FromMM(oy+y)))
    before={t.m_Uuid.AsString() for t in b.GetTracks()}
    try:
        fanout(b,spec,{('R53','1'),('R53','2'),('R171','2')})
        break
    except RuntimeError:
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() not in before:discarded.append(t);b.Remove(t)
else:raise RuntimeError('No bridge placement with clear via exits')
for t in b.GetTracks():t.SetLocked(True)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(D/'pod-7-routed.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(D/'bridge.dsn'))
path=D/'bridge.dsn';text=path.read_text()
def inset(m):
    vals=list(map(float,m.group(2).split()));xs=vals[::2];ys=vals[1::2];mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
    d=-120 if 'path pcb' in m.group(1) else 120
    return m.group(1)+' '+' '.join(str(round(v+d*(1 if v>mid else -1),4)) for pair in zip(xs,ys) for v,mid in zip(pair,[mx,my]))+m.group(3)
text=re.sub(r'(\(path pcb 0|\(polygon signal 0)\s+([\d.\s-]+)(\))',inset,text)
path.write_text(text)
(D/'end-bridge-placement.json').write_text(json.dumps({'ref':'R53','pod_local_mm':[x,y]},indent=2)+'\n')
print('R53',x,y)
