"""Export isolated pod routing jobs; never route the air gaps in the placement panel."""
from pathlib import Path
import json,sys,shutil,re
import pcbnew as p
from kicad_edit import load,save,children,child,uq
from plane_fanout import fanout
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/routing'
placement=json.loads((HW/'verification/placement/placement.json').read_text())
for i in [int(s) for s in sys.argv[1:]] or list(range(8)):
    a=load(HW/'haptic-bracelet.kicad_pcb')
    refs={ref for ref,rec in placement['components'].items() if rec['pod']==i}
    for f in children(a,'footprint'):
        ref=next(uq(x[2]) for x in children(f,'property') if uq(x[1])=='Reference')
        if ref not in refs:a.remove(f)
    spec=placement['pods'][i];ox,oy=spec['origin'];w,h=spec['width'],spec['height']
    def inside(item):
        at=child(item,'start');x,y=map(float,at[1:3])
        return ox-1<x<ox+w+1 and oy-1<y<oy+h+1
    for kind in ['gr_line','segment']:
        for item in children(a,kind):
            if not inside(item):a.remove(item)
    dest=OUT/f'pod-{i}';dest.mkdir(exist_ok=True)
    pcb=dest/f'pod-{i}.kicad_pcb';save(pcb,a)
    shutil.copy2(HW/'haptic-bracelet.kicad_pro',pcb.with_suffix('.kicad_pro'))
    table=(HW/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(HW).replace('\\','/'))
    (dest/'fp-lib-table').write_text(table)
    b=p.LoadBoard(str(pcb))
    # Pull-ups belong in the spacious driver bay; the original fit-only packing
    # put them in a narrow cutout-side routing channel.
    if i:
        moves={f'R{8+2*i}':(9.2,8.2),f'R{9+2*i}':(11.6,8.2),
               f'R{100+10*i}':(5.3,25.8),f'R{102+10*i}':(7.3,25.8)}
        for f in b.GetFootprints():
            if f.GetReference() in moves:
                x,y=moves[f.GetReference()];f.SetOrientationDegrees(0);f.SetPosition(p.VECTOR2I(p.FromMM(ox+x),p.FromMM(oy+y)))
        # Escape B1 before supply fanout so the adjacent decoupler ground via
        # cannot obstruct this middle-row pad's only useful surface exit.
        drv=next(f for f in b.GetFootprints() if f.GetReference()==f'U{3+i}')
        pad=next(pad for pad in drv.Pads() if pad.GetNumber()=='B1')
        def point(x,y):return p.VECTOR2I(p.FromMM(ox+x),p.FromMM(oy+y))
        pts=[(8,6),(7.7,6),(7.4,5.7),(7.4,5.1)]
        for aa,zz in zip(pts,pts[1:]):
            t=p.PCB_TRACK(b);t.SetStart(point(*aa));t.SetEnd(point(*zz));t.SetWidth(p.FromMM(.1));t.SetLayer(p.F_Cu);t.SetNet(pad.GetNet());t.SetLocked(True);b.Add(t)
        via=p.PCB_VIA(b);via.SetPosition(point(*pts[-1]));via.SetWidth(p.FromMM(.45));via.SetDrill(p.FromMM(.2));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());via.SetLocked(True);b.Add(via)
    # Solid internal planes. No signal routing is permitted on either inner layer
    # in these satellite jobs. The actuator opening is clipped by KiCad's filler.
    for layer,net in [(p.In1_Cu,'GND'),(p.In2_Cu,'POD_3V3')]:
        z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(net));z.SetLocalClearance(p.FromMM(.2))
        z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.15))
        poly=z.Outline();poly.NewOutline()
        for x,y in [(ox,oy+spec['top_edge']),(ox+w,oy+spec['top_edge']),(ox+w,oy+h),(ox,oy+h)]:poly.Append(p.FromMM(x),p.FromMM(y))
        b.Add(z)
    result=fanout(b,spec)
    (dest/'plane-fanout.json').write_text(json.dumps(result,indent=2)+'\n')
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(pcb),b)
    assert p.ExportSpecctraDSN(b,str(dest/f'pod-{i}.dsn'))
    dsn=dest/f'pod-{i}.dsn';text=dsn.read_text()
    # DSN uses ordinary track clearance at cutouts, so expand the routing obstacle
    # by 0.12 mm. The native Edge.Cuts geometry is preserved for actual DRC.
    def inset(match):
        nums=list(map(float,match.group(2).split()));xs=nums[0::2];ys=nums[1::2]
        mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
        delta=-120 if 'path pcb' in match.group(1) else 120
        points=[str(round(v+delta*(1 if v>mid else -1),4)) for pair in zip(xs,ys) for v,mid in zip(pair,[mx,my])]
        return match.group(1)+' '+' '.join(points)+match.group(3)
    text=re.sub(r'(\(path pcb 0|\(polygon signal 0)\s+([\d.\s-]+)(\))',inset,text)
    # Give the battery bus and positive cell branch 0.40 mm conductors.
    start=text.index('(class kicad_default');end=text.index('(circuit',start)
    portion=text[start:end]
    cell=next(n.GetNetname() for n in b.GetNetsByName().values() if n.GetNetname().endswith('/CELL_POS') and f'Pod {i} ' in n.GetNetname())
    portion=portion.replace('"'+cell+'"','')
    portion=re.sub(r'\b(VBAT|GND|POD_3V3)\b','',portion)
    text=text[:start]+portion+text[end:]
    idx=text.index('  (wiring')
    # Insert inside the network block, immediately before its final close.
    pos=text.rfind('  )',0,idx)
    text=text[:pos]+f'    (class battery_bus VBAT "{cell}" (circuit (use_via "Via[0-3]_450:200_um")) (rule (width 400) (clearance 150)))\n'+text[pos:]
    pos=text.rfind('  )',0,text.index('  (wiring'))
    text=text[:pos]+'    (class plane_rails GND POD_3V3 (circuit (use_via "Via[0-3]_450:200_um")) (rule (width 250) (clearance 150)))\n'+text[pos:]
    hole=re.search(r'\(keepout "" \(polygon signal 0\s+([\d.\s-]+)\)\)',text).group(1)
    vals=list(map(float,hole.split()));mx=(min(vals[::2])+max(vals[::2]))/2;my=(min(vals[1::2])+max(vals[1::2]))/2
    hole=' '.join(str(round(value+170*(1 if value>mid else -1),4)) for pair in zip(vals[::2],vals[1::2]) for value,mid in zip(pair,[mx,my]))
    text=re.sub(r'(\(plane (?:GND|POD_3V3) \(polygon (In[12].Cu) .*?\))\)',lambda m:m.group(1)+f' (window (polygon {m.group(2)} 0 {hole})))',text,flags=re.S)
    dsn.write_text(text)
    print(i,len(list(b.GetFootprints())),b.GetCopperLayerCount())
