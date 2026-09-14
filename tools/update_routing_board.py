"""One-time incremental PCB migration. Preserve the approved component placement."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
import pcbnew as p
from kicad_edit import load,save,children,child,parse
HW=Path(__file__).resolve().parents[1]/'hardware'
PCB=HW/'haptic-bracelet.kicad_pcb'
OUT=HW/'verification/routing'
assert not (OUT/'board-migration.json').exists(),'Already migrated; do not overwrite routing.'
propath=HW/'haptic-bracelet.kicad_pro'
pro=json.loads(propath.read_text())
rules=pro['board']['design_settings']['rules']
rules.update(min_copper_edge_clearance=.25,min_clearance=.1,min_track_width=.1,min_via_diameter=.45,min_through_hole_diameter=.2,min_via_annular_width=.125)
default=pro['net_settings']['classes'][0]
default.update(clearance=.15,track_width=.15,via_diameter=.45,via_drill=.2,description='Four-layer JLCPCB prototype; 0.10 mm BGA necks, 0.15 mm ordinary signals.')
pro['text_variables']['DESIGN_STATUS']='FOUR-LAYER ROUTING IN PROGRESS - NOT FOR FABRICATION'
propath.write_text(json.dumps(pro,indent=2)+'\n')
b=p.LoadBoard(str(PCB));assert len(list(b.GetTracks()))==0
b.SetCopperLayerCount(4)
ds=b.GetDesignSettings();ds.SetBoardThickness(p.FromMM(.8))
ds.m_CopperEdgeClearance=p.FromMM(.25);ds.m_MinClearance=p.FromMM(.1)
ds.m_TrackMinWidth=p.FromMM(.1);ds.m_ViasMinSize=p.FromMM(.45)
ds.m_ViasMinAnnularWidth=p.FromMM(.125)
doc=ET.parse(HW/'verification/netlist.xml').getroot()
comps={c.get('ref'):c for c in doc.findall('components/comp')}
nodes={};nets={}
for n in doc.findall('nets/net'):
    name=re.sub(r'Pod (\d) / U(\d+)',r'Pod \1 {slash} U\2',n.get('name'))
    if name.startswith('unconnected-'):name=name.replace('/','{slash}')
    net=b.FindNet(name)
    if not net:net=p.NETINFO_ITEM(b,name);b.Add(net)
    nets[name]=net
    for node in n.findall('node'):nodes[(node.get('ref'),node.get('pin'))]=net
fps={}
for old in list(b.GetFootprints()):
    ref=old.GetReference()
    if ref not in comps:b.Remove(old);continue
    c=comps[ref];f=old;fp=c.findtext('footprint')
    if ref=='L1' or ref.startswith('F'):
        lib,name=fp.split(':');f=p.FootprintLoad(str(HW/'HapticBracelet.pretty'),name)
        f.SetFPID(p.LIB_ID(lib,name));f.SetReference(ref);f.SetPath(old.GetPath())
        f.SetPosition(old.GetPosition());f.SetOrientation(old.GetOrientation())
        b.Remove(old);b.Add(f)
    f.SetValue(c.findtext('value'));f.SetField('Datasheet',c.findtext('datasheet') or '')
    f.SetField('Description',c.findtext("fields/field[@name='Description']") or '')
    for field in c.findall('fields/field'):
        key=field.get('name')
        if key in ['Reference','Value','Footprint','Datasheet','Description']:continue
        existing=next((field for field in f.GetFields() if field.GetName()==key),None)
        if existing:existing.SetText(field.text or '')
        else:
            item=p.PCB_FIELD(f,p.FIELD_T_USER,key);item.SetText(field.text or '');item.SetVisible(False);f.Add(item)
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
    for pad in f.Pads():
        ns=[nodes.get((ref,num)) for num in pad.GetNumber().split('/')]
        if ns[0]:pad.SetNet(ns[0])
    fps[ref]=f
for i in range(8):
    f=fps[f'U{3+i}'];pads={pad.GetNumber():pad for pad in f.Pads()}
    assert pads['B2'].GetNetname()==pads['C2'].GetNetname()=='POD_3V3'
    t=p.PCB_TRACK(b);t.SetStart(pads['B2'].GetPosition());t.SetEnd(pads['C2'].GetPosition())
    t.SetWidth(p.FromMM(.1));t.SetLayer(p.F_Cu);t.SetNet(pads['B2'].GetNet());t.SetLocked(True);b.Add(t)
b.GetTitleBlock().SetTitle('Haptic bracelet / four-layer routing study')
b.GetTitleBlock().SetRevision('0.7')
p.SaveBoard(str(PCB),b)
# KiCad Python does not expose stackup editing. Add an explicit symmetric 0.8 mm
# nominal stack; dielectric values are provisional until a JLC stack is selected.
a=load(PCB);setup=child(a,'setup')
for s in children(setup,'stackup'):setup.remove(s)
setup.insert(1,parse('''(stackup
 (layer "F.SilkS" (type "Top Silk Screen"))
 (layer "F.Paste" (type "Top Solder Paste"))
 (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
 (layer "F.Cu" (type "copper") (thickness 0.035))
 (layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
 (layer "In1.Cu" (type "copper") (thickness 0.0175))
 (layer "dielectric 2" (type "core") (thickness 0.475) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
 (layer "In2.Cu" (type "copper") (thickness 0.0175))
 (layer "dielectric 3" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
 (layer "B.Cu" (type "copper") (thickness 0.035))
 (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
 (layer "B.Paste" (type "Bottom Solder Paste"))
 (layer "B.SilkS" (type "Bottom Silk Screen"))
 (copper_finish "ENIG") (dielectric_constraints no))'''))
save(PCB,a)
# SaveBoard may write project defaults; persist the intended routing rules again.
propath.write_text(json.dumps(pro,indent=2)+'\n')
report={'revision':'0.7','components':len(fps),'layers':4,'nominal_thickness_mm':.8,'reset_links':8,'via_mm':[.45,.2],'dielectric_stack':'Provisional symmetric stack; confirm exact JLCPCB stack before impedance/fabrication release.'}
(OUT/'board-migration.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
