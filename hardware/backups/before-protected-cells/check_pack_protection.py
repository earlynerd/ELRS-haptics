"""Validate exported protector topology, manufacturer pin maps, and trip calculations."""
from kicad_edit import *
import xml.etree.ElementTree as ET
from math import isclose

root=ET.parse(HW/'verification/netlist.xml').getroot()
nets={}
for net in root.findall('./nets/net'):
    nodes={(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')}
    for node in nodes: nets[node]=(net.attrib['name'],nodes)
def exact(*nodes): assert nets[nodes[0]][1]==set(nodes),(nodes,nets[nodes[0]])
def same(*nodes): assert len({nets[n][0] for n in nodes})==1,(nodes,[nets[n][0] for n in nodes])
def separate(*nodes): assert len({nets[n][0] for n in nodes})==len(nodes)

# ABLIC Fig19: each source faces its own terminal; only drains join in the center.
drains={('Q6',p) for p in ['1','2','5','6','8']}|{('Q7',p) for p in ['1','2','5','6','8']}
assert nets[('Q6','1')][1]==drains
exact(('R54','2'),('U27','D1'),('Q6','4'),('Q6','7'))
exact(('U27','B2'),('Q6','3'))
exact(('U27','C2'),('Q7','3'))
exact(('Q7','4'),('Q7','7'),('R56','1'),('U11','2'),('J3','1'),('C36','1'))
exact(('U27','D2'),('R56','2'))
# VSS is filtered through 1k to GND; it must not be directly tied to system ground.
exact(('U27','A1'),('U27','B1'),('R55','1'),('C44','2'))
same(('R55','2'),('U1','1'),('J200','2'))
same(('U27','A2'),('C44','1'),('R54','1'),('F100','2'))
separate(('U27','A2'),('U27','D1'),('Q6','1'),('Q7','4'),('U27','A1'),('R55','2'))
exact(('U27','C1'))

components={c.attrib['ref']:c for c in root.findall('./components/comp')}
expected={
 'S-821AAAC-H8T7S':{'A1':'VSS','A2':'VDD','B1':'TH','B2':'CO','C1':'PS','C2':'DO','D1':'VINI','D2':'VM'},
 'CSD17318Q2':{'1':'D','2':'D','3':'G','4':'S','5':'D','6':'D','7':'S','8':'D'},
}
lib=load(HW/'HapticBracelet.kicad_sym')
for name,pinmap in expected.items():
    sym=next(s for s in children(lib,'symbol') if uq(s[1])==name)
    actual={uq(child(p,'number')[1]):uq(child(p,'name')[1]) for sub in children(sym,'symbol') for p in children(sub,'pin')}
    assert actual==pinmap,(name,actual)
# Also inspect the embedded symbol; external library agreement alone is insufficient.
sh=load(HW/'protection.kicad_sch')
for name,pinmap in expected.items():
    sym=next(s for s in children(child(sh,'lib_symbols'),'symbol') if uq(s[1])=='HapticBracelet:'+name)
    assert {uq(child(p,'number')[1]):uq(child(p,'name')[1]) for sub in children(sym,'symbol') for p in children(sub,'pin')}==pinmap

u=next(s for s in children(sh,'symbol') if any(p[1:3]==[q('Reference'),q('U27')] for p in children(s,'property')))
xy=tuple(map(float,child(u,'at')[1:3]))
assert any(tuple(map(float,child(n,'at')[1:3]))==(xy[0]+22.86,round(xy[1]+17.78,4)) for n in children(sh,'no_connect'))
for ref,mpn in [('U27','S-821AAAC-H8T7S'),('Q6','CSD17318Q2'),('Q7','CSD17318Q2'),('R54','D1MPC0805DR003FF-T5')]:
    fields={f.attrib['name']:f.text for f in components[ref].findall('./fields/field')}
    assert fields['MPN']==mpn and fields['Manufacturer'] and fields['DigiKey']
assert components['R55'].findtext('value')=='1k'
assert components['R56'].findtext('value')=='22'
assert components['C44'].findtext('value')=='100n'
r=float(components['R54'].findtext('value').split()[0]); assert isclose(r,.003)

fp=load(HW/'HapticBracelet.pretty/ABLIC_WLP-8V_1.08x1.52mm_P0.4x0.76mm.kicad_mod')
pads={uq(p[1]):p for p in children(fp,'pad')};assert set(pads)==set(expected['S-821AAAC-H8T7S'])
for row,y in zip('ABCD',[-.6,-.2,.2,.6]):
    for col,x in [('1',-.38),('2',.38)]:
        pad=pads[row+col]
        assert tuple(map(float,child(pad,'at')[1:3]))==(x,y)
        assert tuple(map(float,child(pad,'size')[1:3]))==(.18,.18)
fetfp=load(Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_SON.pretty/Texas_DQK.kicad_mod'))
assert {uq(p[1]) for p in children(fetfp,'pad') if uq(p[1])}==set(expected['CSD17318Q2'])

limits={}
for name,v,tol,delay in [('discharge',.0058,.001,128),('short',.0205,.005,.280),('charge',.020,.001,32)]:
    wide_tol=.005 if name=='short' else .0015
    # 1% initial resistor tolerance plus 75 ppm/C over -40..85 C (65 C from 25).
    rt=.01+75e-6*65
    limits[name]={'nominal_A':v/r,'min_25C_A':(v-tol)/(r*1.01),'max_25C_A':(v+tol)/(r*.99),
                  'min_minus40_to85C_A':(v-wide_tol)/(r*(1+rt)),
                  'max_minus40_to85C_A':(v+wide_tol)/(r*(1-rt)), 'nominal_delay_ms':delay}
report={'status':'PASS','components':len(components),'pinmaps':expected,'trips':limits,
 'shunt_loss_at_2A_W':4*r,'fet_pair_loss_at_2A_25C_using_2p5V_max_Rds_W':4*2*.030,
 'protector_Iq_typ_uA':6,'protector_Iq_max_25C_uA':10,'protector_Iq_max_minus40_to85C_uA':14,
 'scope':'KiCad-exported topology, symbol/footprint pin maps and static calculations. No transient simulation, PCB routing, load/cell qualification or physical fault testing.'}
(HW/'verification/pack-protection-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
