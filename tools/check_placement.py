"""Independent native placement/netlist correspondence and land-pattern checks."""
from pathlib import Path
import json,re,xml.etree.ElementTree as E
import pcbnew as p
from plane_fanout import xy,point_rect
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware'
b=p.LoadBoard(str(HW/'haptic-bracelet.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
xml=E.parse(HW/'verification/netlist.xml').getroot()
components={c.attrib['ref']:c for c in xml.findall('components/comp')}
assert set(fps)==set(components) and len(fps)==261
assert b.GetCopperLayerCount()==4 and abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-.8)<1e-6
def escaped(s):
    s=re.sub(r'Pod (\d) / U(\d+)',r'Pod \1 {slash} U\2',s)
    return s.replace('/','{slash}') if s.startswith('unconnected-') else s
nodes={(x.attrib['ref'],x.attrib['pin']):escaped(n.attrib['name']) for n in xml.findall('nets/net') for x in n.findall('node')}
count=0
for ref,f in fps.items():
    for pad in f.Pads():
        num=pad.GetNumber()
        if not num:continue
        for member in num.split('/'):
            expected=nodes.get((ref,member),'')
            assert pad.GetNetname()==expected,(ref,num,pad.GetNetname(),expected)
        count+=1
for i in range(3,11):
    f=p.FootprintLoad(str(HW/'HapticBracelet.pretty'),'DRV2625_YFF_9_0.4mm')
    pads={x.GetNumber():x for x in f.Pads()};assert set(pads)=={r+str(c) for r in 'ABC' for c in [1,2,3]}
    for r in 'ABC':
        for c in [1,2,3]:
            pad=pads[r+str(c)]
            assert abs(p.ToMM(pad.GetPosition().x)-.4*(c-2))<1e-6
            assert abs(p.ToMM(pad.GetPosition().y)-.4*('ABC'.index(r)-1))<1e-6
            assert abs(p.ToMM(pad.GetSize().x)-.225)<1e-6
f=p.FootprintLoad(str(HW/'HapticBracelet.pretty'),'TPS63802_DLA0010A')
pads={x.GetNumber():x for x in f.Pads()};assert set(pads)==set(map(str,range(1,11)))
assert abs(p.ToMM(pads['8'].GetSize().x)-1.3)<1e-6
assert abs(p.ToMM(pads['8'].GetPosition().x)-.55)<1e-6
assert abs(p.ToMM(pads['10'].GetPosition().y)+1)<1e-6
drc=json.loads((HW/'verification/routing/drc.json').read_text())
assert not drc['schematic_parity']
assert not [x for x in drc['violations'] if x['severity']=='error']
poly=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(poly,False)
assert poly.OutlineCount()==8 and all(poly.HoleCount(i)==1 for i in range(8))
specs=json.loads((HW/'verification/placement/placement.json').read_text())['pods']
def pod(item):
    return next(s['pod'] for s in specs if s['origin'][0]-1<item['pos']['x']<s['origin'][0]+s['width']+1 and s['origin'][1]-1<item['pos']['y']<s['origin'][1]+s['height']+1)
main_opens=external_opens=0
for item in drc['unconnected_items']:
    which={pod(n) for n in item['items']}
    if len(which)==1:
        assert which=={0},('Satellite connection reopened after merge',item)
        main_opens+=1
    else:external_opens+=1
for i in range(1,8):
    local=json.loads((HW/f'verification/routing/pod-{i}/drc.json').read_text())
    assert not local['violations'] and not local['unconnected_items'],i
assert not any(t.GetLayer()==p.In1_Cu for t in b.GetTracks() if not isinstance(t,p.PCB_VIA))
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
smds=[pad for f in fps.values() for pad in f.Pads() if pad.GetAttribute()==p.PAD_ATTRIB_SMD]
for via in vias:
    assert abs(p.ToMM(via.GetWidth(p.F_Cu))-.45)<1e-6 and abs(p.ToMM(via.GetDrillValue())-.2)<1e-6
    assert via.GetViaType()==p.VIATYPE_THROUGH
    for pad in smds:
        bb=pad.GetBoundingBox();box=tuple(p.ToMM(t) for t in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()])
        assert point_rect(xy(via.GetPosition()),box)>.1,('Drill overlaps SMD land',pad.GetParent().GetReference(),pad.GetNumber())
result={'status':'PASS','revision':'0.7','footprints':261,'electrical_pads_checked':count,'board_islands':8,'actuator_cutouts':8,'copper_layers':4,'thickness_mm':.8,'tracks_and_vias':len(list(b.GetTracks())),'schematic_parity_issues':0,'copper_DRC_errors':0,'main_board_warnings':len(drc['violations']),'main_board_unconnected_items':main_opens,'inter_island_unconnected_items':external_opens,'satellite_local_unconnected_items':0,'satellites_with_zero_DRC_violations':list(range(1,8)),'scope':'Native pad/net correspondence, layer count, valid outlines and satellite routing closure. Main routing, fabrication, impedance stack, physical fit and bench qualification remain open.'}
result.update(through_vias=len(vias),via_diameter_mm=.45,via_drill_mm=.2,drills_overlapping_smd_lands=0)
(HW/'verification/routing/checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

