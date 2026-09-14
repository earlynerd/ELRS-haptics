"""Current satellite closure, net correspondence, and main-board preservation."""
import json,re,xml.etree.ElementTree as E
from pathlib import Path
import pcbnew as p
from kicad_edit import load,child,children,uq
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';OUT=HW/'verification/routing-v08'
b=p.LoadBoard(str(HW/'haptic-bracelet.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
xml=E.parse(OUT/'netlist.xml').getroot()
assert set(fps)=={c.attrib['ref'] for c in xml.findall('components/comp')}
assert len(fps)==261 and b.GetCopperLayerCount()==4
assert abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-.8)<1e-6
def escaped(s):
    s=re.sub(r'Pod (\d) / U(\d+)',r'Pod \1 {slash} U\2',s)
    return s.replace('/','{slash}') if s.startswith('unconnected-') else s
nodes={(x.attrib['ref'],x.attrib['pin']):escaped(n.attrib['name']) for n in xml.findall('nets/net') for x in n.findall('node')}
count=0
for ref,f in fps.items():
    for pad in f.Pads():
        if not pad.GetNumber():continue
        for member in pad.GetNumber().split('/'):
            assert pad.GetNetname()==nodes.get((ref,member),''),(ref,pad.GetNumber())
        count+=1
poly=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(poly,False)
assert poly.OutlineCount()==8 and all(poly.HoleCount(i)==1 for i in range(8))
specs=json.loads((HW/'verification/placement/placement.json').read_text())['pods']
def which(pos):
    return next(s['pod'] for s in specs if s['origin'][0]-1<pos['x']<s['origin'][0]+s['width']+1 and s['origin'][1]-1<pos['y']<s['origin'][1]+s['height']+1)
drc=json.loads((OUT/'drc.json').read_text());assert not drc['schematic_parity']
main=external=0
for item in drc['unconnected_items']:
    pods={which(x['pos']) for x in item['items']}
    if len(pods)>1:external+=1
    else:assert pods=={0},item;main+=1
for item in drc['violations']:
    assert {which(x['pos']) for x in item['items']}=={0},item
sat=[]
for i in range(1,8):
    report=json.loads((OUT/f'pod-{i}-drc.json').read_text())
    assert not report['violations'] and not report['unconnected_items'],i
    ox,oy=specs[i]['origin']
    items=[t for t in b.GetTracks() if ox<=p.ToMM(t.GetPosition().x)<=ox+17 and oy<=p.ToMM(t.GetPosition().y)<=oy+35]
    vias=[t for t in items if isinstance(t,p.PCB_VIA)]
    tracks=[t for t in items if not isinstance(t,p.PCB_VIA)]
    assert all(t.GetLayer() in [p.F_Cu,p.B_Cu] for t in tracks)
    assert all(p.ToMM(t.GetWidth())>=.1016 for t in tracks)
    assert all(p.ToMM(t.GetWidth(p.F_Cu))>=.5 and p.ToMM(t.GetDrillValue())>=.2 for t in vias)
    jin,jout=fps[f'J{100+4*i}'],fps[f'J{101+4*i}']
    assert all(a.GetPosition().y==z.GetPosition().y for a,z in zip(sorted(jin.Pads(),key=lambda p:p.GetNumber()),sorted(jout.Pads(),key=lambda p:p.GetNumber())))
    sat.append({'pod':i,'segments':len(tracks),'vias':len(vias),'violations':0,'opens':0,'inner_signal_tracks':0})
old=load(HW/'backups/user-placement-20260913/haptic-bracelet.kicad_pcb');now=load(HW/'haptic-bracelet.kicad_pcb')
for kind,field in [('footprint','at'),('segment','start'),('via','at')]:
    before=[x for x in children(old,kind) if float(child(x,field)[1])<70]
    after=[x for x in children(now,kind) if float(child(x,field)[1])<70]
    assert before==after,('Main board changed',kind)
result={'status':'PASS','revision':'0.8','electrical_pads_checked':count,'components':len(fps),'copper_layers':4,'zones':len(list(b.Zones())),'islands':8,'actuator_cutouts':8,'schematic_parity_issues':0,'main_items_unchanged':True,'main_unconnected_items':main,'external_unconnected_items':external,'main_violations':[{'type':x['type'],'severity':x['severity']} for x in drc['violations']],'satellites':sat}
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
