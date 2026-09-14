"""Check protected battery interfaces and switched bulk against an exported netlist.

External PCM functionality is not represented by PCB components and is not tested.
"""
from kicad_edit import *
import xml.etree.ElementTree as ET

doc=ET.parse(HW/'verification/netlist.xml').getroot()
comps={c.attrib['ref']:c for c in doc.findall('./components/comp')}
nets={}
for n in doc.findall('./nets/net'):
    nodes={(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')}
    for p in nodes:nets[p]=(n.attrib['name'],nodes)
assert not {'U27','Q6','Q7','R54','R55','R56','C44'} & comps.keys()
assert not (HW/'protection.kicad_sch').exists()
assert nets[('U11','2')][0]=='VBAT'
assert nets[('U11','2')][0]!=nets[('U26','6')][0]
for i in range(8):
    j,f,c=f'J{200+i}',f'F{100+i}',f'C{103+10*i}'
    assert comps[j].findtext('value')=='PROTECTED CELL 90mAh'
    assert nets[(j,'1')][1]=={(j,'1'),(f,'1')}
    assert nets[(j,'2')][0]==nets[('U1','1')][0]
    assert nets[(f,'2')][0]==nets[('U11','2')][0]
    assert comps[c].findtext('value')=='22u 10V X5R'
    assert comps[c].findtext('footprint')=='Capacitor_SMD:C_0805_2012Metric'
    assert nets[(c,'1')][0]==nets[('U26','6')][0]
    assert nets[(c,'2')][0]==nets[('U1','1')][0]
    fields={p.attrib['name']:p.text for p in comps[j].findall('./fields/field')}
    assert 'PCM intact' in fields['BOM Comments']

def capacitance_uF(v):
    token=v.split()[0]
    return float(token[:-1])*{'u':1,'n':.001,'p':.000001}[token[-1]]
rail=nets[('U26','6')][0]; ground=nets[('U1','1')][0]
rail_caps={}
for r,c in comps.items():
    if r.startswith('C') and {(nets[(r,p)][0]) for p in ['1','2']}=={rail,ground}:
        rail_caps[r]=capacitance_uF(c.findtext('value'))
total_uF=sum(rail_caps.values())
ct_pF=capacitance_uF(comps['C42'].findtext('value'))*1e6
assert ct_pF==4700
slew_us_per_V=.55*ct_pF+30  # TI TPS22918 section 8.3.2, Equation 3
rise_ms=slew_us_per_V*(.5*(1+511/91))/1000
# Equation 3 uses a 10-90% rise definition; current is C*(0.8*V)/t10-90.
capacitor_ramp_mA=.8*total_uF/slew_us_per_V*1000
assert capacitor_ramp_mA<100
report={'status':'PASS','protected_batteries':8,'nominal_capacity_mAh':720,
        'continuous_battery_current_mA_equal_sharing':360,'central_protector_present':False,
        'additional_bulk_uF_each':22,'switched_rail_caps_uF_nominal':rail_caps,
        'total_switched_capacitance_uF_nominal':total_uF,'CT_pF':ct_pF,
        'typical_10_to_90_rise_ms':rise_ms,'nominal_capacitor_only_ramp_mA':capacitor_ramp_mA,
        'source':'TI TPS22918 Rev C section 8.3.2 Equation 3; exported capacitor values',
        'scope':'PCB connectivity and nominal calculations only. External PCM, unequal sharing, capacitor DC bias/tolerance, dynamic loads, actual ramp and fault recovery remain bench checks.'}
(HW/'verification/pack-protection-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
