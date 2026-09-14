"""Bounded satellite routing around the user's pod-6 functional placement.

The template and work products are separate from the native master until merge.
"""
import sys,json,re,shutil,hashlib
from pathlib import Path
import pcbnew as p
from kicad_edit import load,save,children,child,uq,q
HW=Path(__file__).resolve().parents[1]/'hardware';OUT=HW/'verification/routing-v08'
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def fps(b):return {f.GetReference():f for f in b.GetFootprints()}
def pad(b,ref,num):return next(x for x in fps(b)[ref].Pads() if x.GetNumber()==num)
def track(b,net,points,width=.15,layer=p.F_Cu):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=p.PCB_TRACK(b);t.SetStart(vec(103+a[0],96+a[1]));t.SetEnd(vec(103+z[0],96+z[1]));t.SetWidth(p.FromMM(max(width,.11)));t.SetLayer(layer);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
def via(b,net,xy,diameter=.6,drill=.3):
    t=p.PCB_VIA(b);t.SetPosition(vec(103+xy[0],96+xy[1]));t.SetWidth(p.FromMM(diameter));t.SetDrill(p.FromMM(drill));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet(net));t.SetLocked(True);b.Add(t)
def refill(b,path):
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
def prepare():
    b=p.LoadBoard(str(OUT/'template.kicad_pcb'))
    for t in b.GetTracks():t.SetLocked(True)
    f=fps(b)['C24'];f.Move(vec(0,-.2))
    # Direct local passive connections, preserving the user's functional groups.
    track(b,pad(b,'R162','2').GetNetname(),[(11.7125,3.875),(13.165,3.875),(13.19,3.9)])
    track(b,'RING_D6',[(1.1,16),(2.84,16),(2.95,16.11)],.2)
    track(b,pad(b,'R165','2').GetNetname(),[(13.65,10.03),(14.67,10.03),(14.7,10.06)])
    # Supply/reset and REG paths need no signal-layer transitions.
    track(b,'POD_3V3',[(13.1,22.7),(13.1,23.1)],.1)
    track(b,'POD_3V3',[(13.1,23.1),(13.1,24.13),(13.08,24.15),(13.08,25.1),(13.08,25.85)])
    via(b,'POD_3V3',(13.08,25.85))
    track(b,'GND',[(12.12,24.15),(12.12,25.1),(12.12,25.85)],.2)
    via(b,'GND',(12.12,25.85))
    track(b,pad(b,'U9','A2').GetNetname(),[(13.1,22.3),(13.1,21.23)],.1)
    # Ordinary outer-pad fanouts; reserve the two left exits for SDA/SCL.
    track(b,pad(b,'U9','B1').GetNetname(),[(12.7,22.7),(12.1,22.7),(12,22.6)],.1)
    via(b,pad(b,'U9','B1').GetNetname(),(12,22.6),.5,.2)
    track(b,pad(b,'U9','C1').GetNetname(),[(12.7,23.1),(12.25,23.1),(12,23.35)],.1)
    via(b,pad(b,'U9','C1').GetNetname(),(12,23.35),.5,.2)
    track(b,'GND',[(13.5,22.7),(14.35,22.7)],.1);via(b,'GND',(14.35,22.7))
    refill(b,OUT/'prepared.kicad_pcb');shutil.copy2(HW/'haptic-bracelet.kicad_pro',OUT/'prepared.kicad_pro')
def export(name):
    path=OUT/(name+'.kicad_pcb');b=p.LoadBoard(str(path));assert p.ExportSpecctraDSN(b,str(OUT/(name+'.dsn')))
    dsn=OUT/(name+'.dsn');text=dsn.read_text()
    # KiCad DSN board-edge rules need extra routing margin, without changing the
    # native outline. Export the native filled plane polygons including holes.
    def offset(m):
        vals=list(map(float,m.group(2).split()));xs=vals[::2];ys=vals[1::2];mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
        delta=-120 if 'path pcb' in m.group(1) else 120
        return m.group(1)+' '+' '.join(str(round(v+delta*(1 if v>mid else -1),3)) for pair in zip(xs,ys) for v,mid in zip(pair,[mx,my]))+m.group(3)
    text=re.sub(r'(\(path pcb 0|\(polygon signal 0)\s+([\d.\s-]+)(\))',offset,text)
    # Replace the naive unfilled zone-outline export with actual filled polygons.
    text=re.sub(r'\(plane [^\s]+ \(polygon .*?\)\)', '',text,flags=re.S)
    planes=[]
    for z in b.Zones():
        layer=z.GetLayer();poly=z.GetFilledPolysList(layer)
        def polygon(chain):
            pts=[chain.CPoint(j) for j in range(chain.PointCount())]
            return '(polygon '+b.GetLayerName(layer)+' 0 '+' '.join(f'{p.ToMM(v.x)*1000:.3f} {-p.ToMM(v.y)*1000:.3f}' for v in pts)+')'
        for i in range(poly.OutlineCount()):
            s='(plane '+z.GetNetname()+' '+polygon(poly.COutline(i))
            for j in range(poly.HoleCount(i)):s+=' (window '+polygon(poly.CHole(i,j))+')'
            planes.append(s+')')
    insert=text.index('    (via ')
    text=text[:insert]+'\n'.join(planes)+'\n'+text[insert:]
    dsn.write_text(text)
    print('Export',name,'planes',len(planes))
def import_session(name):
    b=p.LoadBoard(str(OUT/(name+'.kicad_pcb')))
    assert p.ImportSpecctraSES(b,str(OUT/(name+'.ses')))
    refill(b,OUT/(name+'-routed.kicad_pcb'))
    shutil.copy2(HW/'haptic-bracelet.kicad_pro',OUT/(name+'-routed.kicad_pro'))
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':prepare()
    if mode=='export':export(sys.argv[2])
    if mode=='import':import_session(sys.argv[2])
